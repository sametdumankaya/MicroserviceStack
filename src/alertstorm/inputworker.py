from abc import ABC, abstractmethod
import logging
import sys
import inspect
import multiprocessing
import json
import requests
import threading
import time
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union


import os
from itertools import islice
from pathlib import Path


class InputWorker(ABC):
    """
        Abstract Input worker that will provide batch of data based to a multiprocessing queue

    """

    def __init__(self, q: multiprocessing.Queue) -> None:
        super().__init__()
        self.q = q

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError

class AlertstormInputWorker( InputWorker, multiprocessing.Process ):

    """
        Input worker that provide data from alertstorm database (http access)

    """
    def __init__(self, q: multiprocessing.Queue, src: str, limit: Optional[int]=1000):

        super(AlertstormInputWorker, self).__init__(q)

        self.CONFIG_SERVER_TIMEOUT = 5
        self.CONFIG_DFRE_SERVER = src ## '10.200.97.8:8082/'
        self.datashape = []
        self.limit = 20

    def run(self):

        print("{0}::{1}(): -->".format(__name__, inspect.currentframe().f_code.co_name))

        # First, get the set of data where we have data
        self.getAvailableDatesList()
        while True:
            for data in self.datashape:
                if data['finish']:
                    pass
                alerts = self.getAlertsForDate(data['date'], data['offset'], self.limit)
                data['offset'] += len(alerts)
                if len(alerts)<self.limit:
                    data['finish'] = True
                self.q.put(alerts)
            time.sleep(1)
        
    def shutdown(self):

        logging.info("Shutdown initiated")

    def getAvailableDatesList(self):

        url = "http://{0}/dfre/alertstorm/query".format(self.CONFIG_DFRE_SERVER)
        logging.debug("... Request data with URI='"+url+"'")
        data = "select date(date), count(*) from borg.borg_runs group by 1 order by 1 ASC;"
        r = requests.post(url, data=data, timeout=self.CONFIG_SERVER_TIMEOUT)
        jsonobj = json.loads(r.text)
        #logging.debug(jsonobj)
        response = jsonobj['content']
        for elmt in response:
            self.datashape.append({'date': elmt['date'], 'borg_run_count': elmt['count'], 'offset': 0, 'finish': False})

    def getAlertsForDate(self, date, offset, limit) -> []:

        url = "http://{0}/dfre/alertstorm/query".format(self.CONFIG_DFRE_SERVER)
        logging.debug("... Request data with URI='"+url+"'")
        data = "select * from borg.alerts where date between '{2} 00:00:00' and '{2} 23:59:59' offset {0} limit {1};".format(offset, limit, date)
        logging.debug("... Request data with request="+data)
        r = requests.post(url, data=data, timeout=self.CONFIG_SERVER_TIMEOUT)
        jsonobj = json.loads(r.text)
        logging.debug(jsonobj)
        alerts = jsonobj['content']
        return alerts

class FileInputWorker( InputWorker, multiprocessing.Process ):

    """
        Input worker that provide data from alerts.data files. Note that the file is not load in memory.
        Processus open file then read line sequencially

    """
    def __init__(self, q: multiprocessing.Queue, src_file: Path, limit: Optional[int]=1000):

        super(FileInputWorker, self).__init__(q)

        self.src_file = src_file
        self.limit = limit

    def run(self):

        logging.debug("--> <--")

        if not self.src_file.exists: raise ValueError(f"The path {self.src_file} does not exist.")
        if not self.src_file.is_file: raise ValueError(f"File {self.src_file} is not a file.")
        with open(self.src_file, 'r') as f:
            while True:
                alerts = []
                lines_gen = islice(f, self.limit)
                for line in lines_gen:
                    alerts.append(json.loads(line))
                if len(alerts)==0:
                    break
                #nb = len(alerts)
                #logging.debug(f"Load {nb} alerts")
                #logging.debug(repr(alerts))
                self.q.put(alerts, block=True)

        logging.info("reach end of file")
        self.q.put({'EOF': '1'}, block=True)

        
    def shutdown(self):

        logging.debug("Shutdown initiated")
