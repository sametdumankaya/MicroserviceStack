#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 15:40:33 2020

@author: ozkan
"""
from TimeSeriesL1Analytics import removeFPBreaks
import TimeSeriesEvents
import stumpy
import numpy as np
import MSig_Functions as MSig
import matplotlib.pyplot as plt
from numba import cuda
import itertools
from redistimeseries.client import Client
import pandas as pd

all_gpu_devices=[device.id for device in cuda.list_devices()]
output_redis_host=input_redis_host="localhost"
input_redis_port=6400
from_time=0
to_time=-1
prefix="rts1:01:symbol:"
bucket_size_msec=60000
filters=["SYMSET=ACTIVE"]
aggregation_type="last"

output_redis_port=6381 #this is for reading the indexes
redis_ind=Client(host=output_redis_host,port=output_redis_port)

df_price_data=pd.DataFrame()
df_indices=pd.DataFrame()

all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
df_price_data=all_data["df_price_data"]

res=redis_ind.range("mind:price:avg", from_time=int(all_data["ts_price_min"]), to_time=int(all_data["ts_price_max"]))
ts_price,data_price = map(list,zip(*res))
df_indices["ts_price"]=ts_price
###IMPORTANT###################
#### IF YOU WANT TO ANALYZE INDEX ONLY USE THIS. OTHERWISE ,cOMMENT out
df_price_data=df_indices
########################


#
m=L=20
ts_data=df_price_data.iloc[:,0].dropna().values
# for i in [0,100,200,300]:
#     if(i!=300):
#         dat=ts_data[0:i+100]
#     else:
#         dat=ts_data[:]
#     mp=stumpy.gpu_stump(dat, m=m,device_id=all_gpu_devices)
#     correct_arc_curve, regime_locations=stumpy.fluss(mp[:,1],L=L,n_regimes=20,excl_factor=1)
#     regime_locations=[i for i in regime_locations if i!=0]
#     fig,axs=plt.subplots(1,1) 
#     axs.plot(dat)
#     trans=axs.get_xaxis_transform()
#     for i in range(len(regime_locations)):
#         axs.axvline(regime_locations[i],lw=0.5,color='red')
#         axs.text(x=regime_locations[i],y=1, s=str(i+1),size=7,transform=trans)
#     plt.figure()

        
mp=stumpy.gpu_stump(ts_data, m=m,device_id=all_gpu_devices)

idx=10
anchored_chain=stumpy.atsc(mp[:,2],mp[:,3],idx)
all_chain_set,longest_unanchored_chain=stumpy.allc(mp[:,2],mp[:,3])

correct_arc_curve, regime_locations=stumpy.fluss(mp[:,1],L=L,n_regimes=20,excl_factor=1)
regime_locations=[i for i in regime_locations if i!=0]

fig,axs=plt.subplots(1,1) 
axs.plot(ts_data)
trans=axs.get_xaxis_transform()
for i in range(len(regime_locations)):
    axs.axvline(regime_locations[i],lw=0.5,color='red')
    axs.text(x=regime_locations[i],y=1, s=str(i+1),size=7,transform=trans)
plt.figure()

#unanchored
plt.plot(df_price_data[df_price_data.columns[0]], linewidth=1, color='black')
plt.title("unanchored longest chain symbol="+df_price_data.columns[0])
for i in range(longest_unanchored_chain.shape[0]):
    y = df_price_data[df_price_data.columns[0]].iloc[longest_unanchored_chain[i]:longest_unanchored_chain[i]+m]
    x = y.index.values
    plt.plot(x, y, linewidth=1.5)


plt.figure()

plt.axis('off')
plt.title("longest unanchored chain")
for i in range(longest_unanchored_chain.shape[0]):
    data = df_price_data[df_price_data.columns[0]].iloc[longest_unanchored_chain[i]:longest_unanchored_chain[i]+m].reset_index().values
    x = data[:, 0]
    y = data[:, 1]
    plt.axvline(x=x[0]-x.min()+(m+5)*i+5, alpha=0.3)
    plt.axvline(x=x[0]-x.min()+(m+5)*i+15, alpha=0.3, linestyle='-.')
    plt.plot(x-x.min()+(m+5)*i, y-y.min(), linewidth=3)
plt.figure()
#stream=stumpy.floss(mp, ts_data, m, L,excl_factor=5)

plt.plot(df_price_data[df_price_data.columns[0]], linewidth=1, color='black')
plt.title("all chains")
chain_cnt=0
for i in range(len(all_chain_set)):
    chain=all_chain_set[i]
    if(len(chain)>1 ):
        print(chain)
        chain_cnt=chain_cnt+1
        is_done=False
        for c in chain:
            y = df_price_data[df_price_data.columns[0]].iloc[c:c+m]
            x = y.index.values
            if(not is_done):
                plt.text(x[0], y.iloc[0], str(chain_cnt))
                is_done=True
            plt.plot(x, y, linewidth=1.5)
plt.show()


#floss
from matplotlib import animation
from IPython.display import HTML
import os
old_data=ts_data[0:100]
new_data=ts_data[100:]
mp = stumpy.stump(old_data, m=m)

stream = stumpy.floss(mp, old_data, m=m, L=L, excl_factor=1)
windows = []
regs=[]
for i, t in enumerate(new_data):
    stream.update(t)

    if i % 10 == 0:
        windows.append((stream.T_, stream.cac_1d_))
        reg=stumpy._rea(stream._cac,n_regimes=20,L=20,excl_factor=1)
        reg=[i for i in reg if i!=0]
        print(reg)
        regs.append(reg)

cac_1d=stream.cac_1d_

fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})

axs[0].set_xlim((0, mp.shape[0]))
axs[0].set_ylim((-0.1, max(np.max(old_data), np.max(new_data))))
axs[1].set_xlim((0, mp.shape[0]))
axs[1].set_ylim((-0.1, 1.1))

lines = []
for ax in axs:
    line, = ax.plot([], [], lw=2)
    lines.append(line)
line, = axs[1].plot([], [], lw=2)
lines.append(line)

def init():
    for line in lines:
        line.set_data([], [])
    return lines

def animate(window):
    data_out, cac_out = window
    for line, data in zip(lines, [data_out, cac_out, cac_1d]):
        line.set_data(np.arange(data.shape[0]), data)
    return lines

anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=windows, interval=10,
                               blit=True)

anim_out = anim.to_jshtml()
plt.close()  # Prevents duplicate image from displaying
if os.path.exists("None0000000.png"):
    os.remove("None0000000.png")  # Delete rogue temp file

HTML(anim_out)
anim.save(os.getcwd()+'/semantic.mp4')


#CHOW
import run_cython
#TODO: CHECK THE STRUC BREAKS IT DOES NOT LOOK LIKE ZERO BASED!!!
strucBreaks=run_cython.OptimizedPelt(model=run_cython.OptimizedNormalCost()).fit(np.array(ts_data)).predict(10)
strucBreaks=removeFPBreaks(df_price_data,strucBreaks,'l1')[0]
fig,axs=plt.subplots(1,1) 
axs.plot(ts_data)
trans=axs.get_xaxis_transform()
for i in range(len(strucBreaks)):
    #if(strucBreaks[i]%3!=0):
        axs.axvline(strucBreaks[i],lw=1,color='red')
    #axs.text(x=strucBreaks[i],y=1, s=str(i+1),size=7,transform=trans)
inters=list(set(strucBreaks)&set(regime_locations))

for i in range(len(regime_locations)):
    if(regime_locations[i] in inters):
        axs.axvline(regime_locations[i],lw=1,color='green')
        axs.text(x=regime_locations[i],y=1, s=str(i+1),size=7,transform=trans)

plt.show()













