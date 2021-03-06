# Licensed under an MIT open source license - see LICENSE


'''

Implementation of the Delta-Variance Method from Stutzki et al. 1998.

'''

import numpy as np
from scipy.stats import nanmean
from scipy.spatial.distance import euclidean
from astropy.convolution import convolve_fft
from astropy import units as u


class DeltaVariance(object):

    """

    The delta-variance technique as described in Ossenkopf et al. (2008).

    Parameters
    ----------

    img : numpy.ndarray
        The image calculate the delta-variance of.
    header : FITS header
        Image header.
    weights : numpy.ndarray
        Weights to be used.
    diam_ratio : float, optional
        The ratio between the kernel sizes.
    lags : numpy.ndarray or list, optional
        The pixel scales to compute the delta-variance at.

    """

    def __init__(self, img, header, weights, diam_ratio=1.5, lags=None):
        super(DeltaVariance, self).__init__()

        self.img = img
        self.header = header
        self.weights = weights
        self.diam_ratio = diam_ratio

        self.nanflag = False
        if np.isnan(self.img).any():
            self.nanflag = True

        if lags is None:
            try:
                self.ang_size = self.header["CDELT2"] * u.deg
                min_size = (0.1 * u.arcmin) / self.ang_size.to(u.arcmin)
                # Can't be smaller than one pixel, set to 3 to
                # avoid noisy pixels. Can't be bigger than half the image
                #(deals with issue from sim cubes).
                if min_size < 3.0 or min_size > min(self.img.shape) / 2.:
                    min_size = 3.0
            except ValueError:
                print "No CDELT2 in header. Using pixel scales."
                self.ang_size = 1.0 * u.astrophys.pixel
                min_size = 3.0
            self.lags = np.logspace(np.log10(min_size),
                                    np.log10(min(self.img.shape) / 2.), 25)
        else:
            self.lags = lags

        self.convolved_arrays = []
        self.convolved_weights = []
        self.delta_var = np.empty((len(self.lags, )))
        self.delta_var_error = np.empty((2, len(self.lags)))

    def do_convolutions(self):
        for i, lag in enumerate(self.lags):
            core = core_kernel(lag, self.img.shape[0], self.img.shape[1])
            annulus = annulus_kernel(
                lag, self.diam_ratio, self.img.shape[0], self.img.shape[1])

            # Extend to avoid boundary effects from non-periodicity
            pad_weights = np.pad(self.weights, int(lag), padwithzeros)
            pad_img = np.pad(self.img, int(lag), padwithzeros) * pad_weights

            interpolate_nan = False
            if self.nanflag:
                interpolate_nan = True

            img_core = convolve_fft(
                pad_img, core, normalize_kernel=True,
                interpolate_nan=interpolate_nan,
                ignore_edge_zeros=True)
            img_annulus = convolve_fft(
                pad_img, annulus, normalize_kernel=True,
                interpolate_nan=interpolate_nan,
                ignore_edge_zeros=True)
            weights_core = convolve_fft(
                pad_weights, core, normalize_kernel=True,
                interpolate_nan=interpolate_nan,
                ignore_edge_zeros=True)
            weights_annulus = convolve_fft(
                pad_weights, annulus, normalize_kernel=True,
                interpolate_nan=interpolate_nan,
                ignore_edge_zeros=True)

            weights_core[np.where(weights_core == 0)] = np.NaN
            weights_annulus[np.where(weights_annulus == 0)] = np.NaN

            self.convolved_arrays.append(
                (img_core / weights_core) - (img_annulus / weights_annulus))
            self.convolved_weights.append(weights_core * weights_annulus)

        return self

    def compute_deltavar(self, bootstrap=True, nsamples=100, alpha=0.05):

        for i, (convolved_array, convolved_weight) in \
         enumerate(zip(self.convolved_arrays, self.convolved_weights)):

            delta_var_val = _delvar(convolved_array, convolved_weight)

            # bootstrap to find an error
            if bootstrap:
                bootstrap_delvar = np.empty((nsamples, ))
                for n in range(nsamples):
                    resample = bootstrap_resample(convolved_array)
                    bootstrap_delvar[n] = _delvar(resample, convolved_weight)

                stat = np.sort(bootstrap_delvar)
                error = (stat[int((alpha/2.0)*nsamples)],
                         stat[int((1-alpha/2.0)*nsamples)])
            else:
                error = (0.0, 0.0)

            self.delta_var[i] = delta_var_val
            self.delta_var_error[:, i] = error

        return self

    def run(self, bootstrap=False, verbose=False, ang_units=True):

        self.do_convolutions()
        self.compute_deltavar(bootstrap=bootstrap)

        if ang_units:
            self.lags *= self.ang_size

        if verbose:
            import matplotlib.pyplot as p
            ax = p.subplot(111)
            ax.set_xscale("log", nonposx="clip")
            ax.set_yscale("log", nonposx="clip")
            error_bar = [np.abs(self.delta_var -
                                self.delta_var_error[0, :]),
                         np.abs(self.delta_var +
                                self.delta_var_error[1, :])]
            p.errorbar(self.lags, self.delta_var, yerr=error_bar, fmt="bD-")
            ax.grid(True)
            ax.set_xlabel("Lag (arcmin)")
            ax.set_ylabel(r"$\sigma^{2}_{\Delta}$")
            p.show()

        return self


