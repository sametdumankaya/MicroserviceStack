import requests
import json
import os
import logging
import sys
import datetime
import time
import locale

from dfre4net.knowledge import KnowledgeGraph
from dfre4net.layer import L1
from dfre4net.config import Config
import dfre4net.knowledge as knowledge


# Default timeout in second to communicate to gateway
CONFIG_SERVER_TIMEOUT = 15


class L1_Output:
    """
        Manage the output of L1 knowledge processing 
    """

    def __init__(self, config: Config):

        self.count_max = 50
        self.config = config
        self.enabled = False
        logging.debug(repr(self.config.output))
        if self.config.output:
            self.enabled = self.config.output['enable'] if 'enable' in self.config.output else True
        logging.info(f"L1 output is {self.enabled}")

        logging.debug(f"locale.getdefaultlocale()={locale.getdefaultlocale()}")
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        
    def send(self, l1: L1) -> None:

        """
            Send current l1 content to configured output.
            Only HTTP supported for now
            Will identify 'new' node and 'update' node. Batching sent of  self.count_max alerts.
        """
        if not self.enabled:
            return

        headers = {'Content-Type': 'application/json'}
        url = self.config.output['endpoint']
        
        t0 = time.time()
        new_alerts = []
        upd_alerts = []
        nb_tot_new = 0
        nb_tot_upd = 0
        for _, node_props in l1.stm.g.nodes(data=True):

            # Add the formatted alert on list of alerts to send
            alert_obj = self.get_transformed_alert( node_props )

            if ('status' not in node_props) or (node_props['status']=='new'):
                new_alerts.append(alert_obj)
                nb_tot_new += 1
            elif node_props['status']=='updated':
                upd_alerts.append(alert_obj)
                nb_tot_upd += 1

            # Send alerts once list is big enough
            if len(new_alerts) > self.count_max:
                self.postNewContent(url, new_alerts, headers)
                new_alerts = []
            if len(upd_alerts) > self.count_max:
                self.putContent(url, upd_alerts, headers)
                upd_alerts = []

            # reset status
            node_props['status'] == ''

        # No more alerts on L1... send remaining contents on lists
        if len(new_alerts) > 0:
            self.postNewContent(url, new_alerts, headers)
        if len(upd_alerts) > 0:
            self.putContent(url, upd_alerts, headers)

        logging.info(f"Send a total of {nb_tot_new} new nodes, and {nb_tot_upd} updated nodes in {round((time.time()-t0),3)}sec")

    def postNewContent(self, url: str, alerts: [], headers: {}) -> None:
        """
            HTTP POST array of alerts to url.
        """
        sdata = str(alerts).replace("'", '"')
        logging.debug(url)
        r = requests.post(url, timeout=CONFIG_SERVER_TIMEOUT, data=sdata, headers=headers)
        #logging.debug("cresult={0}".format(r.text))
        if r.status_code == 403:
            raise Exception("403")
        elif r.status_code == 404 or r.text.find("Not found")!=-1 :
            raise Exception("404")
        elif r.status_code == 400:
            #logging.debug(alerts)
            self.debug_send_L1(alerts)
            raise Exception("400", r.text)

    def putContent(self, url: str, alerts: [], headers: {}) -> None:
        """
            HTTP PUT array of alerts to url.
        """
        sdata = str(alerts).replace("'", '"')
        logging.debug(url)
        r = requests.put(url, timeout=CONFIG_SERVER_TIMEOUT, data=sdata, headers=headers)
        #logging.debug("cresult={0}".format(r.text))
        if r.status_code == 403:
            raise Exception("403")
        elif r.status_code == 404 or r.text.find("Not found")!=-1 :
            raise Exception("404")
        elif r.status_code == 400:
            #logging.debug(alerts)
            self.debug_send_L1(alerts)
            raise Exception("400", r.text)

    def get_transformed_alert(self, node_props: dict) -> dict:

        """
            Transform and format an alert to a format that 'ready to send'
        """
        # Format datetime
        date = datetime.datetime.strptime(node_props['date'] , "%a %b %d %H:%M:%S %Y")

        # clean up severity
        severity = node_props['severity'].upper()
        if severity=='INFO': severity = 'NOTICE'
        if severity=='ALERT': severity = 'CRITICAL'
        if severity not in ['ERROR', 'WARNING', 'NOTICE', 'CRITICAL']:
            logging.error(f'Invalid severity {severity}')
            raise Exception("400", f'Invalid severity {severity}')

        # Clean up title
        title = node_props['title']
        title = title.replace('"',' ')
        title = title.replace('\'',' ')

        # Clean up histo
        histo = ""
        if 'dfre_severity_histo' in node_props:
            histo = node_props['dfre_severity_histo']
            histo = histo.replace('\'','-')

        # Create map paths from deviceName, dfre_semantic_severity and productType
        map_paths = []
        map_paths.append('AlertStorm.Network.TeleologicalCategorization.'+node_props['dfre_category'].strip())
        if 'deviceName' in node_props:
            name = node_props['deviceName']
            name = name.replace('.','_')
            map_paths.append('AlertStorm.Network.TopIssues.ByDevice.'+name)
        if 'dfre_semantic_severity' in node_props:
            if node_props['dfre_semantic_severity']=='high':
                map_paths.append('AlertStorm.TopIssues.TopAlerts')
        if 'productType' in node_props:
            path = node_props['productType']
            path = path.replace('.','_')
            path = path.replace(' ','_')
            map_paths.append('AlertStorm.Network.TopIssues.ByTopology.'+path)

        # Add the formatted alert on list of alerts to send
        tr_alert = {
            'title': title,
            'global_id': node_props['alert_id'],
            'issue_id': node_props['issue_id'],
            'problem_id': node_props['problem_id'],
            'alertstorm_severity': severity,
            'date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'dfre_severity': str(node_props['dfre_severity']),
            'dfre_severity_strategy': 'avg',
            'dfre_severity_histo': histo,
            'l2_map_paths': map_paths
        }

        return tr_alert

    def debug_send_L1(self, alerts: []) -> None:

        headers = {'Content-Type': 'application/json'}
        url = self.config.output['endpoint']
        logging.debug("###")
        logging.debug("Error detected, retry each alert individually")
        logging.debug("###")
        for alert in alerts: 
            logging.debug("Try "+alert['title'])
            sdata = str(alert).replace("'", '"')
            r = requests.post(url, timeout=CONFIG_SERVER_TIMEOUT, data=sdata, headers=headers)
            if r.status_code == 400:
                logging.debug(sdata)
                raise Exception("400", r.text)
            else:
                logging.debug("... ok")

    def send_alternate(self, l1: L1) -> None:
        """
            Alternate send of L1 output.
            Will run a query to get a max 1000 of 'new' elmt, then POST it.
            It will then run a query to get the 1000 top most 'dfre_severity' node in 'updated' state, then PUT it
        """
        if not self.enabled:
            return

        headers = {'Content-Type': 'application/json'}
        url = self.config.output['endpoint']

        # Run a query to get max 1000 concept in 'new' state...
        t0 = time.time()
        query_fct = knowledge.MatchingProp    ## Get top L2 from prior+context knowledge severity
        query_result = knowledge.run_query(
            knowledge.FirstNConceptsQuery( 1000 ), 
            query_fct(l1.stm, 'status', 'new') ## Get top L2 from prior+context knowledge severity
        )
        top_concepts = [ str(cnpt) for cnpt in query_result.concepts ]

        # send the new_alerts content
        new_alerts = []
        for cnpt in top_concepts:
            alert_obj = self.get_transformed_alert( l1.stm.g.nodes[cnpt] )
            new_alerts.append(alert_obj)

            # Send alerts once list is big enough
            if len(new_alerts) > self.count_max:
                self.postNewContent(url, new_alerts, headers)
                new_alerts = []

            # reset status
            l1.stm.g.nodes[cnpt]['status'] = ''

        # No more alerts on L1... send remaining contents on lists
        if len(new_alerts) > 0:
            self.postNewContent(url, new_alerts, headers)

        logging.info(f"POST {len(top_concepts)} concepts in {round((time.time()-t0),3)}sec")

        # Run a query to get max 1000 concept in 'updated' state, in 
        t0 = time.time()
        query_fct = knowledge.MatchingPropWithOrder    ## Get top L2 from prior+context knowledge severity
        query_result = knowledge.run_query(
            knowledge.FirstNConceptsQuery( 1000 ), 
            query_fct(l1.stm, 'status', 'updated', 'dfre_severity') ## Get top L2 from prior+context knowledge severity
        )
        top_concepts = [ str(cnpt) for cnpt in query_result.concepts ]

        upd_alerts = []
        for cnpt in top_concepts:
            alert_obj = self.get_transformed_alert( l1.stm.g.nodes[cnpt] )
            upd_alerts.append(alert_obj)

            # Send alerts once list is big enough
            if len(upd_alerts) > self.count_max:
                self.putContent(url, upd_alerts, headers)
                upd_alerts = []

            # reset status
            l1.stm.g.nodes[cnpt]['status'] = ''

        # No more alerts on L1... send remaining contents on lists
        if len(upd_alerts) > 0:
            self.putContent(url, upd_alerts, headers)

        logging.info(f"PUT {len(top_concepts)} concepts in {round((time.time()-t0),3)}sec")



