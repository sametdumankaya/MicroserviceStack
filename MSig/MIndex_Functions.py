
import pandas as pd
import redis
from redistimeseries.client import Client
import MSig_Functions as MSig
import numpy as np
import matplotlib.pyplot as plt
import TimeSeriesEvents

def getIndexes(ts_names:list,prefix="rts1:01:symbol:",postfix=":volume",redis_host="localhost",redis_port=6381,indexList=['VIX', 'ALPHA', 'BETA', 'EMA','CMA','SMA','RSA','avg'],aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1):
    # arr1=df_price_data.iloc[:,0].values
    # arr1=arr1[~np.isnan(arr1)]
    # arr2=df_price_data.iloc[:,1].values
    # arr2=arr2[~np.isnan(arr2)]
    
    # #single number 
    
    # beta=talib.BETA(arr1,arr2[0:len(arr1)])
    pass


def aggregateData(aggregatedIndexType=['price','volume','market_capital'], prefix="rts1:01:symbol:",input_redis_host="localhost",input_redis_port=6400, output_redis_host="localhost", output_redis_port=6380, aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1,filters=["SYMSET=ACTIVE"]):
    all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    redis_out=Client(host=output_redis_host,port=output_redis_port)
    for index_type in aggregatedIndexType:
        if(index_type=='price'):
            index_name="mind:price:avg"
            print("adding data for",index_name)
            df_price_data=all_data['df_price_data']
            ts_price=[int(i*bucket_size_msec+all_data["ts_price_min"]) for i in range(len(df_price_data))]
            #normalize data
            df_normalized_price=(df_price_data-df_price_data.min())/(df_price_data.max()-df_price_data.min())
            mean_val=df_normalized_price.mean(axis=1,skipna=True)
            #send to redis
            try:
                #create index if does not exists
                if(redis_out.exists(index_name)==0):
                    _=redis_out.create(index_name)
                #push data
                arr_tuples=tuple(zip(ts_price,mean_val.values.astype(float)))
                arr_tuples=[(index_name,)+xs for xs in arr_tuples]
                redis_out.madd(arr_tuples)
            except Exception as e:
                pass
        elif(index_type=='volume'):
            index_name="mind:volume:avg"
            print("adding data for",index_name)
            df_volume_data=all_data['df_volume_data']
            ts_volume=[int(i*bucket_size_msec+all_data["ts_volume_min"]) for i in range(len(df_volume_data))]
            #normalize data
            df_normalized_volume=(df_volume_data-df_volume_data.min())/(df_volume_data.max()-df_volume_data.min())
            mean_val=df_normalized_volume.mean(axis=1,skipna=True)
            #send to redis
            try:
                #create index if does not exists
                if(redis_out.exists(index_name)==0):
                    _=redis_out.create(index_name)
                #push data
                arr_tuples=tuple(zip(ts_volume,mean_val.values.astype(float)))
                arr_tuples=[(index_name,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
            except Exception as e:
                pass
        else:
            index_name="mind:market_capital:avg"
            print("adding data for",index_name)
            df_market_capital=pd.DataFrame(all_data['df_price_data']*all_data['df_volume_data'],columns=all_data['df_price_data'].columns)
            ts_market_capital=[int(i*bucket_size_msec+all_data["ts_price_min"]) for i in range(len(df_market_capital))]
            #normalize data
            df_normalized_market_capital=(df_market_capital-df_market_capital.min())/(df_market_capital.max()-df_market_capital.min())
            mean_val=df_normalized_market_capital.mean(axis=1,skipna=True)
            #send to redis
            try:
                #create index if does not exists
                if(redis_out.exists(index_name)==0):
                    _=redis_out.create(index_name)
                #push data
                arr_tuples=tuple(zip(ts_market_capital,mean_val.values.astype(float)))
                arr_tuples=[(index_name,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
            except Exception as e:
                print(e)
                pass
def visualizeIndexOnRegimeChanges(isSave=False,index_name=['price','volume','market_capital'], prefix="rts1:01:symbol:",input_redis_host="localhost",input_redis_port=6400, output_redis_host="localhost", output_redis_port=6380, aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1,filters=["SYMSET=ACTIVE"],ts_freq_threshold=20,peek_ratio=0.3,windows=[10],num_regimes=20):
    from datetime import datetime
    from matplotlib.lines import Line2D
    from pytz import timezone
    tz=timezone('US/Pacific')

    all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    redis_ind=Client(host=output_redis_host,port=output_redis_port)
    df_indices=pd.DataFrame()
    for ind in index_name:
        if(ind=='price'):
            res=redis_ind.range("mind:price:avg", from_time=int(all_data["ts_price_min"]), to_time=int(all_data["ts_price_max"]))
            ts_price,data_price = map(list,zip(*res))
            df_indices["ts_price"]=ts_price
            df_indices["data_price"]=data_price
        elif(ind=='volume'):
            res=redis_ind.range("mind:volume:avg", from_time=int(all_data["ts_volume_min"]), to_time=int(all_data["ts_volume_max"]))
            ts_volume,data_volume = map(list,zip(*res))
            df_indices["ts_volume"]=ts_volume
            df_indices["data_volume"]=data_volume
        else:
            res=redis_ind.range("mind:market_capital:avg", from_time=int(all_data["ts_price_min"]), to_time=int(all_data["ts_price_max"]))
            ts_market_cap,data_market_cap = map(list,zip(*res))
            df_indices["ts_market_cap"]=ts_market_cap
            df_indices["data_market_cap"]=data_market_cap
    
    df_regimes_price=MSig.get_regime_changes(all_data["df_price_data"],num_regimes=num_regimes,windows=windows)
    histogram_price=MSig.getHistogramFromUnalignedDf(df_regimes_price,all_data["ts_price"],all_data["ts_price_min"],all_data["ts_price_max"],bucket_size_msec)
    df_indices["histogram_price"]=histogram_price[:len(df_indices)]
    all_ts_price=list(range(all_data["ts_price_min"], all_data["ts_price_max"]+bucket_size_msec,bucket_size_msec))
    events_price=TimeSeriesEvents.getCandidateEvents(histogram_price,len(all_ts_price),ts_freq_threshold=ts_freq_threshold,peek_ratio=peek_ratio,sampling_rate=bucket_size_msec)
    ax=df_indices.plot(subplots=True,x="ts_price", y=['histogram_price','data_price','data_volume','data_market_cap'],title=str(input_redis_port)+" port",lw='1')
    colors=['black','red','yellow']
    lines=[Line2D([0],[0],color=c,linewidth=1) for c in colors]
    labels=['li','mi','ti'] 
    ax[0].legend(lines,labels,loc='center left',bbox_to_anchor=(1,0.5))
    for i,row in events_price.iterrows():
        li=int(row["leading indicator"])
        mi=int(row["main indicator"])
        ti=int(row["trailing indicator"])
        isFirst=True
        for x in ax:
            x.axvline(df_indices["ts_price"][li],color="black",lw=0.5)   
            x.axvline(df_indices["ts_price"][mi],color="red",lw=0.5,label="mi"+str(i+1))   
            x.axvline(df_indices["ts_price"][ti],color="yellow",lw=0.5,label="ti"+str(i+1))
    if(isSave):plt.savefig("outp/"+str(input_redis_port)+'.pdf',bbox_inches='tight')
    #plt.savefig("outp/"+str(input_redis_port)+"_"+str(datetime.fromtimestamp(all_data["ts_price_max"]/1000,tz=tz)).split(' ')[0]+'.pdf',bbox_inches='tight')
    #plt.close()
def runMPonIndices(isSave=False,index_name=['price','volume','market_capital'], prefix="rts1:01:symbol:",input_redis_host="localhost",input_redis_port=6400, output_redis_host="localhost", output_redis_port=6380, aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1,filters=["SYMSET=ACTIVE"],ts_freq_threshold=20,peek_ratio=0.3,windows=[10],num_regimes=20):
    from datetime import datetime
    import matplotlib.pyplot as plt
    from pytz import timezone
    tz=timezone('US/Pacific')
    from datetime import datetime
    from pytz import timezone
    import matrixprofile as mp
    import matplotlib.transforms as transforms
    tz=timezone('US/Pacific')

    all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    redis_ind=Client(host=output_redis_host,port=output_redis_port)
    df_index_price=pd.DataFrame()
    df_index_volume=pd.DataFrame()
    df_index_marketcap=pd.DataFrame()
    for ind in index_name:
        if(ind=='price'):
            res=redis_ind.range("mind:price:avg", from_time=int(all_data["ts_price_min"]), to_time=int(all_data["ts_price_max"]))
            ts_price,data_price = map(list,zip(*res))
            df_index_price["ts_price"]=ts_price
            df_index_price["data_price"]=data_price
        elif(ind=='volume'):
            res=redis_ind.range("mind:volume:avg", from_time=int(all_data["ts_volume_min"]), to_time=int(all_data["ts_volume_max"]))
            ts_volume,data_volume = map(list,zip(*res))
            df_index_volume["ts_volume"]=ts_volume
            df_index_volume["data_volume"]=data_volume
        else:
            res=redis_ind.range("mind:market_capital:avg", from_time=int(all_data["ts_price_min"]), to_time=int(all_data["ts_price_max"]))
            ts_market_cap,data_market_cap = map(list,zip(*res))
            df_index_marketcap["ts_market_cap"]=ts_market_cap
            df_index_marketcap["data_market_cap"]=data_market_cap

    fig,axs=plt.subplots(3*len(windows)) 
    fig.suptitle(str(input_redis_port) + " port for win sizes="+'-'.join(map(str,windows)),size=8)
    plt_counter=0
    for w in windows:
        win=[w]
        profile_price=mp.compute(data_price,windows=win)
        profile_volume=mp.compute(data_volume,windows=win)
        profile_market_cap=mp.compute(data_market_cap,windows=win)
        
        x=mp.discover.regimes(profile_price, num_regimes=num_regimes)
        regimes_price= list(filter(lambda x: x != 0, x["regimes"]))
        axs[plt_counter].plot(data_price,lw=0.5)
        axs[plt_counter].title.set_size(fontsize=5)
        axs[plt_counter].title.set_text("price index "+str(w))
        axs[plt_counter].get_xaxis().set_visible(False)
        axs[plt_counter].get_yaxis().set_visible(False)
        trans=axs[plt_counter].get_xaxis_transform()
        for i in range(len(regimes_price)):
            axs[plt_counter].axvline(regimes_price[i],lw=0.5,color='red')
            axs[plt_counter].text(regimes_price[i],0.5,str(i+1),transform=trans,size=5)
        plt_counter=plt_counter+1

        x=mp.discover.regimes(profile_volume, num_regimes=num_regimes)
        regimes_volume= list(filter(lambda x: x != 0, x["regimes"]))
        axs[plt_counter].plot(data_volume[5:-15],color='green',lw=0.5)
        axs[plt_counter].title.set_size(fontsize=5)
        axs[plt_counter].title.set_text("volume index "+str(w))
        axs[plt_counter].get_xaxis().set_visible(False)
        axs[plt_counter].get_yaxis().set_visible(False)
        trans=axs[plt_counter].get_xaxis_transform()
        #plot the regimes
        for i in range(len(regimes_volume)):
            axs[plt_counter].axvline(regimes_volume[i],lw=0.5,color='red')
            axs[plt_counter].text(regimes_volume[i],0.5,str(i+1),transform=trans,size=5)
        plt_counter=plt_counter+1

        x=mp.discover.regimes(profile_market_cap, num_regimes=num_regimes)
        regimes_market_cap= list(filter(lambda x: x != 0, x["regimes"]))
        axs[plt_counter].plot(data_market_cap[5:-15],color='m',lw=0.5)
        axs[plt_counter].title.set_size(fontsize=5)
        axs[plt_counter].title.set_text("market cap index "+str(w))
        axs[plt_counter].get_xaxis().set_visible(False)
        axs[plt_counter].get_yaxis().set_visible(False)
        trans=axs[plt_counter].get_xaxis_transform()

        for i in range(len(regimes_market_cap)):
            axs[plt_counter].axvline(regimes_market_cap[i],lw=0.5,color='red')
            axs[plt_counter].text(regimes_market_cap[i],0.5,str(i+1),transform=trans,size=5)
        plt_counter=plt_counter+1
    plt.tight_layout()
    if(isSave):plt.savefig("outp_ind/"+str(input_redis_port)+"_"+'-'.join(map(str,windows))+'.pdf',dpi=320)
    plt.close()

def generateSectorIndustryGainLoss(df_tmp,ts_price,redis_out,l2File="finL2Extension.graphml",category='price',window=10,input_redis_port=6400):
    from pytz import timezone
    import networkx as nx
    import pandas as pd
    import numpy as np
    from datetime import datetime
    from matplotlib.backends.backend_pdf import PdfPages
    tz=timezone('US/Pacific')
    G=nx.read_graphml(l2File)
    print("generating sector & industry gain loss for",input_redis_port, category, " window=",window)
    nodes=pd.DataFrame.from_dict(dict(G.nodes(data=True)),orient='index')
    sectors=list(nodes.sector.dropna().unique())
    industries=list(nodes.industry.dropna().unique())
    df_sectors_gains=pd.DataFrame(columns=sectors)
    df_sectors_loss=pd.DataFrame(columns=sectors)
    df_industries_gains=pd.DataFrame(columns=industries)
    df_industries_loss=pd.DataFrame(columns=industries)
    df_clean_tmp=df_tmp.iloc[:,:-6] #the last 6 cols are gain loss sums
    for i,row in df_clean_tmp.iterrows():
        values=row.dropna()
        df_sectors_gains=df_sectors_gains.append(pd.Series(0,index=df_sectors_gains.columns),ignore_index=True)
        df_sectors_loss=df_sectors_loss.append(pd.Series(0,index=df_sectors_loss.columns),ignore_index=True)
        df_industries_gains=df_industries_gains.append(pd.Series(0,index=df_industries_gains.columns),ignore_index=True)
        df_industries_loss=df_industries_loss.append(pd.Series(0,index=df_industries_loss.columns),ignore_index=True)
        for t, val in values.iteritems():
            if(t in G.nodes):
                subg=nx.ego_graph(G,t).nodes(data=True)._nodes
                _=subg.pop("ticker",None)
                #_=subg.pop(t,None)
                sect=''
                ind=''
                if('sector' in subg[list(subg.keys())[0]]):
                    sect=subg[list(subg.keys())[0]]['sector']
                if('industry' in subg[list(subg.keys())[0]]):
                    ind=subg[list(subg.keys())[0]]['industry']
                if(len(sect)>0):
                    if(val>0):
                        df_sectors_gains.loc[i,sect]=float(df_sectors_gains.loc[i,sect]+val)
                    elif(val<0):
                        df_sectors_loss.loc[i,sect]=float(df_sectors_loss.loc[i,sect]+val)
                if(len(ind)>0):
                    if(val>0):
                        df_industries_gains.loc[i,ind]=float(df_industries_gains.loc[i,ind]+val)
                    elif(val<0):
                        df_industries_loss.loc[i,ind]=float(df_industries_loss.loc[i,ind]+val)
    
    combined_gain_loss_pdf=PdfPages("combined_gain_loss_"+category+"_"+str(input_redis_port)+"_"+str(window)+ ".pdf")
    sector_gain_pdf=PdfPages("sector_gain_"+category+"_"+str(input_redis_port)+"_"+str(window)+ ".pdf")
    sector_loss_pdf=PdfPages("sector_loss_"+category+"_"+str(input_redis_port)+"_"+str(window)+ ".pdf")
    industry_gain_pdf=PdfPages("industry_gain_"+category+"_"+str(input_redis_port)+"_"+str(window)+ ".pdf")
    industry_loss_pdf=PdfPages("industry_loss_"+category+"_"+str(input_redis_port)+"_"+str(window)+ ".pdf")
    ymd=str(datetime.fromtimestamp(ts_price[0]/1000,tz=tz)).split(' ')[0]
   
    ax= df_sectors_gains.plot()
    ax.set_title(ymd+ " sector gain "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
    combined_gain_loss_pdf.savefig(ax.figure)
    
    ax=df_sectors_loss.plot()
    ax.set_title(ymd+ " sector loss "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
    combined_gain_loss_pdf.savefig(ax.figure)
    
    ax= df_industries_gains.plot(legend=False)
    ax.set_title(ymd+ " industry gain "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
    combined_gain_loss_pdf.savefig(ax.figure)
    
    ax=df_industries_loss.plot(legend=False)
    ax.set_title(ymd+ " industry loss "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
    combined_gain_loss_pdf.savefig(ax.figure)
    combined_gain_loss_pdf.close()
    plt.close('all')
    for c in df_sectors_gains.columns:
        ax= df_sectors_gains.plot(y=[c])
        ax.set_title(ymd +" "+str(c) + " gain "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
        sector_gain_pdf.savefig(ax.figure)
    sector_gain_pdf.close()
    plt.close('all')

    for c in df_sectors_loss.columns:
        ax= df_sectors_loss.plot(y=[c])
        ax.set_title(ymd +" "+ str(c) + " loss "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
        sector_loss_pdf.savefig(ax.figure)
    sector_loss_pdf.close()
    plt.close('all')
    
    for c in df_industries_gains.columns:
        ax= df_industries_gains.plot(y=[c])
        ax.set_title(ymd +" "+str(c) + " gain "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
        industry_gain_pdf.savefig(ax.figure)
        plt.close('all')
    industry_gain_pdf.close()
    plt.close('all')

    for c in df_industries_loss.columns:
        ax= df_industries_loss.plot(y=[c])
        ax.set_title(ymd +" "+ str(c) + " loss "+ category +" @ port "+ str(input_redis_port)+" window="+str(window))
        industry_loss_pdf.savefig(ax.figure)
        plt.close('all')
    industry_loss_pdf.close()
    plt.close('all')
    

def generateGainLossWithWindow(isReportOnly=False,enableSectorIndustry=False,window=10,ports=[item for item in range(6400,6465)],prefix="rts1:01:symbol:",input_redis_host="localhost", output_redis_host="localhost", output_redis_port=6378, aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1,filters=["SYMSET=ACTIVE"],labels={"TYPE":"GAINLOSS"}):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from pytz import timezone
    tz=timezone('US/Pacific')
    from datetime import datetime
    from pytz import timezone
    import matrixprofile as mp
    import matplotlib.transforms as transforms
    tz=timezone('US/Pacific')
    df_index_price=pd.DataFrame()
    df_index_volume=pd.DataFrame()
    df_index_marketcap=pd.DataFrame()
    df_price_data=pd.DataFrame()
    df_volume_data=pd.DataFrame()
    df_market_capital_data=pd.DataFrame()
    redis_out=Client(host=output_redis_host,port=output_redis_port)
    price_pdf=PdfPages('price.pdf')
    volume_pdf=PdfPages('volume.pdf')
    for p in ports:
        print("port="+str(p))
        input_redis_port=p
        all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
        df_price_data=all_data['df_price_data']
        ts_price=[int(i*bucket_size_msec+all_data["ts_price_min"]) for i in range(len(df_price_data))]
        ymd=str(datetime.fromtimestamp(all_data["ts_price_min"]/1000,tz=tz)).split(' ')[0]
        print(ymd)
        #df_temp=pd.DataFrame([10,10,12,13,15,15,15,15,15,17,15,12,10,12,10])
        #df_temp.pct_change(periods=2,axis=0)
        df_tmp=pd.DataFrame(columns=df_price_data.columns)
        for i, row in df_price_data.iterrows():
            if(i>=window-1):
                first=df_price_data.loc[i-window+1,:]
                last=df_price_data.loc[i,:]
                percent=(last-first)/last
                df_tmp=df_tmp.append(percent,ignore_index=True)
            else:
               df_tmp= df_tmp.append(pd.Series(),ignore_index=True)
        #df_temp=df_temp.fillna(0)
        df_tmp["gain"]=df_tmp.apply(lambda x: x[x>0].sum(),axis=1)
        df_tmp["loss"]=df_tmp.apply(lambda x: x[x<0].sum(),axis=1)
        df_tmp["gainloss"]=df_tmp["gain"]+df_tmp["loss"].abs()
        #tmp=list(df_tmp.iloc[9][:-3])
        #negs=[item for item in tmp if item<0]
        #poz=[item for item in tmp if item>0]
        df_tmp["normalized_gain"]=(df_tmp["gain"]-df_tmp["gain"].min())/(df_tmp["gain"].max()-df_tmp["gain"].min())
        df_tmp["normalized_loss"]=(df_tmp["loss"]-df_tmp["loss"].min())/(df_tmp["loss"].max()-df_tmp["loss"].min())
        df_tmp["normalized_gainloss"]=(df_tmp["gainloss"]-df_tmp["gainloss"].min())/(df_tmp["gainloss"].max()-df_tmp["gainloss"].min())
        #ax=df_tmp.plot(y=["normalized_gain","normalized_loss"])
        #ax.set_title(ymd+ " price @ port "+ str(input_redis_port)+ " window="+str(window))
        #price_pdf.savefig(ax.figure)
        if(enableSectorIndustry):generateSectorIndustryGainLoss(df_tmp,ts_price,redis_out,category='price',window=window,input_redis_port=input_redis_port)
        #df_tmp.plot(subplots=True,y=["normalized_gain","normalized_loss","normalized_gainloss"],layout=(1,3))
        if(isReportOnly==False):
            index_gain="mind:gain:price:window:"+str(window)
            index_loss="mind:loss:price:window:"+str(window)
            index_gainloss="mind:gainloss:price:window:"+str(window)
            print("adding data for",index_gain,index_loss,index_gainloss, "port=",input_redis_port)
            try:
                #create index if does not exists
                if(redis_out.exists(index_gain)==0):
                    _=redis_out.create(index_gain)
                    _=redis_out.alter(index_gain,labels=labels)
                if(redis_out.exists(index_loss)==0):
                    _=redis_out.create(index_loss)
                if(redis_out.exists(index_gainloss)==0):
                    _=redis_out.create(index_gainloss)
                #push data gain
                arr_tuples=tuple(zip(ts_price,df_tmp["normalized_gain"].values.astype(float)))
                arr_tuples=[(index_gain,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
                #push data loss
                arr_tuples=tuple(zip(ts_price,df_tmp["normalized_loss"].values.astype(float)))
                arr_tuples=[(index_loss,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
                #push data gainloss
                arr_tuples=tuple(zip(ts_price,df_tmp["normalized_gainloss"].values.astype(float)))
                arr_tuples=[(index_gainloss,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
            except Exception as e:
               print(e)
        else:
            #ax=df_tmp.plot(subplots=True,y=["normalized_gain","normalized_loss"],layout=(1,3))
            ax=df_tmp.plot(y=["normalized_gain","normalized_loss"])
            ax.set_title(ymd+ " price @ port "+ str(input_redis_port))
            price_pdf.savefig(ax.figure)
            
        #do the same for volume
        df_volume_data=all_data['df_volume_data']
        ts_volume=[int(i*bucket_size_msec+all_data["ts_volume_min"]) for i in range(len(df_volume_data))]
        ymd=str(datetime.fromtimestamp(all_data["ts_volume_min"]/1000,tz=tz)).split(' ')[0]
        print(ymd)
        df_tmp=pd.DataFrame(columns=df_volume_data.columns)
        for i, row in df_volume_data.iterrows():
            if(i>=window-1):
                first=df_volume_data.loc[i-window+1,:]
                last=df_volume_data.loc[i,:]
                percent=(last-first)/last
                df_tmp=df_tmp.append(percent,ignore_index=True)
            else:
               df_tmp= df_tmp.append(pd.Series(),ignore_index=True)
        df_tmp["gain"]=df_tmp.apply(lambda x: x[x>0].sum(),axis=1)
        df_tmp["loss"]=df_tmp.apply(lambda x: x[x<0].sum(),axis=1)
        df_tmp["gainloss"]=df_tmp["gain"]+df_tmp["loss"].abs()
        df_tmp["normalized_gain"]=(df_tmp["gain"]-df_tmp["gain"].min())/(df_tmp["gain"].max()-df_tmp["gain"].min())
        df_tmp["normalized_loss"]=(df_tmp["loss"]-df_tmp["loss"].min())/(df_tmp["loss"].max()-df_tmp["loss"].min())
        df_tmp["normalized_gainloss"]=(df_tmp["gainloss"]-df_tmp["gainloss"].min())/(df_tmp["gainloss"].max()-df_tmp["gainloss"].min())
        #df_tmp.plot(y=["gain","loss","gainloss"])
        #df_tmp.plot(y=["normalized_gain","normalized_loss","normalized_gainloss"])
        if(enableSectorIndustry):generateSectorIndustryGainLoss(df_tmp,ts_volume,redis_out,category='volume',window=window,input_redis_port=input_redis_port)
        if(isReportOnly==False):
            index_gain="mind:gain:volume:window:"+str(window)
            index_loss="mind:loss:volume:window:"+str(window)
            index_gainloss="mind:gainloss:volume:window:"+str(window)
            print("adding data for",index_gain,index_loss,index_gainloss, "port=",input_redis_port)
            try:
                #create index if does not exists
                if(redis_out.exists(index_gain)==0):
                    _=redis_out.create(index_gain)
                    _=redis_out.alter(index_gain,labels=labels)
                if(redis_out.exists(index_loss)==0):
                    _=redis_out.create(index_loss)
                    _=redis_out.alter(index_loss,labels=labels)
                if(redis_out.exists(index_gainloss)==0):
                    _=redis_out.create(index_gainloss)
                    _=redis_out.alter(index_gainloss,labels=labels)
                #push data gain
                arr_tuples=tuple(zip(ts_price,df_tmp["normalized_gain"].values.astype(float)))
                arr_tuples=[(index_gain,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
                #push data loss
                arr_tuples=tuple(zip(ts_price,df_tmp["normalized_loss"].values.astype(float)))
                arr_tuples=[(index_loss,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
                #push data gainloss
                arr_tuples=tuple(zip(ts_price,df_tmp["normalized_gainloss"].values.astype(float)))
                arr_tuples=[(index_gainloss,)+xs for xs in arr_tuples]
                _=redis_out.madd(arr_tuples)
            except Exception as e:
               print(e)
        else:
            ax=df_tmp.plot(y=["normalized_gain","normalized_loss"])
            ax.set_title(ymd+ " volume @ port "+ str(input_redis_port))
            volume_pdf.savefig(ax.figure)
        plt.close('all')
    
    price_pdf.close()
    volume_pdf.close()

def generateAllGainLossIndices(flushAll=False,includeLivePort=True, enableSectorIndustry=True,window=10,ports=[item for item in range(6400,6465)],prefix="rts1:01:symbol:",input_redis_host="localhost", redis_live_port=6381, output_redis_host="localhost", output_redis_port=6378, aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1,filters=["SYMSET=ACTIVE"],labels={"TYPE":"GAINLOSS"}):
    from redistimeseries.client import Client
    from pytz import timezone
    tz=timezone('US/Pacific')
    from datetime import datetime

    redis_out=Client(host=output_redis_host,port=output_redis_port)
    #Add live port to index generation
    if(includeLivePort):
        print("Adding the live port",redis_live_port,"to the ports for indext generation...")
        ports.append(redis_live_port)
    #Resetting indices. Ask for confirmation
    if(flushAll):
        x=input("Are you sure you want to delete all indices? (Y/N):")
        if(x=='Y'or x=='y'): 
            print("Removing all indices at",output_redis_port)
            redis_out.execute_command("flushall")
    #get raw data for each port
    for input_redis_port in ports:
        try:
            all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                     from_time=from_time,to_time=to_time,
                                     query_key=None,prefix=prefix,
                                     aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
        except Exception as e:
            print(e)
            print("Cannot read data at",input_redis_port)
        try:
            #Create indices
            #PRICE AND VOLUME
            for category in ['price','volume']:
                #####PRICE#####
                if(category=='price'): 
                    df_data=all_data['df_price_data']
                    ts_data=[int(i*bucket_size_msec+all_data["ts_price_min"]) for i in range(len(df_data))]
                    ymd=str(datetime.fromtimestamp(all_data["ts_price_min"]/1000,tz=tz)).split(' ')[0]
                    print(category,ymd)
                #####VOLUME#####
                else:
                    df_data=all_data['df_volume_data']
                    ts_data=[int(i*bucket_size_msec+all_data["ts_volume_min"]) for i in range(len(df_data))]
                    ymd=str(datetime.fromtimestamp(all_data["ts_volume_min"]/1000,tz=tz)).split(' ')[0]
                    print(category,ymd)
                df_tmp=pd.DataFrame(columns=df_data.columns)
                for i, row in df_data.iterrows():
                    if(i>=window-1):
                        first=df_data.loc[i-window+1,:]
                        last=df_data.loc[i,:]
                        percent=(last-first)/last
                        df_tmp=df_tmp.append(percent,ignore_index=True)
                    else:
                       df_tmp= df_tmp.append(pd.Series(),ignore_index=True)
                df_tmp["gain"]=df_tmp.apply(lambda x: x[x>0].sum(),axis=1)
                df_tmp["loss"]=df_tmp.apply(lambda x: x[x<0].sum(),axis=1)
                df_tmp["gainloss"]=df_tmp["gain"]+df_tmp["loss"].abs()
                df_tmp["normalized_gain"]=(df_tmp["gain"]-df_tmp["gain"].min())/(df_tmp["gain"].max()-df_tmp["gain"].min())
                df_tmp["normalized_loss"]=(df_tmp["loss"]-df_tmp["loss"].min())/(df_tmp["loss"].max()-df_tmp["loss"].min())
                df_tmp["normalized_gainloss"]=(df_tmp["gainloss"]-df_tmp["gainloss"].min())/(df_tmp["gainloss"].max()-df_tmp["gainloss"].min())
                ##CREATING GAIN AND LOSS INDICES
                index_gain="mind:gain:"+category+":window:"+str(window)
                index_loss="mind:loss:"+category+":window:"+str(window)
                index_gainloss="mind:gainloss:"+category+":window:"+str(window)
                print("adding data for",index_gain,index_loss,index_gainloss, "port=",input_redis_port, "category=",category)
                try:
                    #create index if does not exists
                    if(redis_out.exists(index_gain)==0):
                        _=redis_out.create(index_gain)
                        _=redis_out.alter(index_gain,labels=labels)
                    if(redis_out.exists(index_loss)==0):
                        _=redis_out.create(index_loss)
                        _=redis_out.alter(index_loss,labels=labels)
                    if(redis_out.exists(index_gainloss)==0):
                        _=redis_out.create(index_gainloss)
                        _=redis_out.alter(index_gainloss,labels=labels)
                    #push data gain
                    arr_tuples=tuple(zip(ts_data,df_tmp["normalized_gain"].values.astype(float)))
                    arr_tuples=arr_tuples[window-1:]
                    arr_tuples=[(index_gain,)+xs for xs in arr_tuples]
                    _=redis_out.madd(arr_tuples)
                    #push data loss
                    arr_tuples=tuple(zip(ts_data,df_tmp["normalized_loss"].values.astype(float)))
                    arr_tuples=[(index_loss,)+xs for xs in arr_tuples]
                    arr_tuples=arr_tuples[window-1:]

                    _=redis_out.madd(arr_tuples)
                    #push data gainloss
                    arr_tuples=tuple(zip(ts_data,df_tmp["normalized_gainloss"].values.astype(float)))
                    arr_tuples=[(index_gainloss,)+xs for xs in arr_tuples]
                    arr_tuples=arr_tuples[window-1:]
                    _=redis_out.madd(arr_tuples)
                    #GENERATE SECTOR-INDUSTRY INDICES
                    if(enableSectorIndustry):
                       generateSectorIndustryIndicesWithLAbels(df_tmp=df_tmp,ts_data=ts_data,l1File="finL2Extension.graphml",category=category,window=window,input_redis_host=input_redis_host,input_redis_port=input_redis_port,output_redis_host=output_redis_host,output_redis_port=output_redis_port)
                    
                    
                except Exception as e:
                   print(e)
            
        
        except Exception as e:
            print(e)
def generateSectorIndustryIndicesWithLAbels(df_tmp,ts_data,l1File="finL2Extension.graphml",category='price',window=10,input_redis_host='localhost',input_redis_port=6381,output_redis_host='localhost',output_redis_port=6378,labels={'TYPE': 'GAINLOSS'}):
    import networkx as nx
    import re
    import time
    import numpy as np
    G=nx.read_graphml(l1File) 
    #get sectors & industries and clean them                 
    print("generating sector & industry gain loss for",input_redis_port, category, " window=",window)
    nodes=pd.DataFrame.from_dict(dict(G.nodes(data=True)),orient='index')
    companies=list(nodes['symbol'].values)

    #nodes.index=nodes['symbol']
    sectors=list(nodes.sector.dropna().unique())
    #sectors=[re.sub('[^a-zA-Z0-9]+','',x) for x in sectors]
    industries=list(nodes.industry.dropna().unique())
    #industries=[re.sub('[^a-zA-Z0-9]+','',x) for x in industries]
    missing=[]
    df_clean_tmp=df_tmp.iloc[:,:-6] #the last 6 cols are gain loss sums  
    df_sectors_gains=pd.DataFrame(np.zeros((len(df_clean_tmp),len(sectors))),columns=sectors)
    df_sectors_loss=pd.DataFrame(np.zeros((len(df_clean_tmp),len(sectors))),columns=sectors)
    df_industries_gains=pd.DataFrame(np.zeros((len(df_clean_tmp),len(industries))),columns=industries)
    df_industries_loss=pd.DataFrame(np.zeros((len(df_clean_tmp),len(industries))),columns=industries)
    start=time.time()
    lookup_sectors=pd.DataFrame(columns=["sector","industry"])
    for i,row in df_clean_tmp.iterrows():
        data=row.dropna()
        if(i>=window-1):
            for t, val in data.iteritems():
                try:
                    subg=nx.ego_graph(G,t).nodes(data=True)._nodes
                    _=subg.pop("ticker",None)
                    if(len(subg)==2):_=subg.pop(t,None)
                    sect=''
                    ind=''
                    if('sector' in subg[list(subg.keys())[0]]):
                        sect=subg[list(subg.keys())[0]]['sector']
                    if('industry' in subg[list(subg.keys())[0]]):
                        ind=subg[list(subg.keys())[0]]['industry']

                    if(len(sect)>0):
                             if(val>0):
                                 df_sectors_gains.at[i,sect]+=float(val)
                             elif(val<0):
                                 df_sectors_loss.at[i,sect]+=float(val)
                    elif(i==window):
                         if(t not in missing):missing.append(t)
                    if(len(ind)>0):
                             if(val>0):
                                 df_industries_gains.at[i,ind]+=float(val)
                             elif(val<0):
                                 df_industries_loss.at[i,ind]+=float(val)
                             if(i==window):lookup_sectors.loc[len(lookup_sectors)]=[re.sub('[^a-zA-Z0-9]+','',sect) ,re.sub('[^a-zA-Z0-9]+','',ind)]
                    elif(i==window):
                        if(t not in missing):missing.append(t)
                except Exception as e:
                    print(e)
        
    print("cannot read sector and industry for",missing)                
    print("process time in sec=",time.time()-start)
    print("Sending sector & industry indices to redis...")
    lookup_sectors=lookup_sectors.drop_duplicates(subset='industry',keep='first')
    sendDfToRedis(df_sectors_gains,df_sectors_loss,df_industries_gains,df_industries_loss,ts_data,lookup_sectors,category,window,output_redis_host,output_redis_port,labels)
    
def sendDfToRedis(df_sectors_gains,df_sectors_loss,df_industries_gains,df_industries_loss,ts_data,lookup_sectors,category,window,output_redis_host='localhost',output_redis_port=6378,labels={'TYPE': 'GAINLOSS'}):
    from redistimeseries.client import Client
    from pytz import timezone
    tz=timezone('US/Pacific')
    from datetime import datetime
    import time
    import re
    redis_out=Client(host=output_redis_host,port=output_redis_port)

    ##SECTOR GAIN    
    for j,col in df_sectors_gains.iteritems():
        sect=re.sub('[^a-zA-Z0-9]+','',j)
        index_gain="mind:sector:"+sect+":gain:"+category+":window:"+str(window)
        print("adding data for",index_gain)
        try:
            #create index if does not exists
            if(redis_out.exists(index_gain)==0):
                _=redis_out.create(index_gain)
                labels['SECTOR']=sect.upper()
                _=redis_out.alter(index_gain,labels=labels)
           
            #push data gain
            arr_tuples=tuple(zip(ts_data,col.values.astype(float)))
            arr_tuples=arr_tuples[window-1:]
            arr_tuples=[(index_gain,)+xs for xs in arr_tuples]
            _=redis_out.madd(arr_tuples)         
        except Exception as e:
           print(e)
    ##SECTOR LOSS    
    for j,col in df_sectors_loss.iteritems():
        sect=re.sub('[^a-zA-Z0-9]+','',j)
        index_loss="mind:sector:"+sect+":loss:"+category+":window:"+str(window)
        print("adding data for",index_loss)
        try:
            #create index if does not exists
            if(redis_out.exists(index_loss)==0):
                _=redis_out.create(index_loss)
                labels['SECTOR']=sect.upper()
                _=redis_out.alter(index_loss,labels=labels)
           
            #push data gain
            arr_tuples=tuple(zip(ts_data,col.values.astype(float)))
            arr_tuples=arr_tuples[window-1:]
            arr_tuples=[(index_loss,)+xs for xs in arr_tuples]
            _=redis_out.madd(arr_tuples)         
        except Exception as e:
           print(e)
    
    ##INDUSTRY GAIN    
    for j,col in df_industries_gains.iteritems():
        ind=re.sub('[^a-zA-Z0-9]+','',j)
        index_gain="mind:industry:"+ind+":gain:"+category+":window:"+str(window)
        sect=list(lookup_sectors[lookup_sectors['industry']==ind]['sector'].values)[0]
        print("adding data for",index_gain)
        try:
            #create index if does not exists
            if(redis_out.exists(index_gain)==0):
                _=redis_out.create(index_gain)
                labels['SECTOR']=sect.upper()
                labels['INDUSTRY']=ind.upper()
                _=redis_out.alter(index_gain,labels=labels)
           
            #push data gain
            arr_tuples=tuple(zip(ts_data,col.values.astype(float)))
            arr_tuples=arr_tuples[window-1:]
            arr_tuples=[(index_gain,)+xs for xs in arr_tuples]
            _=redis_out.madd(arr_tuples)         
        except Exception as e:
           print(e)
    ##INDUSTRY LOSS    
    for j,col in df_industries_loss.iteritems():
        ind=re.sub('[^a-zA-Z0-9]+','',j)
        index_loss="mind:industry:"+ind+":loss:"+category+":window:"+str(window)
        sect=list(lookup_sectors[lookup_sectors['industry']==ind]['sector'].values)[0]
        print("adding data for",index_loss)
        try:
            #create index if does not exists
            if(redis_out.exists(index_loss)==0):
                _=redis_out.create(index_loss)
                labels['SECTOR']=sect.upper()
                labels['INDUSTRY']=ind.upper()
                _=redis_out.alter(index_loss,labels=labels)
           
            #push data gain
            arr_tuples=tuple(zip(ts_data,col.values.astype(float)))
            arr_tuples=arr_tuples[window-1:]
            arr_tuples=[(index_loss,)+xs for xs in arr_tuples]
            _=redis_out.madd(arr_tuples)         
        except Exception as e:
           print(e)

def fixNamingLabels(output_redis_host='localhost',output_redis_port=6378):
    from redistimeseries.client import Client
    from pytz import timezone
    tz=timezone('US/Pacific')
    from datetime import datetime
    import time
    import re
    import json
    redis_out=Client(host=output_redis_host,port=output_redis_port)
    keys=redis_out.execute_command("keys *")
    keys=[k.decode("utf-8") for k in keys]
    #Labeling window size
    for k in keys:
        w=int(k.split(":")[-1])
        x=redis_out.execute_command("ts.info "+k)
        for i in range(len(x)):
            item=x[i]
            if(type(item)==bytes):
                if(item.decode("utf-8")=='labels'):
                    break
        lab=[item.decode("utf-8") for sublist in x[i+1] for item in sublist]
        tmp_lab={}
        for j in range(0,len(lab),2):
            tmp_lab[lab[j]]=lab[j+1]
        if("WINDOW" not in tmp_lab):
            tmp_lab["WINDOW"]=w
            _=redis_out.alter(k,labels=tmp_lab)
    for k in keys:
         k_set=k.split(":")
         if("industry" in k and "industry" not in k_set):
             tmp_k=k
             tmp_k=tmp_k.replace("industry","industry:")
             _=redis_out.execute_command("RENAME "+k+ " "+tmp_k)
    for k in keys:
        w=int(k.split(":")[-1])
        x=redis_out.execute_command("ts.info "+k)
        for i in range(len(x)):
            item=x[i]
            if(type(item)==bytes):
                if(item.decode("utf-8")=='labels'):
                    break
        lab=[item.decode("utf-8") for sublist in x[i+1] for item in sublist]
        tmp_lab={}
        for j in range(0,len(lab),2):
            tmp_lab[lab[j]]=lab[j+1]
        
        if("SUBTYPE" not in tmp_lab ):
            if(':gain:' in k):
                tmp_lab["SUBTYPE"]="GAIN"
            elif(':loss:' in k):
                tmp_lab["SUBTYPE"]="LOSS"
        
        if("CATEGORY" not in tmp_lab ):
            if(':industry:' in k):
                tmp_lab["CATEGORY"]="INDUSTRY"
            elif(':sector:' in k):
                tmp_lab["CATEGORY"]="SECTOR"
        if("BASEDON" not in tmp_lab ):
            if(':price:' in k):
                tmp_lab["BASEDON"]="PRICE"
            elif(':volume:' in k):
                tmp_lab["BASEDON"]="VOLUME"
        
            _=redis_out.alter(k,labels=tmp_lab)
    
    
    _=redis_out.execute_command("SAVE")
    
    
    
if __name__ == "__main__":
    pass
    # df_spike_3=df_tmp.loc[225]
    # df_spike_20=df_tmp.loc[240]
    # sorted_3=df_spike_3.sort_values(ascending=False)
    # sorted_20=df_spike_20.sort_values(ascending=False)
    # sorted_3.to_csv('win3_225.csv')
    # sorted_20.to_csv('win20_240.csv')
    
    # ts_data=sorted_3
    # # ports=[item for item in range(6400,6470)]
    # ts_freq_threshold=5#ignore an element in the histogram if it involves less than 20 simultaneous regime changes
    # peek_ratio=0.25
    # windows=[10]
    # for p in ports:
    #     visualizeIndexOnRegimeChanges(input_redis_port=p,ts_freq_threshold=ts_freq_threshold,peek_ratio=peek_ratio,windows=windows)
    # #     break
    # ports=[item for item in range(6400,6470)]
    # windows=[10,20]
    # for p in ports:    
    #     runMPonIndices(isSave=True,input_redis_port=p,windows=windows)
    # windows=[50,100]
    # for p in ports:    
    #     runMPonIndices(isSave=True,input_redis_port=p,windows=windows)
    # import stumpy 
    # from numba import cuda
    # all_gpu_devices=[device.id for device in cuda.list_devices()]
    # m=L=10
    # ts_data=df_tmp["gain"].iloc[:,0].dropna().values
    # mp=stumpy.gpu_stump(ts_data, m=m,device_id=all_gpu_devices)
    # correct_arc_curve, regime_locations=stumpy.fluss(mp[:,1],L=L,n_regimes=20,excl_factor=1)
    # regime_locations=[i for i in regime_locations if i!=0]
    # fig,axs=plt.subplots(1,1) 
    # axs.plot(ts_data)
    # trans=axs.get_xaxis_transform()
    # for i in range(len(regime_locations)):
    #     axs.axvline(regime_locations[i],lw=0.5,color='red')
    #     axs.text(x=regime_locations[i],y=1, s=str(i+1),size=7,transform=trans)
    # plt.figure()
    #ports=[item for item in range(6400,6470)]
    #for p in ports:
    #    aggregateData(input_redis_port=p)
    #    print(p,"Done")
    
    #x=df_normalized_price.iloc[0,:].values
            #x=x[~np.isnan(x)]
            #x=(x-x.min())/(x.max()-x.min())
    # df_price_data.plot(y=['AAON'])
    # plt.axvline(x=regimes_aaon[0])
    # plt.axvline(x=regimes_aaon[1])
    # val=list(df_price_data['AAON'].values)
    # val=[x for x in val if str(x)!='nan']
    # x=mp.compute(val,windows=[10])
    # x=mp.discover.regimes(x, num_regimes=20)
    # regimes_aaon= list(filter(lambda x: x != 0, x["regimes"]))
    # cols=[]
    # for i,row in df_regimes_price.iterrows():
    #     clean_row=[x for x in list(row) if str(x)!='nan']
    #     if(len(list(clean_row))==2):
    #         #print(i,list(row))
    #         cols.append(df_price_data.columns[i])
    # df_new=df_price_data[cols]
    # df_new=(df_new-df_new.min())/(df_new.max()-df_new.min())
    # df_new["mean_val"]=df_new.mean(axis=1,skipna=True)
    # df_new.plot(y=["mean_val"])