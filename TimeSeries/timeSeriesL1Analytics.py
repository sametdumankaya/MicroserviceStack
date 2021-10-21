import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import chowTest


def get_ts_mbl(ts: pd.DataFrame, breaks: list):
    import math
    """This functions receives a singe time series and corresponding list of breaks.
    Returns a list of m,b,l for each lines for each interval"""
    ts = ts.values.tolist()
    line_eq = []
    start_ind = 0
    for i in range(len(breaks)):
        end_ind = breaks[i]
        x = list(range(start_ind, end_ind))
        y = ts[start_ind:end_ind]
        m, b = np.polynomial.polynomial.polyfit(x, y, 1)
        l = math.pow(math.pow((end_ind - start_ind) * m + b, 2) + math.pow((end_ind - start_ind), 2), 0.5)
        line_eq.append([m, b, l])
        start_ind = end_ind
    end_ind = len(ts) - 1
    x = list(range(start_ind, end_ind))
    y = ts[start_ind:end_ind]
    m, b = np.polynomial.polynomial.polyfit(x, y, 1)
    l = math.pow(math.pow((end_ind - start_ind) * m + b, 2) + math.pow((end_ind - start_ind), 2), 0.5)
    line_eq.append([m, b, l])
    return line_eq


def removeFPBreaks(df: pd.DataFrame, strucBreaks: list, model: str) -> list:
    """This function receives a df of time series and structural breaks.
    It eliminates false positives by applying Chow Test and model equation comparison"""
    # TODO: Implement for l2 and rbf models
    newBreaks = strucBreaks
    if (model == 'l1'):
        newBreaks = []
        for i in range(len(df.columns)):
            line = []
            cnt = 0
            breaks = strucBreaks[i]
            ts = df.iloc[:, i].values.tolist()
            for br in breaks:
                x1 = ts[0:br]
                x1 = list(range(0, br))
                x2 = list(range(0, len(ts) - br))
                y1 = ts[0:br]
                y2 = ts[br:]
                p = chowTest.p_value(y1, x1, y2, x2)
                if (p < 0.05):
                    line.append(br)
                else:
                    cnt = cnt + 1
            if (cnt > 0):
                print(cnt, "break(s) removed for failing the Chow Test for the time series #", i + 1)
            newBreaks.append(line)
        newBreaks_phase2 = []
        for i in range(len(df.columns)):
            line_eq = get_ts_mbl(df.iloc[:, i], newBreaks[i])
            tmp_break = []
            cnt = 0
            for j in range(len(line_eq) - 1):
                m1 = line_eq[j][0]
                b1 = line_eq[j][1]
                m2 = line_eq[j + 1][0]
                b2 = line_eq[j + 1][1]
                if (min(m1, m2) * 0.05 + min(m1, m2) >= max(m1, m2) and min(b1, b2) * 0.05 + min(b1, b2) >= max(b1,
                                                                                                                b2)):
                    cnt = cnt + 1
                else:
                    tmp_break.append(newBreaks[i][j])
            if (cnt > 0):
                print(cnt, "break(s) removed for failing  for", model, " model check for time series #", i + 1)
            newBreaks_phase2.append(tmp_break)
        newBreaks = newBreaks_phase2
    return newBreaks


def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-((x - mean) / 4 / stddev) ** 2)


def plotEventHistograms(histogram_cnt: list, number_of_samples: int, events: pd.DataFrame) -> None:
    plt.plot(range(number_of_samples), histogram_cnt)
    for i, row in events.iterrows():
        start_event = row[0]
        end_event = row[2]
        peek = row[1]
        x_values = np.linspace(0, number_of_samples, 1000)
        plt.plot(x_values,
                 gaussian(x_values, histogram_cnt[peek], peek, (end_event + start_event) / (end_event - start_event)))
    plt.show()
    return


def getHistogramFromUnalignedDf(df_regimes: pd.DataFrame(), ts, ts_min, ts_max, bucket_size_msec):
    all_ts = list(range(ts_min, ts_max + bucket_size_msec, bucket_size_msec))
    # all_ts = [item for x in ts for item in x]
    # all_ts = list(range(ts_min, ts_max + 1000, 1000))
    histogram = [0] * len(all_ts)
    for index, rows in df_regimes.iterrows():
        for r in rows:
            if not pd.isnull(r):
                r = int(r)
                try:
                    local_ts = ts[int(index)][r]
                    global_ind = int(all_ts.index(local_ts))
                    histogram[global_ind] = histogram[global_ind] + 1
                except Exception as e:
                    continue
    return histogram


def getMatrixProfile(ts: np.ndarray, isFigures: bool):
    """This function receives an array of numbers, performs matrix profile analysis on it"""
    """Returns discord, top 3 motifs and corresponding 6 figures for various window sizes"""
    import os
    import numpy as np
    # np raises error for missing values due to sampling error in ts
    np.seterr(all='ignore')
    try:
        import matrixprofile as mp
    except ImportError:
        print("Trying to Install required module: matrixprofile\n")
        os.system('python -m pip install matrixprofile')
        import matrixprofile as mp
    profile, figures = mp.analyze(ts, n_jobs=-1)
    if (isFigures):
        return profile, figures
    else:
        return profile


