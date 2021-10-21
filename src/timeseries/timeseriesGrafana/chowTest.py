import numpy as np
from scipy.stats import f

def find_rss (y, x):
        """This function finds the residual sum of squares for a given set of data
        Args:
            y: Array like y-values for data subset
            x: Array like x-values for data subset
        Returns:
            rss: Returns residual sum of squares of the linear equation represented by that data
            length: The number of n terms that the data represents
        """
        A = np.vstack([x, np.ones(len(x))]).T
        #Fit a line to it. get the rss
        rss = np.linalg.lstsq(A, y, rcond=None)[1]
        length = len(y)
        return (rss, length)
    
def f_value(y1, x1, y2, x2):
    """This is the f_value function for the Chow Test
    Args:
        y1: Array like y-values before the breakpoint
        x1: Array like x-values before the breakpoint
        y2: Array like y-values after the breakpoint
        x2: Array like x-values after the breakpoint
    Returns:
        F-value
    """
    rss_total, n_total = find_rss(np.append(y1, y2), np.append(x1, x2))
    rss_1, n_1 = find_rss(y1, x1)
    rss_2, n_2 = find_rss(y2, x2)

    chow_nom = (rss_total - (rss_1 + rss_2)) / 2
    chow_denom = (rss_1 + rss_2) / (n_1 + n_2 - 4)
    return chow_nom / chow_denom

def p_value(y1, x1, y2, x2, **kwargs):
    F = f_value(y1, x1, y2, x2, **kwargs)
    if not F:
        return 1
    df1 = 2
    df2 = len(x1) + len(x2) - 4
    p_val = f.sf(F[0], df1, df2)
    return p_val