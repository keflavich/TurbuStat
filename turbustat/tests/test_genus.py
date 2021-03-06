# Licensed under an MIT open source license - see LICENSE

'''
Test functions for Genus
'''

from unittest import TestCase

import numpy as np
import numpy.testing as npt

from ..statistics import Genus, GenusDistance
from ._testing_data import \
    dataset1, dataset2, computed_data, computed_distances


class testGenus(TestCase):

    def setUp(self):
        self.dataset1 = dataset1
        self.dataset2 = dataset2

    def test_Genus_method(self):
        self.tester = Genus(dataset1["integrated_intensity"][0],
                            lowdens_thresh=20)
        self.tester.run()

        assert np.allclose(self.tester.genus_stats,
                           computed_data['genus_val'])

    def test_Genus_distance(self):
        self.tester_dist = \
            GenusDistance(dataset1["integrated_intensity"][0],
                          dataset2["integrated_intensity"][0])
        self.tester_dist.distance_metric()
        npt.assert_almost_equal(self.tester_dist.distance,
                                computed_distances['genus_distance'])
