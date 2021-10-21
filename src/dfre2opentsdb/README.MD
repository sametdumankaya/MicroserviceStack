These codes are for accessing Drew Pletcher's Short Stack telemetry data via opentsdb. The current server address is at url="http://spa-cxdp-opentsdb-1.cisco.com:4242" 
Note that the link works in FireFox but not in Chrome if you want to visit and browse the database from a web interface. 
If combined with an aggregator and with a commong starting date like "start=1d-ago", it is possible to query multiple metrics with a single call.

- dfre2opentsdb.py contains the class to create an object to query all available metrics, get time series data for all the metrics given a time delta (1 hours, 2 hours, 24 hours, etc.). 

- After retrieving all data, the test code calls matrix profile on the first time series to demonstrate how regime changes are detected and plotted. This demonstrates semantic segmentation.

- The final line, "all_cac,all_regimes=getSemanticSegmentationFromMP(df)", performs semantic segmentation on all retrieved time series. This code C-based but still as it performs the analysis on thousands of time series. 

- matrix_profile.py contains the test code and the functions for matrix profile-semantic segmentation. 

- Note that SCAMP is faster MP library. However, it does not have semantic segmentation implementation yet. So this code is based on STUMPY (https://stumpy.readthedocs.io/en/latest/motivation.html).

- STUMPY FLOSS is more appropriate for useful streaming data because it t calculates a modified version of the corrected arc curve assuming that the causal arcs will be from left to right, which is from old data to new data (https://stumpy.readthedocs.io/en/latest/Tutorial_Semantic_Segmentation.html#FLUSS )

-- n_regimes parameter is to give a max number of expected regimes in the time series. 

-- matrix profile windows size "m" and subsquence length "L" are usually set to the same number, such as 100. 

-- These 3 are main and important parameters to set.

-- NOTE THAT: If the interval between two regime changes is "window_size + 1", the latest one is a false positive. In other words, if n_regimes > actual number of regimes in the data, the semantic segmentation returns false positive. For example, if the code states that there are 4 regime with the time stamps at 100, 201, 302, 201 and 302 are most probably false positives (July 20, 2020). 
