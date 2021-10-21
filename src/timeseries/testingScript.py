# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 13:33:59 2020

@author: ozkan
"""
from pathlib import Path
import os
from dfre4net2.DFRE_KG import DFRE_KG, merge_KG
from dfre4net2.query_KG import sql_query_KG

fname='L2timeseries.dfrescr'
DIR = Path(os.getcwd())
timeSeriesScript = DIR / Path('./timeseries/L2script')/fname
kb=DFRE_KG(str(timeSeriesScript))
kb.dump_KG_to_graphml('test.graphml')

fname='L2fromDrew.dfrescr'
drewScript = DIR / Path('./timeseries/L2script')/fname
kb_drew=DFRE_KG(str(drewScript))
kb_drew.dump_KG_to_graphml('test2.graphml')


kb_merged=merge_KG(kb,kb_drew)
kb_merged.dump_KG_to_graphml('test3.graphml')

alertstrom_path= DIR / Path('./troubleshoot/LargestCC_topologyBorg_withAlerts.graphml')
fname=str(alertstrom_path)
kb_alertstorm=DFRE_KG(fname)

sql="select * from concepts where problem_count > 5"
new_KB1=sql_query_KG(kb_alertstorm,sql)
new_KB1.dump_KG_to_graphml('alert_strom_prob5.graphml')

sql="select * from concepts where network like '10.%' and (topics like '%3%' or topics like '%3%')"
new_KB2=sql_query_KG(kb_alertstorm,sql)
new_KB2.dump_KG_to_graphml('alert_strom_netw_topic.graphml')


kb_merged=DFRE_KG('test3.graphml')
sql="select * from relations where source ='Events'"
new_KB3=sql_query_KG(kb_merged,sql)
new_KB3.dump_KG_to_graphml('drew_events.graphml')