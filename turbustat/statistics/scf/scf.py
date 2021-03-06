# Licensed under an MIT open source license - see LICENSE


import numpy as np


class SCF(object):

    '''
    Computes the Spectral Correlation Function of a data cube
    (Rosolowsky et al, 1999).

    Parameters
    ----------
    cube : numpy.ndarray
        Data cube.
    size : int, optional
        Maximum size roll over which SCF will be calculated.
    '''

    def __init__(self, cube, size=11):
        super(SCF, self).__init__()
        self.cube = cube
        if size % 2 == 0:
            print "Size must be odd. Reducing size to next lowest odd number."
            self.size = size - 1
        else:
            self.size = size

        self.scf_surface = np.zeros((self.size, self.size))

    def compute_scf(self):
        '''
        Compute the SCF up to the given size.
        '''

        dx = np.arange(self.size) - self.size / 2
        dy = np.arange(self.size) - self.size / 2

        for i in dx:
            for j in dy:
                tmp = np.roll(self.cube, i, axis=1)
                tmp = np.roll(tmp, j, axis=2)
                values = np.nansum(((self.cube - tmp) ** 2), axis=0) / \
                    (np.nansum(self.cube ** 2, axis=0) +
                     np.nansum(tmp ** 2, axis=0))

                scf_value = 1. - \
                    np.sqrt(np.nansum(values) / np.sum(np.isfinite(values)))
                self.scf_surface[
                    i + self.size / 2, j + self.size / 2] = scf_value

        return self

    def run(self, verbose=False):
        '''
        Computes the SCF. Necessary to maintain package standards.

        Parameters
        ----------
        verbose : bool, optional
            Enables plotting.

        '''

        self.compute_scf()

        if verbose:
            import matplotlib.pyplot as p

            p.subplot(2, 1, 1)
            p.imshow(self.scf_surface, origin="lower", interpolation="nearest")
            p.colorbar()

            p.subplot(2, 1, 2)
            p.hist(self.scf_surface.ravel())

            p.show()


class SCF_Distance(object):

    '''
    Calculates the distance between two data cubes based on their SCF surfaces.
    The distance is the L2 norm between the surfaces. We weight the surface by
    1/r^2 where r is the distance from the centre.

    Parameters
    ----------
    cube1 : numpy.ndarray
        Data cube.
    cube2 : numpy.ndarray
        Data cube.
    size : int, optional
        Maximum size roll over which SCF will be calculated.
    fiducial_model : SCF
        Computed SCF object. Use to avoid recomputing.
    weighted : bool, optional
        Sets whether to apply the 1/r^2 weighting to the distance.

    '''

    def __init__(self, cube1, cube2, size=11, fiducial_model=None,
                 weighted=True):
        super(SCF_Distance, self).__init__()
        self.cube1 = cube1
        self.cube2 = cube2
        self.size = size
        self.weighted = weighted

        if fiducial_model is not None:
            self.scf1 = fiducial_model
        else:
            self.scf1 = SCF(self.cube1, self.size)
            self.scf1.run()

        self.scf2 = SCF(self.cube2, self.size)
        self.scf2.run()

        self.distance = None

    def distance_metric(self, verbose=False):
        '''
        Compute the distance between the surfaces.

        Parameters
        ----------
        verbose : bool, optional
            Enables plotting.

        '''

        dx = np.arange(self.size) - self.size / 2
        dy = np.arange(self.size) - self.size / 2

        a, b = np.meshgrid(dx, dy)
        if self.weighted:
            # Centre pixel set to 1
            a[np.where(a == 0)] = 1.
            b[np.where(b == 0)] = 1.
            dist_weight = 1 / np.sqrt(a ** 2 + b ** 2)
        else:
            dist_weight = np.ones((self.size, self.size))

        difference = (
            (self.scf1.scf_surface - self.scf2.scf_surface) * dist_weight) ** 2.
        self.distance = np.sqrt(
            np.nansum(difference) / np.sum(np.isfinite(difference)))

        if verbose:
            import matplotlib.pyplot as p

            # print "Distance: %s" % (self.distance)

            p.subplot(1, 3, 1)
            p.imshow(
                self.scf1.scf_surface, origin="lower", interpolation="nearest")
            p.title("SCF1")
            p.colorbar()
            p.subplot(1, 3, 2)
            p.imshow(
                self.scf2.scf_surface, origin="lower", interpolation="nearest")
            p.title("SCF2")
            p.colorbar()
            p.subplot(1, 3, 3)
            p.imshow(difference, origin="lower", interpolation="nearest")
            p.title("Difference")
            p.colorbar()

            p.show()

        return self
