#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/python3
import argparse
import sys
import time
import os
import random
import math
import ctwRTS
import ctwGrafana

class StratUtils:
   """Strategy utilities"""

   def __init__(self):
      self.grafana = ctwGrafana.grafana('admin','grafana','localhost',7123,'localhost',6380)
      self.ctwrts = ctwRTS.rts(port=6380)
      self.rts = self.ctwrts.rts

   def TStoSymbols(self, ts):
      data = [ 1 if (ts[i+1] - ts[i]) >= 0 else 0 for i in range(len(ts) - 1)]
      ups = 0
      downs = 0
      syms = []
      last = None
      for i in range(len(data)):
         if data[i] > 0:
            ups += 1
            if last is not None and last == 0:
               syms.append(downs * -1)
               downs = 0
         else:
            downs += 1
            if last is not None and last > 0:
               syms.append(ups)
               ups = 0
         last = data[i]
      if ups > 0:
         syms.append(ups)
      elif downs > 0:
         syms.append(downs * -1)
   
      return syms

   def MatchPattern(self, pattern, symbols,f):
      lenp = len(pattern) 
      lens = len(symbols) 
      print("pattern:",file=f)
      print(pattern,file=f)
      print("symbols:",file=f)
      print(symbols[-3:],file=f)
   
      if lens < lenp:
         print("no match: lens < lenp",file=f)
         return False
      for i in range(lenp):
         print("i:{}".format(i), file=f)
         if symbols[-1 - i] < 0 and pattern[-1 - i] > 0:
            print("no match: sym < 0 and pattern > 0",file=f)
            return False
         elif symbols[-1 -i] > 0 and pattern[-1 -i ] < 0:
            print("no match: syms > 0 and pattern < 0",file=f)
            return False
         if pattern[-1 - i] > 0 and symbols[-1 -i] >= pattern[-1 -i ]:
            print("pattern > 0 and symbol >= pattern", file=f)
            pass
         elif pattern[-1 -i ] < 0 and symbols[-1 -i ]  >= pattern[-1 - i]:
            print("pattern < 0 and symbol >= pattern",file=f)
            pass
         else:
            print("no match",file=f)
            return False
      print("we have a match!",file=f)
   
      return True

   def AnnotateArray(self, pattern, data, ts_name, dashboard,f):
      tdata = []
      hits = []
      for i in range(len(data)):
         tdata.append(data[i])
         syms = self.TStoSymbols(tdata)
         print("{}.syms".format(i),file=f)
         print(syms,file=f)
         if self.MatchPattern(pattern, syms,f):
            hits.append(i)
            annotations = [ [time.time() - (len(data) * 10) + (i * 10) , ["buy buy buy"]]]
            if dashboard is not None:
               dashboard.addAnnotations(ts_name, annotations)
      return hits

   def GetSymbolDataValues(self, sym):
      pricekey = "rts1:01:symbol:{}:price".format(sym)
      if not self.rts.exists(pricekey):
         return
      symprices_ts = self.rts.range(pricekey, '-', '+', aggregation_type='avg', bucket_size_msec=10000)
      idata = [ symprices_ts[i][1] for i in range(len(symprices_ts))]
      return idata

   def ProcessSymbol(self, sym, pattern):
      minhistory = 5 # minimum available price information history in minutes
      pricekey = "rts1:01:symbol:{}:price".format(sym)
      if not self.rts.exists(pricekey):
         return False
      f = open("/tmp/{}.log".format(sym),"w")
      symprices_ts = self.rts.range(pricekey, '-', '+', aggregation_type='avg', bucket_size_msec=10000)

      intervals = len(symprices_ts) - 1
      print("symprices_ts length: {}".format(intervals))
   
      if intervals < (minhistory * 6): #correction based on rts.range bucket size
         time.sleep(1)
         return False
   
      idata = [ symprices_ts[i][1] for i in range(len(symprices_ts))]
      idata_delta = [ 1 if (idata[i+1] - idata[i]) >= 0 else 0 for i in range(len(idata) - 1)]
      idata_symbols = self.TStoSymbols(idata)
   
      dashboard = self.grafana.createDashboard("ddb_testStrategy003.{}".format(sym))
      dashboard.delete()
      dashboard = self.grafana.createDashboard("ddb_testStrategy003.{}".format(sym))
      tsname = "{}.idata".format(sym)
      dashboard.DrawGraph(tsname,idata, samplerate=10000)
      tsname = "{}.idata_delta".format(sym)
      dashboard.DrawGraph(tsname,idata_delta, samplerate=10000)
   
      tsname = "{}.idata_symbols".format(sym)
      duration = len(idata)*10000
      sr = int(duration / len(idata_symbols))
      dashboard.DrawGraph(tsname,idata_symbols, samplerate=sr)
   
      dashboard.addTSPanel(pricekey)
   
      self.AnnotateArray(pattern, idata, "{}.idata".format(sym),dashboard, f)

      return True


# ProcessSymbol2: No UX
   def ProcessSymbol2(self, sym, pattern, outdir="/tmp"):
      minhistory = 5 # minimum available price information history in minutes
      pricekey = "rts1:01:symbol:{}:price".format(sym)
      if not self.rts.exists(pricekey):
         return
      f = open("{}/{}.log".format(outdir,sym),"w")
      symprices_ts = self.rts.range(pricekey, '-', '+', aggregation_type='avg', bucket_size_msec=10000)

      intervals = len(symprices_ts) - 1
      print("symprices_ts length: {}".format(intervals))
   
      if intervals < (minhistory * 6): #correction based on rts.range bucket size
         time.sleep(1)
         return
   
      idata = [ symprices_ts[i][1] for i in range(len(symprices_ts))]
      idata_delta = [ 1 if (idata[i+1] - idata[i]) >= 0 else 0 for i in range(len(idata) - 1)]
      idata_symbols = self.TStoSymbols(idata)
   
      tsname = "{}.idata".format(sym)
      tsname = "{}.idata_delta".format(sym)
   
      tsname = "{}.idata_symbols".format(sym)
      duration = len(idata)*10000
      sr = int(duration / len(idata_symbols))   
      hits = self.AnnotateArray(pattern, idata, "{}.idata".format(sym),None, f)

      return hits, idata

