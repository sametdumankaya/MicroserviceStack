## Importing our packages
import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport log, M_PI
# Defining our numpy types
ctypedef np.float64_t np_float_t
ctypedef np.int64_t np_int_t
## Compiler directives
# cython: boundscheck=False
# cython: cdivision=True
# cython: wraparound=False
# Defining our fast Normal cost
cdef class OptimizedNormalCost:
    
    cdef:
        np_float_t[:] sum_stat1
        np_float_t[:] sum_stat2
        int min_size
        int n
        
    cpdef double error(self, int start, int stop):
            cdef:
                double l = stop - start
                double x1 = self.sum_stat1[stop] - self.sum_stat1[start]
                double x2 = self.sum_stat2[stop] - self.sum_stat2[start]
                double sigsq = max((x2-((x1*x1)/l))/l, 0.000000001)
            
            # Calculating our normal cost
            return l*(log(2*M_PI)+log(sigsq)+1)
    def __init__(self):
        self.sum_stat1 = np.float64([])
        self.sum_stat2 = np.float64([])
        self.min_size = 3
    def fit(self, np.ndarray[np_float_t, ndim=1] signal):
        self.n = signal.shape[0]
        # Creating our test statistics
        self.sum_stat1 = np.append(0, signal.cumsum())
        self.sum_stat2 = np.append(0, (signal**2).cumsum())
        return self

# Defining our PELT class
cdef class OptimizedPelt:
    
    cdef:
        object model
        np_float_t[:] signal
    
    def __init__(self, object model):
        self.model = model
    
    cpdef object fit(self, np.ndarray[np_float_t, ndim=1] signal):
        self.signal = signal
        self.model.fit(signal)
        return self
    cpdef list predict(self, float pen):
        cdef:
            int i, n, current_tau, prev_tau, best_prev_tau_ind, new_prev_tau_size, current_ind
            float current_best_cost
            list prev_taus, cp_inds
            np_float_t[:] best_cost, cost_prev_tau
            np_int_t[:] prev_cp_ind
            
        # Initializing for PELT
        n = self.signal.shape[0]
        best_cost = np.empty(n+1, dtype=np.float64)
        best_cost[0] = -pen
        
        # Calculating our initial segmentation costs
        for i in range(3, 5):
            best_cost[i] = self.model.error(0, i)
        
        # Setting up our list of taus
        prev_cp_ind = np.zeros(n+1, dtype=np.int64)
        prev_taus = [0, 2]
        
        # Iterating through our time series
        for current_tau in range(4, n+1):
            
            # Calculating segmentation costs
            cost_prev_tau = np.empty(len(prev_taus), dtype=np.float64)
            for i, prev_tau in enumerate(prev_taus):
                cost_prev_tau[i] = best_cost[prev_tau] + self.model.error(prev_tau, current_tau) + pen
                
            # Determining the best tau and best cost
            best_prev_tau_ind = np.argmin(cost_prev_tau)
            best_cost[current_tau] = cost_prev_tau[best_prev_tau_ind]
            prev_cp_ind[current_tau] = prev_taus[best_prev_tau_ind]
            current_best_cost = cost_prev_tau[best_prev_tau_ind]
            
            # Pruning taus that cannot be changepoints according to pruning rule
            new_prev_tau_size = 0
            for i in range(0, len(prev_taus)):
                if cost_prev_tau[i] < current_best_cost + pen:
                    prev_taus[new_prev_tau_size] = prev_taus[i]
                    new_prev_tau_size += 1
            del prev_taus[new_prev_tau_size:(len(prev_taus)-new_prev_tau_size)]
            
            # Appending the next tau
            prev_taus.append(current_tau - 1)
        
        # Returning all changepoints detected
        cp_inds = []
        current_ind = prev_cp_ind[n]
        while current_ind != 0:
            cp_inds.append(current_ind-1)
            current_ind = prev_cp_ind[current_ind]
        cp_inds = sorted(cp_inds)
        return cp_inds