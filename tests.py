# coding: utf-8

import unittest

from .tests.tests_area import multipolygon_with_holes


class TestArea(unittest.TestCase):
    def test_multipolygon_with_holes(self):
        area = multipolygon_with_holes()
        coord = area.xy
        self.assertEqual(len(coord), 2)
        self.assertEqual(len(coord[0]), 1)
        # self.assertEqual(len(coord[1]), 2)


if __name__ == '__main__':
    unittest.main()
