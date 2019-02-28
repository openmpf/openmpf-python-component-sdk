#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2019 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2019 The MITRE Corporation                                      #
#                                                                           #
# Licensed under the Apache License, Version 2.0 (the "License");           #
# you may not use this file except in compliance with the License.          #
# You may obtain a copy of the License at                                   #
#                                                                           #
#    http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                           #
# Unless required by applicable law or agreed to in writing, software       #
# distributed under the License is distributed on an "AS IS" BASIS,         #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
# See the License for the specific language governing permissions and       #
# limitations under the License.                                            #
#############################################################################

from __future__ import division, print_function

import test_util
test_util.add_local_component_libs_to_sys_path()
import unittest
import mpf_component_util as mpf_util


class TestRect(unittest.TestCase):
    def test_rect_info_methods(self):
        test_rect = mpf_util.Rect(2, 3, 4, 5)

        self.assertEqual(20, test_rect.area)
        self.assertFalse(test_rect.empty)
        self.assertEqual(mpf_util.Point(2, 3), test_rect.tl)
        self.assertEqual(mpf_util.Point(6, 8), test_rect.br)
        self.assertEqual(mpf_util.Size(4, 5), test_rect.size)


    def test_rect_creation(self):
        test_rect = mpf_util.Rect(2, 3, 4, 5)
        self.assertEqual(test_rect, (2, 3, 4, 5))

        self.assertEqual(test_rect, mpf_util.Rect.from_corner_and_size((2, 3), (4, 5)))
        self.assertEqual(test_rect, mpf_util.Rect.from_corner_and_size(mpf_util.Point(2, 3), mpf_util.Size(4, 5)))
        self.assertEqual(test_rect, mpf_util.Rect.from_corner_and_size(mpf_util.Point(2, 3), (4, 5)))

        self.assertEqual(test_rect, mpf_util.Rect.from_corners((2, 3), (6, 8)))
        self.assertEqual(test_rect, mpf_util.Rect.from_corners(mpf_util.Point(2, 3), mpf_util.Point(6, 8)))


    def test_rect_union(self):
        rect1 = mpf_util.Rect(0, 0, 8, 10)
        rect2 = mpf_util.Rect(2, 2, 4, 3)
        union = rect1.union(rect2)
        self.assertEqual(union, rect2.union(rect1))
        # rect1 encloses rect2
        self.assertEqual(rect1, union)

        rect1 = mpf_util.Rect(2, 6, 5, 10)
        rect2 = mpf_util.Rect(4, 3, 6, 9)
        union = rect1.union(rect2)
        self.assertEqual(union, rect2.union(rect1))
        self.assertEqual((2, 3, 8, 13), union)

        rect1 = mpf_util.Rect(1, 3, 8, 4)
        rect2_args = (6, 5, 9, 5)
        union = rect1.union(rect2_args)
        self.assertEqual(union, mpf_util.Rect(*rect2_args).union(rect1))
        self.assertEqual((1, 3, 14, 7), union)

        # Rects with no overlap
        rect1 = mpf_util.Rect(0, 0, 5, 5)
        rect2 = mpf_util.Rect(8, 8, 4, 4)
        union = rect1.union(rect2)
        self.assertEqual(union, rect2.union(rect1))
        self.assertEqual((0, 0, 12, 12), union)

        rect1 = mpf_util.Rect(0, 0, 5, 5)
        rect2 = mpf_util.Rect(0, 0, 5, 5)
        union = rect1.union(rect2)
        self.assertEqual(union, rect2.union(rect1))
        self.assertEqual(union, rect1)



    def test_rect_intersection(self):
        rect1 = mpf_util.Rect(0, 0, 8, 10)
        rect2 = mpf_util.Rect(2, 2, 4, 3)
        intersection = rect1.intersection(rect2)
        self.assertEqual(intersection, rect2.intersection(rect1))
        # rect1 encloses rect2
        self.assertEqual(rect2, intersection)

        rect1 = mpf_util.Rect(2, 6, 5, 10)
        rect2_args = (mpf_util.Point(4, 3), mpf_util.Point(10, 12))
        intersection = rect1.intersection(rect2_args)
        self.assertEqual(intersection, mpf_util.Rect.from_corners(*rect2_args).intersection(rect1))
        self.assertEqual((4, 6, 3, 6), intersection)

        rect1 = mpf_util.Rect(1, 3, 8, 4)
        rect2_args = ((6, 5), mpf_util.Size(9, 5))
        intersection = rect1.intersection(rect2_args)
        self.assertEqual(intersection, mpf_util.Rect.from_corner_and_size(*rect2_args).intersection(rect1))
        self.assertEqual((6, 5, 3, 2), intersection)

        # Rects with no overlap
        rect1 = mpf_util.Rect(0, 0, 5, 5)
        rect2 = mpf_util.Rect(8, 8, 4, 4)
        intersection = rect1.intersection(rect2)
        self.assertEqual(intersection, rect2.intersection(rect1))
        self.assertEqual((0, 0, 0, 0), intersection)

        rect1 = mpf_util.Rect(0, 0, 5, 5)
        rect2 = mpf_util.Rect(0, 0, 5, 5)
        intersection = rect1.intersection(rect2)
        self.assertEqual(intersection, rect2.intersection(rect1))
        self.assertEqual(intersection, rect1)

