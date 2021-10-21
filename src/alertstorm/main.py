import argparse
import logging
import math
import networkx as nx
import os
from pathlib import Path
from random import choice
import sys
import time
from typing import List

import dfre4net.ingest as ingest
import dfre4net.knowledge as knowledge
from dfre4net.knowledge import KnowledgeGraph
import dfre4net.layer as layer
from dfre4net.layer import L1, L2
import alertstorm.agent as agent
import alertstorm.layer as as_layer
import alertstorm.net as net
from alertstorm.L0_input import L0_Input
from alertstorm.L2_input import L2_Input
from alertstorm.L1_output import L1_Output
from dfre4net.config import Config


USE_CASE_ID = 'alertstorm'

def get_cli_parser() -> argparse.ArgumentParser:

    cli_parser = argparse.ArgumentParser(
        prog=sys.argv[0]+' '+USE_CASE_ID,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    ## Help
    cli_parser.add_argument(
        '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='Show AlertStorm specific arguments.'
    )
    ## Debugging
    cli_parser.add_argument(
        '--log-level',
        type=str,
        default='DEBUG',
        help='Log level'
    )
    return cli_parser


def main(args: List[str]) -> None:

    ## command line parameters parser
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(args)

    ## set logger configuration
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d - %(funcName)20s()] %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
    flag_log_level = cli_options.log_level
    defaultLoggingLevel=logging.INFO
    if flag_log_level== 'INFO':
        defaultLoggingLevel=logging.INFO
    elif flag_log_level== 'WARNING':
        defaultLoggingLevel=logging.WARNING
    elif flag_log_level== 'ERROR':
        defaultLoggingLevel=logging.ERROR
    elif flag_log_level== 'DEBUG':
        defaultLoggingLevel=logging.DEBUG
    logging.getLogger().setLevel(defaultLoggingLevel)

    ## Load config from config file
    config = Config()

    ## our dictionary to store layers. contain "l1", "l2", "l1_batch"
    layers = {"l2": None, "l1": None, "l1_batch": None}

    ## Create L2
    layers["l2"] = L2_Input(config).getL2()

    ## create an empty L1. Will be fill with l1_batch
    layers["l1"] = as_layer.create_new_l1()

    ## Create the input that will provide batches of L0 data
    l0_input = L0_Input(config, 1000)
    l0_input.start()

    ## create an output to send L1 to the database used for UI
    l1_output = L1_Output(config)

    ## Do pre-processing, if any
    logging.debug(f"Pre-processing ...")
    for process_id in config.pre_processing:
        processing_stage = config.pre_processing[process_id]
        agent.process2_phase(layers, processing_stage)
    logging.info(f"Pre-processing done.")
    
    ## manage the processing loop
    batch_loop_counter = 0
    try:
        while batch_loop_counter < config.get('max_batchs'):
            
            t0 = time.time()
            logging.info(f'Batch Loop {batch_loop_counter} -->')

            ## Get a l0 batch
            l0_batch = l0_input.getL0()
            if l0_batch is None:
                logging.info('   REACH END OF DATA')
                break
            logging.info(f'   [Setup] Loading an L0 batch with {len(l0_batch.kg.g.nodes)} alerts... Done!')

            ## Calculate initial L1 corresponding to the l0 batch above, according to the current L2
            layers["l1_batch"] = as_layer.derive_l1(l0_batch, layers["l2"])
            logging.info('   [Setup] Create initial L1 for the batch... Done!')

            ## Building interlayer links for the alerts... Don't forget to reference l2.extension to extend current one
            intension_map, extension_map = agent.link(layers["l1_batch"].stm, layers["l2"].stm, None, layers["l2"].extension)
            layers["l1_batch"].intension, layers["l2"].extension = intension_map, extension_map
            logging.info("   [Setup] Building AlertStorm interlayer links for the alerts... Done!")

            ## detect and display some unclassified item (i.e. L1 nodes that have no intension)
            agent.detectUnclassified(layers["l1_batch"].stm, layers["l1_batch"].intension)

            ## Processes batch of L1 with processing phase describe from config file
            for process_id in config.processing:
                processing_stage = config.processing[process_id]
                agent.process2_phase(layers, processing_stage)

            ## Send current l1 update (new/update) to database
            l1_output.send_alternate(layers["l1"])

            ## Dump if needed
            if config.get('dump_l1'):
                nx.write_graphml(layers["l1"].stm.g, 'alertstorm_l1_stm_{0}.graphml'.format(batch_loop_counter))
            if config.get('dump_l2'):
                nx.write_graphml(layers["l2"].stm.g, 'alertstorm_l2_stm_{0}.graphml'.format(batch_loop_counter))

            # Add edges to the L1 graph           
            if config.get('add_l1_edges'):
                G = nx.read_graphml('LargestCC_topologyBorgWithAlerts.graphml')
                G_nodes = list(G.nodes(data=True))
                logging.info("Adding edges to the L1 graph")
                l1_nodes = list(layers["l1"].stm.g.nodes(data=True))
                
                for i in range(len(l1_nodes)):
                    if(l1_nodes[i][1]['deviceName'] in G_nodes):
                        G.add_edge( l1_nodes[i] , G.nodes(l1_nodes[i][1]['deviceName']))

                G = nx.write_graphml( G ,'LargestCC_topologyBorgWithAlerts.graphml')

            # Okay for now to load G and add edges but when corrected use the L2 source as G.


            ## Loop again for next batch
            batch_loop_counter += 1

            logging.info(f"Batch Loop {batch_loop_counter} <-- took {round((time.time()-t0),3)}sec")

        logging.info("!Done Main batch loop")
        
        ## Send remaining 'new'/'updated' content to output
        logging.info("Send remaining 'new'/'updated' L1 content to output...")
        l1_output.send(layers["l1"])

    except KeyboardInterrupt:
        logging.info("main(): catch KeyboardInterrupt")
        pass
    #except Exception as err:
    #    logging.info("main(): catch Error="+repr(err))

    logging.info("!Done")
    
    ## Dump final state if needed
    if config.get('dump_l1'):
        logging.info("main(): Dump L1 to 'alertstorm_l1_stm.graphml'...")
        nx.write_graphml(layers["l1"].stm.g, 'alertstorm_l1_stm_final.graphml')
        logging.info("main(): Dump L1 to 'alertstorm_l1_stm.graphml'... Done!")

    logging.info("l1:")
    logging.info(repr(layers["l1"]))

    ## stop the l0
    l0_input.stop()
    logging.info("l0_input stopped. Ok.")

if __name__ == '__main__':
    main(sys.argv[1:])
