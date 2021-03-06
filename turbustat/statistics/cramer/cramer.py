# Licensed under an MIT open source license - see LICENSE


'''

Implementation of the Cramer Statistic

'''

import numpy as np
from sklearn.metrics.pairwise import pairwise_distances


class Cramer_Distance(object):
    """
    Compute the Cramer distance between two data cubes. The data cubes
    are flattened spatially to give 2D objects. We clip off empty channels
    and keep only the top quartile in the remaining channels.

    Parameters
    ----------

    cube1 : numpy.ndarray
        First cube to compare.
    cube2 : numpy.ndarray
        Second cube to compare.
    noise_value1 : float, optional
        Noise level in the first cube.
    noise_value2 : float, optional
        Noise level in the second cube.
    data_format : str, optional
        Method to arange cube into 2D. Only 'intensity' is currently
        implemented.
    """

    def __init__(self, cube1, cube2, noise_value1=0.1,
                 noise_value2=0.1, data_format="intensity"):
        super(Cramer_Distance, self).__init__()
        self.cube1 = cube1
        self.cube2 = cube2
        self.data_format = data_format

        self.noise_value1 = noise_value1
        self.noise_value2 = noise_value2

        self.data_matrix1 = None
        self.data_matrix2 = None
        self.distance = None

    def format_data(self, data_format=None):
        '''
        Rearrange data into a 2D object using the given format.
        '''

        if data_format is not None:
            self.data_format = data_format

        if self.data_format == "spectra":
            raise NotImplementedError("")

        elif self.data_format == "intensity":
            self.data_matrix1 = intensity_data(self.cube1,
                                               noise_lim=self.noise_value1)
            self.data_matrix2 = intensity_data(self.cube2,
                                               noise_lim=self.noise_value2)

        else:
            raise NameError(
                "data_format must be either 'spectra' or 'intensity'.")

        return self

    def cramer_statistic(self, n_jobs=1):
        '''
        Applies the Cramer Statistic to the datasets.

        Parameters
        ----------

        n_jobs : int, optional
            Sets the number of cores to use to calculate
            pairwise distances
        '''
        # Adjust what we call n,m based on the larger dimension.
        # Then the looping below is valid.
        if self.data_matrix1.shape[0] >= self.data_matrix2.shape[0]:
            m = self.data_matrix1.shape[0]
            n = self.data_matrix2.shape[0]
            larger = self.data_matrix1
            smaller = self.data_matrix2
        else:
            n = self.data_matrix1.shape[0]
            m = self.data_matrix2.shape[0]
            larger = self.data_matrix2
            smaller = self.data_matrix1

        pairdist11 = pairwise_distances(
            larger, metric="euclidean", n_jobs=n_jobs)
        pairdist22 = pairwise_distances(
            smaller, metric="euclidean", n_jobs=n_jobs)
        pairdist12 = pairwise_distances(
            larger, smaller,
            metric="euclidean", n_jobs=n_jobs)

        term1 = 0.0
        term2 = 0.0
        term3 = 0.0
        for i in range(m):
            for j in range(n):
                term1 += pairdist12[i, j]
            for ii in range(m):
                term2 += pairdist11[i, ii]

            if i < n:
                for jj in range(n):
                    term3 += pairdist22[i, jj]

        m, n = float(m), float(n)

        term1 *= (1 / (m * n))
        term2 *= (1 / (2 * m ** 2.))
        term3 *= (1 / (2 * n ** 2.))

        self.distance = (m * n / (m + n)) * (term1 - term2 - term3)

        return self

    def distance_metric(self, n_jobs=1):
        '''

        This serves as a simple wrapper in order to remain with the coding
        convention used throughout the rest of this project.

        '''

        self.format_data()
        self.cramer_statistic(n_jobs=n_jobs)

        return self


def intensity_data(cube, p=0.1, noise_lim=0.1):
    '''
    Clips off channels below the given noise limit and keep the
    upper percentile specified.

    Parameters
    ----------
    cube : numpy.ndarray
        Data cube.
    p : float, optional
        Sets the fraction of data to keep in each channel.
    noise_lim : float, optional
        The noise limit used to reject channels in the cube.

    Returns
    -------

    intensity_vecs : numpy.ndarray
        2D dataset of size (# channels, p * cube.shape[1] * cube.shape[2]).
    '''
    vec_length = int(round(p * cube.shape[1] * cube.shape[2]))
    intensity_vecs = np.empty((cube.shape[0], vec_length))

    delete_channels = []

    for dv in range(cube.shape[0]):
        vec_vec = cube[dv, :, :]
        # Remove nans from the slice
        vel_vec = vec_vec[np.isfinite(vec_vec)]
        # Apply noise limit
        vel_vec = vel_vec[vel_vec > noise_lim]
        vel_vec.sort()
        if len(vel_vec) < vec_length:
            diff = vec_length - len(vel_vec)
            vel_vec = np.append(vel_vec, [0.0] * diff)
        else:
            vel_vec = vel_vec[:vec_length]

        # Return the normalized, shortened vector
        maxval = np.max(vel_vec)
        if maxval != 0.0:
            intensity_vecs[dv, :] = vel_vec / maxval
        else:
            delete_channels.append(dv)
    # Remove channels
    intensity_vecs = np.delete(intensity_vecs, delete_channels, axis=0)

    return intensity_vecs
