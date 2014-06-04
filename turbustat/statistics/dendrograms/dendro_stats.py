
'''

Dendrogram statistics as described in Burkhart et al. (2013)
Two statistics are contained:
    * number of leaves + branches vs. $\delta$ parameter
    * statistical moments of the intensity histogram

Requires the astrodendro package (http://github.com/astrodendro/dendro-core)

'''

import numpy as np
from pandas import HDFStore, Series, DataFrame
import statsmodels.formula.api as sm
from scipy.interpolate import UnivariateSpline
from mecdf import mecdf


class DendroDistance(object):

    """docstring for DendroDistance"""

    def __init__(self, file1, file2, timestep, nbins="best",
                 min_features=1000):
        super(DendroDistance, self).__init__()

        self.file1 = HDFStore(file1)
        self.file2 = HDFStore(file2)
        self.nbins = nbins

        if timestep[0] != "/":  # Saving in HDF5 adds this to the beginning
            timestep = "/" + timestep

        assert timestep in self.file1.keys()
        assert timestep in self.file2.keys()

        self.file1 = self.file1[timestep]
        self.file2 = self.file2[timestep]

        assert (self.file1["Deltas"] == self.file2["Deltas"]).all()
        self.deltas1 = np.log10(self.file1["Deltas"])
        self.deltas2 = np.log10(self.file2["Deltas"])
        self.numdata1 = np.log10(self.file1["Num Features"])
        self.numdata2 = np.log10(self.file2["Num Features"])

        # Set the minimum number of components to create a histogram
        self.cutoff = min(np.argwhere((self.file1["Num Features"] < min_features) == 1)[0],
                          np.argwhere((self.file2["Num Features"] < min_features) == 1)[0])[0]

        self.histograms1 = None
        self.histograms2 = None
        self.bins = []
        self.mecdf1 = None
        self.mecdf2 = None

        self.num_results = None
        self.num_distance = None
        self.histogram_distance = None

    def numfeature_stat(self, verbose=False):
        '''
        '''

        # Remove points where log(numdata)=0
        if (self.numdata1 == 0).any() or (self.numdata2 == 0).any():
            self.deltas1 = self.deltas1[self.numdata1 > 0]
            self.deltas2 = self.deltas2[self.numdata2 > 0]

            self.numdata1 = self.numdata1[self.numdata1 > 0]
            self.numdata2 = self.numdata2[self.numdata2 > 0]

        # Approximate knot location using linear splines with minimal smoothing
        break1 = break_spline(self.deltas1, self.numdata1, k=1, s=1)
        break2 = break_spline(self.deltas2, self.numdata2, k=1, s=1)

        self.numdata1 = self.numdata1.ix[np.where(self.deltas1 > break1)]
        self.numdata2 = self.numdata2.ix[np.where(self.deltas2 > break2)]
        clip_delta1 = self.deltas1.ix[np.where(self.deltas1 > break1)]
        clip_delta2 = self.deltas2.ix[np.where(self.deltas2 > break2)]

        # Set up columns for regression
        dummy = [0] * len(clip_delta1) + [1] * len(clip_delta2)
        x = np.concatenate((clip_delta1, clip_delta2))
        regressor = x.T * dummy

        numdata = np.concatenate((self.numdata1, self.numdata2))

        d = {"dummy": Series(dummy), "scales": Series(x),
             "log_numdata": Series(numdata), "regressor": Series(regressor)}

        df = DataFrame(d)

        model = sm.ols(
            formula="log_numdata ~ dummy + scales + regressor", data=df)

        self.num_results = model.fit()

        self.num_distance = np.abs(self.num_results.tvalues["regressor"])
        if verbose:

            print self.num_results.summary()

            import matplotlib.pyplot as p
            p.plot(clip_delta1, self.numdata1, "bD",
                   clip_delta2, self.numdata2, "gD")
            p.plot(df["scales"][:len(self.numdata1)],
                   self.num_results.fittedvalues[:len(self.numdata1)], "b",
                   df["scales"][-len(self.numdata2):],
                   self.num_results.fittedvalues[-len(self.numdata2):], "g")
            p.grid(True)
            p.xlabel(r"log $\delta$")
            p.ylabel("log Number of Features")
            p.show()

        return self

    def histogram_stat(self, verbose=False):
        '''
        '''

        if self.nbins == "best":
            self.nbins = [int(round(np.sqrt((n1 + n2) / 2.))) for n1, n2 in
                          zip(self.file1["Num Features"].ix[:self.cutoff],
                              self.file2["Num Features"].ix[:self.cutoff])]
        else:
            self.nbins = [self.nbins] * len(self.deltas1.ix[:self.cutoff])

        self.histograms1 = np.empty(
            (len(self.deltas1.ix[:self.cutoff]), np.max(self.nbins)))
        self.histograms2 = np.empty(
            (len(self.deltas2.ix[:self.cutoff]), np.max(self.nbins)))

        for n, (data1, data2, nbin) in enumerate(
                zip(self.file1["Histograms"].ix[:self.cutoff],
                    self.file2["Histograms"].ix[:self.cutoff], self.nbins)):
            hist1, bins = np.histogram(
                data1, bins=nbin, density=True, range=[0, 1])[:2]
            self.histograms1[n, :] = \
                np.append(hist1, (np.max(self.nbins) - nbin) * [np.NaN])
            self.bins.append(bins)
            hist2 = np.histogram(
                data2, bins=nbin, density=True, range=[0, 1])[0]
            self.histograms2[n, :] = \
                np.append(hist2, (np.max(self.nbins) - nbin) * [np.NaN])

            # Normalize
            self.histograms1[n, :] /= np.nansum(self.histograms1[n, :])
            self.histograms2[n, :] /= np.nansum(self.histograms2[n, :])

        self.mecdf1 = mecdf(self.histograms1)
        self.mecdf2 = mecdf(self.histograms2)

        self.histogram_distance = hellinger_stat(
            self.histograms1, self.histograms2)

        if verbose:
            import matplotlib.pyplot as p

            p.subplot(2, 2, 1)
            p.title("ECDF 1")
            p.xlabel("Intensities")
            for n in range(len(self.deltas1[:self.cutoff])):
                p.plot((self.bins[n][:-1] + self.bins[n][1:])/2,
                       self.mecdf1[n, :][:self.nbins[n]])
            p.subplot(2, 2, 2)
            p.title("ECDF 2")
            p.xlabel("Intensities")
            for n in range(len(self.deltas2[:self.cutoff])):
                p.plot((self.bins[n][:-1] + self.bins[n][1:])/2,
                       self.mecdf2[n, :][:self.nbins[n]])
            p.subplot(2, 2, 3)
            p.title("PDF 1")
            for n in range(len(self.deltas1[:self.cutoff])):
                bin_width = self.bins[n][1] - self.bins[n][0]
                p.bar((self.bins[n][:-1] + self.bins[n][1:])/2,
                      self.histograms1[n, :][:self.nbins[n]],
                      align="center", width=bin_width, alpha=0.25)
            p.subplot(2, 2, 4)
            p.title("PDF 2")
            for n in range(len(self.deltas2[:self.cutoff])):
                bin_width = self.bins[n][1] - self.bins[n][0]
                p.bar((self.bins[n][:-1] + self.bins[n][1:])/2,
                      self.histograms2[n, :][:self.nbins[n]],
                      align="center", width=bin_width, alpha=0.25)
            p.show()

        return self

    def distance_metric(self, verbose=False):
        '''
        '''

        self.histogram_stat(verbose=verbose)
        self.numfeature_stat(verbose=verbose)

        # Close HDF5 files
        self.file1.close()
        self.file2.close()

        return self


def hellinger_stat(x, y):

    assert x.shape == y.shape

    hellinger = lambda i, j: (
        1 / np.sqrt(2)) * np.sqrt(np.nansum((np.sqrt(i) - np.sqrt(j)) ** 2.))

    if len(x.shape) == 1:
        return hellinger(x, y)
    else:
        dists = np.empty((x.shape[0], 1))
        for n in range(x.shape[0]):
            dists[n, 0] = hellinger(x[n, :], y[n, :])
        return np.mean(dists)


def break_spline(x, y, **kwargs):

    s = UnivariateSpline(x, y, **kwargs)
    knots = s.get_knots()

    if len(knots) > 3:
        print "Many knots"
        knot_expec = -0.8
        posn = np.argmin(knots - knot_expec)
        return knots[posn]  # Return the knot closest to the expected value

    elif len(knots) == 2:
        print "No knots"
        return -0.6  # Set the threshold at the expected

    else:
        return knots[1]