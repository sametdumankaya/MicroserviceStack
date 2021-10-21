import os,sys
import argparse
from pathlib import Path
from typing import List
import redis
from subprocess import Popen
import time
sys.path.append(os.path.dirname(Path(os.path.abspath(__file__)).parent))
import timeseries.timeSeriesAgent
USE_CASE_ID = 'timeseries'
import tmux_util as tu
import argparse 

def get_cli_parser() -> argparse.ArgumentParser:
    cli_parser = argparse.ArgumentParser(
        prog=sys.argv[0]+' '+USE_CASE_ID,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    ## redishost parameter
    cli_parser.add_argument(
        '--redishost',
        type=str,
        default='localhost',
        help='Host address for redis.'
    )
    ## redisport parameter
    cli_parser.add_argument(
        '--redisport',
        type=int,
        default=6379,
        help='Port number for redis'
    )
    
    return cli_parser

def main(args: List[str]) -> None:
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(args)
    r = redis.Redis(host=cli_options.redishost, port=cli_options.redisport, db=0)
    try:
        r.ping() 
    except Exception as e:
        print("Unable to connect redis... If the server is up and running theck the local connection settings at ", 	  str(Path(os.path.abspath(__file__))))
        return
    import subprocess
    if(os.name=='nt'):
        p2 = subprocess.Popen(["start", "cmd", "/k", "python timeseries/taskManagementAgent.py " +"".join(args)], shell = True) 
        time.sleep(5)
        timeseries.timeSeriesAgent.main(args)
    else:
        p1 = tu.open_pane('window1','dfre','python timeseries/taskManagementAgent.py ' +''.join(args))
        time.sleep(5)
        timeseries.timeSeriesAgent.main(args)

if __name__ == '__main__':
    main(sys.argv[1:])
