"""
First Order Exponentialy Weighted Fuzzy Time Series by Sadaei et al. (2013)

H. J. Sadaei, R. Enayatifar, A. H. Abdullah, and A. Gani, “Short-term load forecasting using a hybrid model with a 
refined exponentially weighted fuzzy time series and an improved harmony search,” Int. J. Electr. Power Energy Syst., vol. 62, no. from 2005, pp. 118–129, 2014.
"""

import numpy as np
from pyFTS.common import FuzzySet,FLR,fts, flrg

default_c = 1.1


class ExponentialyWeightedFLRG(flrg.FLRG):
    """First Order Exponentialy Weighted Fuzzy Logical Relationship Group"""
    def __init__(self, LHS, **kwargs):
        super(ExponentialyWeightedFLRG, self).__init__(1, **kwargs)
        self.LHS = LHS
        self.RHS = []
        self.count = 0.0
        self.c = kwargs.get("c",default_c)
        self.w = None

    def append(self, c):
        self.RHS.append(c)
        self.count = self.count + 1.0

    def weights(self):
        if self.w is None:
            wei = [self.c ** k for k in np.arange(0.0, self.count, 1.0)]
            tot = sum(wei)
            self.w = np.array([k / tot for k in wei])
        return self.w

    def __str__(self):
        tmp = self.LHS.name + " -> "
        tmp2 = ""
        cc = 0
        wei = [self.c ** k for k in np.arange(0.0, self.count, 1.0)]
        tot = sum(wei)
        for c in sorted(self.RHS, key=lambda s: s.name):
            if len(tmp2) > 0:
                tmp2 = tmp2 + ","
            tmp2 = tmp2 + c.name + "(" + str(wei[cc] / tot) + ")"
            cc = cc + 1
        return tmp + tmp2

    def __len__(self):
        return len(self.RHS)


class ExponentialyWeightedFTS(fts.FTS):
    """First Order Exponentialy Weighted Fuzzy Time Series"""
    def __init__(self, name, **kwargs):
        super(ExponentialyWeightedFTS, self).__init__(1, "EWFTS", **kwargs)
        self.name = "Exponentialy Weighted FTS"
        self.detail = "Sadaei"
        self.c = kwargs.get('c', default_c)

    def generate_flrg(self, flrs, c):
        flrgs = {}
        for flr in flrs:
            if flr.LHS.name in flrgs:
                flrgs[flr.LHS.name].append(flr.RHS)
            else:
                flrgs[flr.LHS.name] = ExponentialyWeightedFLRG(flr.LHS, c=c);
                flrgs[flr.LHS.name].append(flr.RHS)
        return (flrgs)

    def train(self, data, **kwargs):
        self.c = kwargs.get('parameters', default_c)
        if kwargs.get('sets', None) is not None:
            self.sets = kwargs.get('sets', None)
        ndata = self.apply_transformations(data)
        tmpdata = FuzzySet.fuzzyfy_series_old(ndata, self.sets)
        flrs = FLR.generate_recurrent_flrs(tmpdata)
        self.flrgs = self.generate_flrg(flrs, self.c)

    def forecast(self, data, **kwargs):
        l = 1

        data = np.array(data)

        ndata = self.apply_transformations(data)

        l = len(ndata)

        ret = []

        for k in np.arange(0, l):

            mv = FuzzySet.fuzzyfy_instance(ndata[k], self.sets)

            actual = self.sets[np.argwhere(mv == max(mv))[0, 0]]

            if actual.name not in self.flrgs:
                ret.append(actual.centroid)
            else:
                flrg = self.flrgs[actual.name]
                mp = flrg.get_midpoints()

                ret.append(mp.dot(flrg.weights()))

        ret = self.apply_inverse_transformations(ret, params=[data])

        return ret
