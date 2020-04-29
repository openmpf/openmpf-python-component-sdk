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

import operator
import sys
from typing import NamedTuple, Sequence, Union, Tuple

import numpy as np

import mpf_component_api as mpf



def get_property(properties, key, default_value, prop_type=None):
    if key not in properties:
        return default_value

    if prop_type is None:
        prop_type = type(default_value)

    value = properties[key]
    if prop_type is bool:
        return value.upper() == 'TRUE'

    try:
        return prop_type(value)
    except (TypeError, ValueError) as err:
        print('Failed to convert the "%s" key with value "%s" to %s due to: %s' % (key, value, prop_type, err),
              file=sys.stderr)
        return default_value



def dict_items_ordered_by_key(dict_, key=None, reverse=False):
    ordered_keys = sorted(dict_, key=key, reverse=reverse)
    return ((k, dict_[k]) for k in ordered_keys)


def dict_values_ordered_by_key(dict_):
    return (v for k, v in dict_items_ordered_by_key(dict_))



def normalize_angle(angle):
    if 0 <= angle < 360:
        return angle
    angle %= 360
    if angle >= 0:
        return angle
    return 360 + angle

def rotation_angles_equal(a1, a2, epsilon=0.1):
    return abs(normalize_angle(a1) - normalize_angle(a2)) < epsilon


IntOrFloat = Union[int, float]

class Point(NamedTuple):
    x: IntOrFloat
    y: IntOrFloat


_PointLike = Union[Point, Tuple[IntOrFloat, IntOrFloat], Sequence[IntOrFloat]]


class Size(NamedTuple):
    width: IntOrFloat
    height: IntOrFloat

    @property
    def area(self) -> IntOrFloat:
        return self.width * self.height

    @staticmethod
    def from_frame(frame: np.ndarray) -> 'Size':
        height, width, _ = frame.shape
        return Size(width, height)

    @staticmethod
    def as_size(obj: '_SizeLike') -> 'Size':
        return obj if isinstance(obj, Size) else Size(*obj)


_SizeLike = Union[Size, Tuple[IntOrFloat, IntOrFloat], Sequence[IntOrFloat]]


def element_wise_op(op, obj1, obj2, target_type=None):
    if target_type is None:
        target_type = type(obj1)
    return target_type(*(op(v1, v2) for v1, v2 in zip(obj1, obj2)))


class Rect(NamedTuple):
    x: IntOrFloat
    y: IntOrFloat
    width: IntOrFloat
    height: IntOrFloat

    @property
    def br(self) -> Point:
        return Point(self.x + self.width, self.y + self.height)

    @property
    def tl(self) -> Point:
        return Point(self.x, self.y)

    @property
    def empty(self) -> bool:
        return self.area <= 0

    @property
    def area(self) -> IntOrFloat:
        return self.width * self.height

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)

    def union(self, other: '_RectLike') -> 'Rect':
        other = Rect.__rectify(other)

        if self.empty:
            return other
        elif other.empty:
            return self
        else:
            return Rect.from_corners(
                element_wise_op(min, self.tl, other.tl),
                element_wise_op(max, self.br, other.br))


    def intersection(self, other: '_RectLike') -> 'Rect':
        other = Rect.__rectify(other)

        top_left = element_wise_op(max, self.tl, other.tl)
        bottom_right = element_wise_op(min, self.br, other.br)

        if top_left.x >= bottom_right.x or top_left.y >= bottom_right.y:
            return Rect(0, 0, 0, 0)
        return Rect.from_corners(top_left, bottom_right)


    @staticmethod
    def from_corners(point1: _PointLike, point2: _PointLike) -> 'Rect':
        top_left = element_wise_op(min, point1, point2, Point)
        bottom_right = element_wise_op(max, point1, point2, Point)
        dist = element_wise_op(operator.sub, bottom_right, top_left, Size)
        return Rect.from_corner_and_size(top_left, dist)

    @staticmethod
    def from_corner_and_size(top_left_point: _PointLike, size: _SizeLike):
        return Rect(top_left_point[0], top_left_point[1], size[0], size[1])

    @staticmethod
    def from_image_location(image_location: mpf.ImageLocation):
        return Rect(image_location.x_left_upper, image_location.y_left_upper, image_location.width,
                    image_location.height)

    @staticmethod
    def __rectify(obj) -> 'Rect':
        if isinstance(obj, Rect):
            return obj
        if len(obj) == 4:
            return Rect(*obj)
        if len(obj) == 2:
            obj1 = obj[0]
            obj2 = obj[1]
            if isinstance(obj2, Point):
                return Rect.from_corners(obj1, obj2)
            if isinstance(obj2, Size):
                return Rect.from_corner_and_size(obj1, obj2)
        raise TypeError('Could not convert argument %s to Rect.' % (obj,))


_RectLike = Union[
    Rect,
    Tuple[IntOrFloat, IntOrFloat, IntOrFloat, IntOrFloat],
    Sequence[IntOrFloat],
    Tuple[_PointLike, Size],
    Tuple[_PointLike, Point]
]
