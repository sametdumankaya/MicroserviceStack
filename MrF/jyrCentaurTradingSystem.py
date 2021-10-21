#!/usr/bin/env python
# coding: utf-8

# In[14]:


import sys
from enum import Enum, auto
import threading
import time
import ctwRTS

class OrderMetaType(Enum):
    TDARegular = auto
    TDAExtended = auto
    STMSimulated = auto
    STMSimulatedPaper = auto
    
class OrderType(Enum):
    buyLimit = auto
    sellLimit = auto

    buyLimitF = auto
    sellLimitF = auto
    
    buyMarket = auto
    sellMarket = auto
    
class OrderStatus(Enum):
    queued_unconfirmed = auto
    queued = auto
    canceled = auto
    filled = auto
    rejected = auto
    
class Order:
    def __init__(self, orderid, ordermetatype = OrderMetaType.TDARegular, 
        orderstatus=OrderStatus.queued_unconfirmed):
        self.id = orderid
        self.metatype = ordermetatype
        self.status = orderstatus

class BrokerType(Enum):
    TDARegular = auto
    TDAExtended = auto
    TDAPaper = auto
    STMSimulated = auto
    STMSimulatedPaper = auto

# Broker
class Broker:
    def __init__(self, brokertype=BrokerType.STMSimulated):
        self.type = brokertype
        self.traders = []
        self.maxtraders = 2 
        self.tradeCandidates = []
    # openOrders organized by symbol
        self.openOrders = {}
# openPositions organized by symbol
        self.openPositions = {}
# expiredOrders organized by symbol

    def availableForNewTrader(self):
        return len(self.traders) < self.maxtraders

    def addTrader(self, tradingGuidance, tradingIntention):
        trader = Trader(tradingGuidance,tradingIntention)
        self.traders.append(trader)
    
    def placeOrder(self, ordertype, symbol, qty, timeout, limitprice=None):
        pass
    
    def getOpenOrders(self):
        pass
    
    def getOpenPositions(self):
        pass
    
# updateOrdersAndPositions
#    Will get latest info from system of record (e.g. TDAmeritrade)
    def updateOrdersAndPositions(self):
        pass
    
    def update(self):
        for trader in self.traders:
            if trader.expired():
                print("{} trader expired".format(trader.tradingIntention.symbol))
                self.traders.remove(trader)
#                print("{} trader expired".format(trader.tradingIntention.symbol))
         
# TradingGuidance
#    may apply to CentaurTradingSystem or an individual trader
class TradingGuidance:
    def __init__(self, maxspend=100, maxloss=5, maxloss_rate=3):
        self.maxspend = maxspend
        self.maxloss = maxloss
        self.maxloss_rate = maxloss_rate
        
class Trader:
    def __init__(self, tradingGuidance, tradingIntention):
        self.tradingGuidance = tradingGuidance
        self.tradingIntention = tradingIntention
        self.opentime = time.time()
        self.expiresec=10

    def expired(self):
        return time.time() - self.opentime > self.expiresec
        
class ctsMode(Enum):
# TDA mode will fire off multiple brokers including a live trading broker and a live paper trading broker
    TDA = auto
# Sim mode will fire off multiple brokers including a simulated trading broker and a simulated paper trading broker
    Sim = auto

class TradingStrategy(Enum):
    oscillator001 = auto
    
class TradingIntention:
    def __init__(self, symbol, strategy=TradingStrategy.oscillator001):
        self.symbol = symbol
        self.strategy = strategy
        self.opentime = time.time()
        self.expiresec = 5
        
    def expired(self):
        return time.time() - self.opentime > self.expiresec
        
class IntentionEngine:
    def __init__(self, tradingGuidance):
        self.tradingIntentions = []
        self.maxTradingIntentions = 2
        self.tradingGuidance = tradingGuidance
        self.symsOfInterest = ["CSCO","IBM","MSFT","NFLX","GILD","WMT","GLD","SPY","QQQ"]
        
    def suggestATradingIntention(self):
        if len(self.tradingIntentions) < self.maxTradingIntentions:
            if len(self.symsOfInterest) > 0:
                tradingIntention = TradingIntention(self.symsOfInterest.pop())
                self.tradingIntentions.append(tradingIntention)
                return tradingIntention
            else:
                print("my apologies but I'm out of new trading ideas...")
        return None
        
    def updateIntentionList(self):
        for tradingIntention in self.tradingIntentions:
            if tradingIntention.expired():
                print("{} trading intention has expired".format(tradingIntention.symbol))
                self.tradingIntentions.remove(tradingIntention)
    
class CentaurTradingSystem:
    def mainLoop(self, name):
        i = 0
        while True:
            print("CentaurTradingSystem iteration: {}".format(i))
            i = i + 1
            if self.stop_threads:
                break
            time.sleep(.5)
            tradingIntention = self.intentionEngine.suggestATradingIntention()
            if tradingIntention is not None:
                print("attempting to activate a new tradingIntention")
                print("   tradingIntention: {} created".format(tradingIntention.symbol))
                if self.brokerPrimary.availableForNewTrader():
                    self.intentionEngine.tradingIntentions.remove(tradingIntention)
                    self.brokerPrimary.addTrader(
                        self.intentionEngine.tradingGuidance,
                        tradingIntention)
                    print("   trader created for {}".format(tradingIntention.symbol))
                
            self.intentionEngine.updateIntentionList()
            self.brokerPrimary.update()
            self.brokerPaper.update()

# shutdownClean
#    shutdown cleanly, certainly ensure that:
#       no new intention driven events (not related to shutdown)
#       close all existing intentions (not related to shutdown)
#       cancel all outstanding orders
#       close all positions
    def shutdownClean(self):
        self.stop_threads = True
    
    def __init__(self, intentionEngine, redisPort=6380, mode = ctsMode.Sim):
        self.redisPort = redisPort
        self.ctwRTS = ctwRTS.rts(port=redisPort)
        self.mode = mode
# brokerPrimary can be simulated or real dollars, the objective function of the
#    CentaurTradingSystem is to maximize profit as measured by the performance of brokerPrimary
#        self.brokerPrimary = "simulated or TDA"
        if mode == ctsMode.Sim:
            self.brokerPrimary = Broker(BrokerType.STMSimulated)
# brokerPaper is used to test things out and improve the performance of brokerPrimary. it is only a tool
#        self.brokerPaper = "may be simulated_paper or TDA_paper"
            self.brokerPaper = Broker(BrokerType.STMSimulatedPaper)
        elif mode == ctsMode.TDA:
            self.brokerPrimary = Broker(BrokerType.TDARegular)
            self.brokerPaper = Broker(BrokerType.TDAPaper)
        else :
            raise Exception("invalid mode")
            
        self.intentionEngine = intentionEngine
        self.stop_threads = False
        self.primaryThread = threading.Thread(
            target=self.mainLoop, 
            args=("primaryThread" , ))
        self.primaryThread.start()
        


# In[ ]:




