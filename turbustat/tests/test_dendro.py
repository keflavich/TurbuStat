# Licensed under an MIT open source license - see LICENSE


'''
Tests for Dendrogram statistics
'''

from unittest import TestCase

import numpy as np
import numpy.testing as npt

from ..statistics import Dendrogram_Stats, DendroDistance
from ._testing_data import \
    dataset1, dataset2, computed_data, computed_distances


class testDendrograms(TestCase):

    def setUp(self):
        self.min_deltas = np.append(np.logspace(-1.5, -0.7, 8),
                                    np.logspace(-0.6, -0.35, 10))

    def test_DendroStat(self):

        self.tester = Dendrogram_Stats(dataset1["cube"][0],
                                       min_deltas=self.min_deltas)
        self.tester.run()

        assert np.allclose(self.tester.numfeatures,
                           computed_data["dendrogram_val"])

    def test_DendroDistance(self):

        self.tester_dist = \
            DendroDistance(dataset1["cube"][0],
                           dataset2["cube"][0],
                           min_deltas=self.min_deltas).distance_metric()

        npt.assert_almost_equal(self.tester_dist.histogram_distance,
                                computed_distances["dendrohist_distance"])
        npt.assert_almost_equal(self.tester_dist.num_distance,
                                computed_distances["dendronum_distance"])