def cleanAlignmentValues(df: pd.DataFrame, alignmentValue: int):
    """This function receives a set of time series and cleans the alignment value in it"""
    import numpy as np
    df = df.replace(alignmentValue, np.NaN)
    return df


def normalizeTimeSeries(df: pd.DataFrame):
    """This function receives a time series dataframe and normalizes columns."""
    """It returns the normalized dataframe and df composed of horizontal lines"""
    import numpy as np
    np.seterr(all='raise')
    new_df = pd.DataFrame()
    horizontal_cluster = pd.DataFrame()
    for i in range(len(df.columns)):
        tmp = df.iloc[:, i]
        min_val = np.nanmin(tmp.values)
        max_val = np.nanmax(tmp.values)
        if (min_val != max_val):
            tmp = (tmp - min_val) / (max_val - min_val)
            new_df.insert(len(new_df.columns), tmp.name, tmp)
        else:
            horizontal_cluster.insert(len(horizontal_cluster.columns), tmp.name, tmp)
    return new_df, horizontal_cluster


def filter_lines(df: pd.DataFrame):
    """This function receives a pandas dataframe of time series and removes the lines (constant slopes).
    Each column is a normalized time series data."""
    import numpy as np
    new_df = pd.DataFrame()
    line_cluster = pd.DataFrame()
    for i in range(len(df.columns)):
        # Derivative of the time series
        dTs = np.gradient(df.iloc[:, i].values)
        min_val = np.nanmin(dTs)
        max_val = np.nanmax(dTs)
        tmp = df.iloc[:, i]
        if (min_val != max_val):  # not constant slope
            new_df.insert(len(new_df.columns), tmp.name, tmp)
        else:
            line_cluster.insert(len(line_cluster.columns), tmp.name, tmp)
    return new_df, line_cluster


def filter_spikes(df: pd.DataFrame):
    """This function received a dataframe and removes spike signals (=all valus are 0 or 1)."""
    """first return argument is non-spike signals, the second one for the spikes"""
    new_df = pd.DataFrame()
    spike_cluster = pd.DataFrame()
    for i in range(len(df.columns)):
        tmp = df.iloc[:, i]
        uniques = tmp.unique()
        uniques = [x for x in uniques if str(x) != 'nan']
        uniques = [x for x in uniques if x not in [0.0, 1.0]]
        if (len(uniques) <= 1):  # spike like
            spike_cluster.insert(len(spike_cluster.columns), tmp.name, tmp)
        else:
            new_df.insert(len(new_df.columns), tmp.name, tmp)
    return new_df, spike_cluster


def filter_no_structuralBreaks(df: pd.DataFrame, strucBreaks: list, split_limit: int):
    """This function received a dataframe, and an array of sbreaks' locations 
    and removes signals that have no structural breaks"""
    subset_df = pd.DataFrame()
    cluster_3 = pd.DataFrame()
    for i in range(len(df.columns)):
        tmp = df.iloc[:, i]
        if (len(strucBreaks[i]) > 0 and len(strucBreaks[i]) < split_limit):
            subset_df.insert(len(subset_df.columns), tmp.name, tmp)
        else:
            cluster_3.insert(len(cluster_3.columns), tmp.name, tmp)
    strucBreaks = [x for x in strucBreaks if x != [] and len(x) < split_limit]
    return subset_df, cluster_3, strucBreaks


def plot_ts(subset_df, col_start, col_end, ts_start, ts_end):
    """This function receives a pandas dataframe and returns the line plot of data between given ranges"""
    fig = subset_df.iloc[ts_start:ts_end, col_start:col_end].plot.line(legend=False).get_figure()
    return fig


def binarySplitBreaks(dfObj: pd.DataFrame, splitCriterion_start: int, splitCriterion_end: int, col: int):
    """This function receives a df of structural break for multiple time series. 
    Splits the df according to the split criteria for the break's location"""
    import math
    smaller_breaks = pd.DataFrame(columns=dfObj.columns)
    larger_breaks = pd.DataFrame(columns=dfObj.columns)
    for index, row in dfObj.iterrows():
        l = list(row)
        if (math.isnan(l[col]) == False):
            if (splitCriterion_start <= l[col] and l[col] <= splitCriterion_end):
                smaller_breaks.loc[len(smaller_breaks)] = l
            else:
                larger_breaks.loc[len(larger_breaks)] = l
    return larger_breaks, smaller_breaks


def binarySplitDf(remaining: pd.DataFrame, splitCriterion_start: int, splitCriterion_end: int, col: int,
                  breaks_df: pd.DataFrame):
    """This function receives a df of time series and a df of structural breaks for multiple time series. 
    Splits the the time series df according to the split criteria using the breaks_df"""
    import numpy as np
    strucBreaks = []
    for index, rows in breaks_df.iterrows():
        strucBreaks.append(rows.to_list())
    strucBreaks = [[int(x) for x in y if not np.isnan(x)] for y in strucBreaks]
    smaller_df = pd.DataFrame()
    larger_df = pd.DataFrame()
    for i in range(len(remaining.columns)):
        lst_b = strucBreaks[i]
        tmp = remaining.iloc[:, i]
        if (splitCriterion_start <= lst_b[col] and lst_b[col] <= splitCriterion_end):
            smaller_df.insert(len(smaller_df.columns), tmp.name, tmp)
        else:
            larger_df.insert(len(larger_df.columns), tmp.name, tmp)
    return larger_df, smaller_df


