#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2020 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2020 The MITRE Corporation                                      #
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

import dataclasses
import operator
import sys
import typing
from typing import Callable, Mapping, NamedTuple, Optional, Sequence, Tuple, Union, TypeVar

import cv2
import numpy as np

import mpf_component_api as mpf


T = TypeVar('T')

def get_property(
        properties: Mapping[str, str],
        key: str,
        default_value: T,
        prop_type: Optional[Callable[[str], T]] = None) -> T:
    if key not in properties:
        return default_value

    if prop_type is None:
        prop_type = type(default_value)

    value = properties[key]
    if prop_type is bool:
        return typing.cast(T, value.upper() == 'TRUE')

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


def normalize_angle(angle: float) -> float:
    if 0 <= angle < 360:
        return angle
    angle %= 360
    if angle >= 0:
        return angle
    return 360 + angle

def rotation_angles_equal(a1: float, a2: float, epsilon=0.1) -> bool:
    a1 = normalize_angle(a1)
    a2 = normalize_angle(a2)
    if abs(a1 - a2) < epsilon:
        return True
    else:
        a1_dist = min(a1, 360 - a1)
        a2_dist = min(a2, 360 - a2)
        return (a1_dist + a2_dist) < epsilon


IntOrFloat = Union[int, float]


class Point(NamedTuple):
    """
    The C++ OpenCV has a cv::Point class, but the Python version uses 2-tuples to represent points.
    Since NamedTuple is a subclass of tuple, this class can be used as a parameter in OpenCV functions
    that expect a point.
    """
    x: IntOrFloat
    y: IntOrFloat


_PointLike = Union[Point, Tuple[IntOrFloat, IntOrFloat], Sequence[IntOrFloat]]


class Size(NamedTuple):
    """
    The C++ OpenCV has a cv::Size class, but the Python version uses 2-tuples to represent sizes.
    Since NamedTuple is a subclass of tuple, this class can be used as a parameter in OpenCV functions
    that expect a size.
    """
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
    """
    The C++ OpenCV has a cv::Rect class, but the Python version uses 4-tuples to represent rectangles.
    Since NamedTuple is a subclass of tuple, this class can be used as a parameter in OpenCV functions
    that expect a rectangle.
    """
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


@dataclasses.dataclass
class RotatedRect:
    """
    Represents a rectangle that may or may not be axis aligned.
    The algorithm to "draw" the rectangle, is as follows:
    1. Draw the rectangle ignoring rotation and flip.
    2. Stick a pin in the top left corner of the rectangle because the top left doesn't move,
       but the rest of the rectangle may be moving.
    3. Rotate the rectangle counter-clockwise the given number of degrees around its top left corner.
    4. If the rectangle is flipped, flip horizontally around the top left corner.
    """
    x: float
    y: float
    width: float
    height: float
    rotation: float
    flip: bool

    @property
    def corners(self) -> Tuple[Point, Point, Point, Point]:
        has_rotation = not rotation_angles_equal(self.rotation, 0)
        if not has_rotation and not self.flip:
            return (
                Point(self.x, self.y),
                Point(self.x + self.width - 1, self.y),
                Point(self.x + self.width - 1, self.y + self.height - 1),
                Point(self.x, self.y + self.height - 1),
            )

        xform_mat = self._get_transform_mat()

        tr_x = self.x + self.width - 1
        br_y = self.y + self.height - 1
        corner_mat = (
            (tr_x, tr_x, self.x),
            (self.y, br_y, br_y),
            (1, 1, 1)
        )

        xformed_corners = np.matmul(xform_mat, corner_mat)
        return (
            Point(self.x, self.y),
            Point(xformed_corners[0, 0], xformed_corners[1, 0]),
            Point(xformed_corners[0, 1], xformed_corners[1, 1]),
            Point(xformed_corners[0, 2], xformed_corners[1, 2])
        )

    def _get_transform_mat(self):
        has_rotation = not rotation_angles_equal(self.rotation, 0)
        assert has_rotation or self.flip

        if has_rotation and not self.flip:
            # This case is handled separately because it is the most common case and we can avoid some work.
            return cv2.getRotationMatrix2D((self.x, self.y), self.rotation, 1)

        # At this point, we know we need to flip since we already checked
        # !hasRotation && !flip before calling this function.

        # The last column of flip_mat makes it so the flip is around the top left coordinate, rather than the y-axis.
        # 2*self.x is used because the point is initially x units away from the y-axis. After flipping around the
        # y-axis, the mirrored point is also x units away from the y-axis, except in the opposite direction.
        # This means there is a total distance of 2*self.x between a point and its mirrored point.
        flip_mat = (
            (-1, 0, 2 * self.x),
            (0, 1, 0)
        )
        if not has_rotation:
            return flip_mat

        rotation_mat2d = cv2.getRotationMatrix2D((self.x, self.y), self.rotation, 1)
        # Add a row to the rotation matrix so it has the size required to multiply with the flip matrix.
        full_rotation_mat = np.vstack((rotation_mat2d, (0, 0, 1)))

        # Transform are applied from right to left, so rotation will occur before flipping.
        return np.matmul(flip_mat, full_rotation_mat)


    @property
    def bounding_rect(self) -> Rect:
        corners = np.asarray(self.corners)
        return Rect.from_corners(np.min(corners, axis=0), np.max(corners, axis=0) + 1)
