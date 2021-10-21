import pandas as pd
import numpy as np
import stumpy
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib import animation
from IPython.display import HTML
import urllib
import ssl
import io
import os
#TODO:
#ADD A SEGMENTATION QUALITY CONTROL CODE. IF THE DISTANCE BETWEEN TWO SEGMENTATION IS m+1, the latest one is false positive.
#DELETE THE LATEST ONE
def getSemanticSegmentationFromMP(df,n_regimes=10):
    #df is a dataframe of timeseries. Each column is one series
    all_regimes=[]
    all_cac=[]
    abp=[]
    for i in range(len(df.columns)):
        abp=df.iloc[:,i]
        abp=abp[abp.notnull()].values.astype(np.float32)
        m = 100
        mp = stumpy.stump(abp, m=m)
        L = 100
        cac, regime_locations = stumpy.fluss(mp[:, 1], L=L, n_regimes=n_regimes, excl_factor=1)
        all_regimes.append(regime_locations)
        all_cac.append(cac)
    return all_cac, all_regimes

def plotSemanticSegForSingleTS(time_series,n_regimes=2):
    #time_series: array of float
    abp=time_series
    m = 50
    mp = stumpy.stump(abp, m=m,ignore_trivial=True)
    L = 50
    cac, regime_locations = stumpy.fluss(mp[:, 1], L=L, n_regimes=n_regimes, excl_factor=1)
    fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})
    axs[0].plot(range(abp.shape[0]), abp)
    for i in regime_locations:
        if(i!=0):
            axs[0].axvline(x=i, linestyle="dashed")
    axs[1].plot(range(cac.shape[0]), cac, color='C1')
    for i in regime_locations:
        if(i!=0):
            axs[1].axvline(x=i, linestyle="dashed")
            
def testStumpyWithDummyData():
    #MORE TEST CODE FROM TUTORIAL BELOW
    context = ssl.SSLContext()  # Ignore SSL certificate verification for simplicity
    url = 'https://sites.google.com/site/timeserieschain/home/TiltABP_210_25000.txt'
    raw_bytes = urllib.request.urlopen(url, context=context).read()
    data = io.BytesIO(raw_bytes)
    df = pd.read_csv(data, header=None)
    df = df.reset_index().rename({'index': 'time', 0: 'abp'}, axis='columns')
    df.head()
    def change_plot_size(width, height, plt):
        fig_size = plt.rcParams["figure.figsize"]
        fig_size[0] = width
        fig_size[1] = height
        plt.rcParams["figure.figsize"] = fig_size
    
    change_plot_size(20, 6, plt)
    plt.plot(df['time'], df['abp'])
    rect = Rectangle((24000,2400),2000,6000,facecolor='lightgrey')
    plt.gca().add_patch(rect)
    start = 25000 - 2500
    stop = 25000 + 2500
    abp = df.iloc[start:stop, 1]
    plt.plot(range(abp.shape[0]), abp)
    plt.ylim(2800, 8500)
    plt.axvline(x=2373, linestyle="dashed")
    plt.show()
    style="Simple, tail_width=0.5, head_width=6, head_length=8"
    kw = dict(arrowstyle=style, color="k")
    
    # regime 1
    rect = Rectangle((55,2500), 225, 6000, facecolor='lightgrey')
    plt.gca().add_patch(rect)
    rect = Rectangle((470,2500), 225, 6000, facecolor='lightgrey')
    plt.gca().add_patch(rect)
    rect = Rectangle((880,2500), 225, 6000, facecolor='lightgrey')
    plt.gca().add_patch(rect)
    rect = Rectangle((1700,2500), 225, 6000, facecolor='lightgrey')
    plt.gca().add_patch(rect)
    arrow = FancyArrowPatch((75, 7000), (490, 7000), connectionstyle="arc3, rad=-.5", **kw)
    plt.gca().add_patch(arrow)
    arrow = FancyArrowPatch((495, 7000), (905, 7000), connectionstyle="arc3, rad=-.5", **kw)
    plt.gca().add_patch(arrow)
    arrow = FancyArrowPatch((905, 7000), (495, 7000), connectionstyle="arc3, rad=.5", **kw)
    plt.gca().add_patch(arrow)
    arrow = FancyArrowPatch((1735, 7100), (490, 7100), connectionstyle="arc3, rad=.5", **kw)
    plt.gca().add_patch(arrow)
    plt.show()
    # regime 2
    rect = Rectangle((2510,2500), 225, 6000, facecolor='moccasin')
    plt.gca().add_patch(rect)
    rect = Rectangle((2910,2500), 225, 6000, facecolor='moccasin')
    plt.gca().add_patch(rect)
    rect = Rectangle((3310,2500), 225, 6000, facecolor='moccasin')
    plt.gca().add_patch(rect)
    arrow = FancyArrowPatch((2540, 7000), (3340, 7000), connectionstyle="arc3, rad=-.5", **kw)
    plt.gca().add_patch(arrow)
    arrow = FancyArrowPatch((2960, 7000), (2540, 7000), connectionstyle="arc3, rad=.5", **kw)
    plt.gca().add_patch(arrow)
    arrow = FancyArrowPatch((3340, 7100), (3540, 7100), connectionstyle="arc3, rad=-.5", **kw)
    plt.gca().add_patch(arrow)        
    plt.show()
    
if __name__ == "__main__":
    print("testing stumpy semantic segmentation with dummy data")
    testStumpyWithDummyData()
    #DF is a set of time series each column is one series
    strucBreaks=pd.read_csv("strucBreaks.csv")
    strucBreaks=strucBreaks[strucBreaks.strucBreaks.astype(str) !='nan']
    strucBreaks=strucBreaks.reset_index(drop=True)
    df=pd.read_csv("merged_191015_1949.csv")
    cols=list(strucBreaks["name"].astype(str))
    df = df[df.columns.intersection(cols)]

    abp=df.iloc[:,0]
    time_series=abp[abp.notnull()].values.astype(np.float32)
    plotSemanticSegForSingleTS(time_series,n_regimes=3)
    #GET ALL SEMANTIC SEGMENTATION
    all_cac,all_regimes=getSemanticSegmentationFromMP(df)
    
  




        