def splitSquaresFromSpikes(spike_cluster: pd.DataFrame):
    """This function receives a df with mixed square and spike signals.
    It splits them and returns the two separate sets"""
    squares_df = pd.DataFrame()
    spikes_df = pd.DataFrame()
    for i in range(len(spike_cluster.columns)):
        added = False
        tmp = spike_cluster.iloc[:, i]
        arr = tmp.values.tolist()
        for i in range(len(arr) - 1):
            val1 = arr[i]
            val2 = arr[i + 1]
            if (val1 != [] and val2 != []):
                if (val1 > 0 and val2 > 0):
                    squares_df.insert(len(squares_df.columns), tmp.name, tmp)
                    added = True
                    break
        if (not added):
            spikes_df.insert(len(spikes_df.columns), tmp.name, tmp)
    return squares_df, spikes_df


def getHistogramFromDf(dfObj: pd.DataFrame, ts_len: int):
    """This function receives a dataframe of structural breaks and flattens it (macro scale)"""
    histogram_cnt = []
    counts = pd.value_counts(dfObj.values.flatten())
    for i in range(ts_len):
        if (counts.get(i) != None):
            histogram_cnt.append(counts.get(i))
        else:
            histogram_cnt.append(0)
    return histogram_cnt


def analyzeHistogramForEvents(df_l1_concepts: pd.DataFrame):
    number_of_samples = int(df_l1_concepts['number_of_samples'][0:1].values)
    sampling_rate = int(df_l1_concepts['sampling_rate'][0:1].values)
    df_l1_concepts = pd.DataFrame(df_l1_concepts['strucBreaks'])
    strucBreaks = []
    for index, rows in df_l1_concepts.iterrows():
        data = (rows.values[0])[1:-1]
        data = [int(i) for i in data.split(',')]
        strucBreaks.append(data)
    dfObj = pd.DataFrame(strucBreaks)
    histogram_cnt = getHistogramFromDf(dfObj, number_of_samples)
    ts_freq_threshold = 20
    peek_ratio = 0.3
    events = getCandidateEvents(histogram_cnt, number_of_samples, ts_freq_threshold, peek_ratio, sampling_rate)
    events.index.name = 'Event Number'
    events.index += 1
    return strucBreaks, histogram_cnt, events


def getCandidateEvents(histogram_cnt: list, ts_len: int, ts_freq_threshold: int, peek_ratio: float, sampling_rate: int):
    """This function analysis the histogram of structural breaks and creates a dataframe of events"""
    import numpy as np
    from scipy.signal import find_peaks
    from heapq import nsmallest
    events = pd.DataFrame(columns=['leading indicator', 'main indicator', 'trailing indicator'])
    # Candidates above the threshold
    filter_cnt = []
    for cnt in histogram_cnt:
        if (cnt > ts_freq_threshold):
            filter_cnt.append(int(cnt))
        else:
            filter_cnt.append(0)
    x = np.array(filter_cnt)
    peax, _ = find_peaks(x, height=np.max(filter_cnt) * peek_ratio)

    # merge immediately conseq peaks
    peaks = []
    for p in range(0, len(peax) - 1):
        if (abs(peax[p] - peax[p + 1]) <= 2):
            peaks.append(filter_cnt.index(min(filter_cnt[peax[p]], filter_cnt[peax[p + 1]]), peax[p]))
    peaks = [x for x in peax if x not in peaks]
    # merge peaks with no breaks between
    tmp = []
    for p in range(0, len(peaks) - 1):
        if (np.max(filter_cnt[peaks[p] + 1:peaks[p + 1]]) == 0):
            tmp.append(filter_cnt.index(min(filter_cnt[peaks[p]], filter_cnt[peaks[p + 1]]), peaks[p]))
    peaks = [x for x in peaks if x not in tmp]

    for i in range(len(peaks)):
        if (i == 0):
            leading_indicator = histogram_cnt.index(np.max(histogram_cnt[0:peaks[0]]))
        else:
            leading_indicator = filter_cnt.index(np.max(filter_cnt[peaks[i - 1] + 1:peaks[i] - 1]), peaks[i - 1] + 1)
        main_indicator = peaks[i]
        s_int = main_indicator + 1
        if (i == len(peaks) - 1):
            e_int = ts_len
        else:
            e_int = peaks[i + 1] - 1
        trailing_space = nsmallest(2, np.unique(filter_cnt[s_int:e_int]))[-1]
        trailing_indicator = filter_cnt.index(trailing_space, s_int)
        events.loc[len(events)] = [leading_indicator, main_indicator, trailing_indicator]
    return events