def core_kernel(lag, x_size, y_size):
    '''
    Core Kernel for convolution.

    Parameters
    ----------

    lag : int
        Size of the lag. Set the kernel size.
    x_size : int
        Grid size to use in the x direction
    y_size_size : int
        Grid size to use in the y_size direction

    Returns
    -------

    kernel : numpy.ndarray
        Normalized kernel.
    '''

    x, y = np.meshgrid(np.arange(-x_size / 2, x_size / 2 + 1, 1),
                       np.arange(-y_size / 2, y_size / 2 + 1, 1))
    kernel = ((4 / np.pi * lag)) * \
        np.exp(-(x ** 2. + y ** 2.) / (lag / 2.) ** 2.)

    return kernel / np.sum(kernel)


def annulus_kernel(lag, diam_ratio, x_size, y_size):
    '''

    Annulus Kernel for convolution.

    Parameters
    ----------
    lag : int
        Size of the lag. Set the kernel size.
    diam_ratio : float
                 Ratio between kernel diameters.
    x_size : int
        Grid size to use in the x direction
    y_size_size : int
        Grid size to use in the y_size direction

    Returns
    -------

    kernel : numpy.ndarray
        Normalized kernel.
    '''

    x, y = np.meshgrid(np.arange(-x_size / 2, x_size / 2 + 1, 1),
                       np.arange(-y_size / 2, y_size / 2 + 1, 1))

    inner = np.exp(-(x ** 2. + y ** 2.) / (lag / 2.) ** 2.)
    outer = np.exp(-(x ** 2. + y ** 2.) / (diam_ratio * lag / 2.) ** 2.)

    kernel = 4 / (np.pi * lag * (diam_ratio ** 2. - 1)) * (outer - inner)

    return kernel / np.sum(kernel)


def padwithzeros(vector, pad_width, iaxis, kwargs):
    '''
    Pad array with zeros.
    '''
    vector[:pad_width[0]] = 0
    vector[-pad_width[1]:] = 0
    return vector


class DeltaVariance_Distance(object):

    """
    Compares 2 datasets using delta-variance. The distance between them is
    given by the Euclidean distance between the curves weighted by the
    bootstrapped errors.

    Parameters
    ----------

    dataset1 : FITS hdu
        Contains the data and header for one dataset.
    dataset2 : FITS hdu
        See above.
    weights1 : numpy.ndarray
        Weights for dataset1.
    weights2 : numpy.ndarray
        See above.
    diam_ratio : float, optional
        The ratio between the kernel sizes.
    lags : numpy.ndarray or list, optional
        The pixel scales to compute the delta-variance at.
    fiducial_model : DeltaVariance
        A computed DeltaVariance model. Used to avoid recomputing.
    """

    def __init__(self, dataset1, weights1, dataset2, weights2, diam_ratio=1.5,
                 lags=None, fiducial_model=None):
        super(DeltaVariance_Distance, self).__init__()

        if fiducial_model is not None:
            self.delvar1 = fiducial_model
        else:
            self.delvar1 = DeltaVariance(dataset1[0], dataset1[1], weights1,
                                         diam_ratio=diam_ratio, lags=lags)
            self.delvar1.run()

        self.delvar2 = DeltaVariance(dataset2[0], dataset2[1], weights2,
                                     diam_ratio=diam_ratio, lags=lags)
        self.delvar2.run()

        self.distance = None

    def distance_metric(self, verbose=False):
        '''
        Applies the Euclidean distance to the delta-variance curves.

        Parameters
        ----------
        verbose : bool, optional
            Enables plotting.
        '''

        errors1 = np.abs(self.delvar1.delta_var_error[1, :] -
                         self.delvar1.delta_var_error[0, :])
        errors2 = np.abs(self.delvar2.delta_var_error[1, :] -
                         self.delvar2.delta_var_error[0, :])

        self.distance = np.linalg.norm(np.log10(self.delvar1.delta_var) -
                                  np.log10(self.delvar2.delta_var))

        if verbose:
            import matplotlib.pyplot as p
            ax = p.subplot(111)
            ax.set_xscale("log", nonposx="clip")
            ax.set_yscale("log", nonposx="clip")
            error_bar1 = [np.abs(self.delvar1.delta_var -
                                 self.delvar1.delta_var_error[0, :]),
                          np.abs(self.delvar1.delta_var +
                                 self.delvar1.delta_var_error[1, :])]
            p.errorbar(self.delvar1.lags, self.delvar1.delta_var,
                       yerr=error_bar1, fmt="bD-",
                       label="Delta Var 1")
            error_bar2 = [np.abs(self.delvar2.delta_var -
                                 self.delvar2.delta_var_error[0, :]),
                          np.abs(self.delvar2.delta_var +
                                 self.delvar2.delta_var_error[1, :])]
            p.errorbar(self.delvar2.lags, self.delvar2.delta_var,
                       yerr=error_bar2, fmt="gD-",
                       label="Delta Var 2")
            ax.legend(loc='best')
            ax.grid(True)
            ax.set_xlabel("Lag (arcmin)")
            ax.set_ylabel(r"$\sigma^{2}_{\Delta}$")
            p.show()

        return self


def _delvar(array, weight):
    '''
    Computes the delta variance of the given array.
    '''
    avg_value = nanmean(array, axis=None)

    val = np.nansum((array - avg_value) ** 2. * weight) /\
        np.nansum(weight)

    return val


def bootstrap_resample(X, n=None):
    """
    Code based on: http://nbviewer.ipython.org/gist/aflaxman/6871948
    Bootstrap resample an array_like
    Parameters
    ----------
    X : array_like
      data to resample
    n : int, optional
      length of resampled array, equal to len(X) if n==None

    Returns
    -------
    returns X_resamples
    """
    if n is None:
        n = len(X)

    resample_i = np.floor(np.random.rand(n)*len(X)).astype(int)
    X_resample = X[resample_i]
    return X_resample
