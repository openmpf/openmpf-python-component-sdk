#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2023 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2023 The MITRE Corporation                                      #
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

from __future__ import annotations

import functools
from typing import Sequence, Iterable, Tuple

import cv2
import numpy as np

import mpf_component_api as mpf

from .frame_transformer import BaseDecoratedFrameTransformer, IFrameTransformer
from .. import utils
from .search_region import SearchRegion


class AffineFrameTransformer(BaseDecoratedFrameTransformer):
    def __init__(self,
                 regions: Sequence[utils.RotatedRect],
                 frame_rotation: float,
                 frame_flip: bool,
                 fill_color: Tuple[int, int, int],
                 search_region: SearchRegion,
                 inner_transform: IFrameTransformer):
        super().__init__(inner_transform)
        self.__transform = _AffineTransformation(regions, frame_rotation, frame_flip, fill_color,
                                                 search_region)

    @staticmethod
    def search_region_on_rotated_frame(rotation: float, flip: bool,
                                       fill_color: Tuple[int, int, int],
                                       search_region: SearchRegion,
                                       inner_transform: IFrameTransformer
                                       ) -> 'AffineFrameTransformer':
        return AffineFrameTransformer(
            _full_frame(inner_transform.get_frame_size(0)),
            rotation, flip, fill_color, search_region, inner_transform)

    @staticmethod
    def rotate_full_frame(rotation: float, flip: bool, fill_color: Tuple[int, int, int],
                          inner_transform: IFrameTransformer) -> 'AffineFrameTransformer':
        return AffineFrameTransformer(
            _full_frame(inner_transform.get_frame_size(0)),
            rotation, flip, fill_color, SearchRegion(), inner_transform)

    @staticmethod
    def rotated_superset_region(regions: Sequence[utils.RotatedRect], frame_rotation: float,
                                frame_flip: bool, fill_color: Tuple[int, int, int],
                                inner_transform: IFrameTransformer) -> 'AffineFrameTransformer':
        return AffineFrameTransformer(regions, frame_rotation, frame_flip, fill_color,
                                      SearchRegion(), inner_transform)

    def _do_frame_transform(self, frame, frame_index):
        return self.__transform.apply(frame)

    def _do_reverse_transform(self, image_location, frame_index):
        self.__transform.apply_reverse(image_location)

    def get_frame_size(self, frame_index):
        return self.__transform.get_region_size()



class FeedForwardExactRegionAffineTransformer(BaseDecoratedFrameTransformer):
    def __init__(self, regions: Iterable[utils.RotatedRect], fill_color: Tuple[int, int, int],
                 inner_transform: IFrameTransformer):
        super().__init__(inner_transform)
        self.__frame_transforms = [self.__create_transformation(r, fill_color) for r in regions]

    def _do_frame_transform(self, frame, frame_index):
        return self.__get_transform(frame_index).apply(frame)

    def _do_reverse_transform(self, image_location, frame_index):
        self.__get_transform(frame_index).apply_reverse(image_location)

    def get_frame_size(self, frame_index):
        return self.__get_transform(frame_index).get_region_size()

    def __get_transform(self, frame_index):
        try:
            return self.__frame_transforms[frame_index]
        except IndexError:
            raise IndexError(
                'Attempted to get transformation for frame: {}, but there are only {} entries in the feed forward track'
                .format(frame_index, len(self.__frame_transforms)))

    @staticmethod
    def __create_transformation(region: utils.RotatedRect,
                                fill_color: Tuple[int, int, int]) -> '_AffineTransformation':
        frame_rotation = 360 - region.rotation if region.flip else region.rotation
        return _AffineTransformation((region,), frame_rotation, region.flip, fill_color,
                                     SearchRegion())



def _full_frame(frame_size: utils.Size) -> Sequence[utils.RotatedRect]:
    return (utils.RotatedRect(0, 0, frame_size.width, frame_size.height, 0, False),)


class _AffineTransformation(object):
    def __init__(self,
                 pre_transform_regions: Sequence[utils.RotatedRect],
                 frame_rotation_degrees: float,
                 flip: bool, fill_color: Tuple[int, int, int],
                 post_transform_search_region: SearchRegion):
        if len(pre_transform_regions) == 0:
            raise IndexError('The "preTransformRegions" parameter must contain at least one element, but it was empty')

        self.__rotation_degrees = frame_rotation_degrees
        self.__flip = flip
        self.__fill_color = fill_color

        # Rotating an image around the origin will move some or all of the pixels out of the frame.
        rotation_mat = _IndividualXForms.rotation(360 - frame_rotation_degrees)
        # Use the rotation matrix to figure out where the pixels we are looking for ended up.
        mapped_bounding_rect = self.__get_mapped_bounding_rect(pre_transform_regions, rotation_mat)
        # Shift the pixels we are looking for back in to the frame.
        move_roi_to_origin = _IndividualXForms.translation(-mapped_bounding_rect.x, -mapped_bounding_rect.y)

        # The search region is generally specified by a human, so for convenience the coordinates are relative to
        # the correctly oriented image.
        # searchRegionRect will either be the same as mappedBoundingRect or be contained within mappedBoundingRect.
        search_region_rect = post_transform_search_region.get_rect(mapped_bounding_rect.size)
        self.__region_size: utils.Size[int] = search_region_rect.size
        # When searchRegionRect is smaller than mappedBoundingRect, we need to move the searchRegionRect
        # to the origin. This slides the pixels outside of the search region off of the frame.
        move_search_region_to_origin = _IndividualXForms.translation(-search_region_rect.x, -search_region_rect.y)

        if flip:
            #          -x     x=0     +x
            # initial: [     ] | [ a b ]
            # flipped: [ b a ] | [     ]
            # shift:   [     ] | [ b a ]
            flip_mat = _IndividualXForms.horizontal_flip()
            flip_shift_correction = _IndividualXForms.translation(mapped_bounding_rect.width - 1, 0)
            # Transformations are applied from right to left, so rotation occurs first.
            combined_transform = functools.reduce(
                np.matmul,
                (move_search_region_to_origin, flip_shift_correction, flip_mat, move_roi_to_origin, rotation_mat))
        else:
            # Transformations are applied from right to left, so rotation occurs first.
            combined_transform = functools.reduce(
                np.matmul,
                (move_search_region_to_origin, move_roi_to_origin, rotation_mat))

        # When combining transformations the 3d version must be used,
        # but when mapping 2d points the last row of the matrix can be dropped.
        combined_2d_transform = combined_transform[:2, :3]
        self.__reverse_transformation_matrix = cv2.invertAffineTransform(combined_2d_transform)


    def apply(self, frame: np.ndarray) -> np.ndarray:
        # From cv::warpAffine docs:
        # The function warpAffine transforms the source image using the specified matrix when the flag
        # WARP_INVERSE_MAP is set. Otherwise, the transformation is first inverted with cv::invertAffineTransform.
        # From OpenCV's Geometric Image Transformations module documentation:
        # To avoid sampling artifacts, the mapping is done in the reverse order, from destination to the source.

        # Using INTER_CUBIC, because according to
        # https://en.wikipedia.org/wiki/Affine_transformation#Image_transformation
        # "This transform relocates pixels requiring intensity interpolation to approximate the value of moved pixels,
        # bicubic interpolation is the standard for image transformations in image processing applications."
        return cv2.warpAffine(frame, self.__reverse_transformation_matrix, self.__region_size,  # type: ignore
                              flags=cv2.WARP_INVERSE_MAP | cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=self.__fill_color)


    def apply_reverse(self, image_location: mpf.ImageLocation) -> None:
        top_left = np.array((image_location.x_left_upper, image_location.y_left_upper, 1.0), dtype=float)
        new_top_left = np.matmul(self.__reverse_transformation_matrix, top_left)

        image_location.x_left_upper = int(round(new_top_left[0]))
        image_location.y_left_upper = int(round(new_top_left[1]))

        if not utils.rotation_angles_equal(self.__rotation_degrees, 0):
            existing_rotation = utils.get_property(image_location.detection_properties, 'ROTATION', 0.0)
            rotation_adjustment_amount = 360 - self.__rotation_degrees if self.__flip else self.__rotation_degrees
            new_rotation = utils.normalize_angle(existing_rotation + rotation_adjustment_amount)
            image_location.detection_properties['ROTATION'] = str(new_rotation)

        if self.__flip:
            existing_flip = utils.get_property(image_location.detection_properties, 'HORIZONTAL_FLIP', False)
            if existing_flip:
                del image_location.detection_properties['HORIZONTAL_FLIP']
            else:
                image_location.detection_properties['HORIZONTAL_FLIP'] = 'true'


    def get_region_size(self) -> utils.Size:
        return self.__region_size


    @staticmethod
    def __get_mapped_bounding_rect(regions: Sequence[utils.RotatedRect],
                                   frame_rot_mat: np.ndarray) -> utils.Rect[float]:
        # Since we are working with 2d points and we aren't doing any translation here,
        # we can drop the last row and column to save some work.
        simple_rotation = frame_rot_mat[:2, :2]
        mapped_corners = np.matmul(simple_rotation, _AffineTransformation.__get_all_corners(regions))
        corner1 = np.amin(mapped_corners, axis=1)
        corner2 = np.amax(mapped_corners, axis=1)
        return utils.Rect.from_corners(corner1, corner2 + 1)


    @staticmethod
    def __get_all_corners(regions: Iterable[utils.RotatedRect]) -> np.ndarray:
        # Matrix containing each region's 4 corners. First row is x coordinate and second row is y coordinate.
        return np.transpose(np.vstack([r.corners for r in regions]))  # type: ignore



class _IndividualXForms(object):
    """
    All transformation matrices are from https://en.wikipedia.org/wiki/Affine_transformation#Image_transformation
    """

    # Returns a matrix that will rotate points the given number of degrees in the counter-clockwise direction.
    @staticmethod
    def rotation(rotation_degrees: float) -> np.ndarray:
        if utils.rotation_angles_equal(rotation_degrees, 0):
            # When rotation angle is 0 some matrix elements that should
            # have been 0 were actually 1e-16 due to rounding issues.
            return np.identity(3)

        radians = np.deg2rad(rotation_degrees)
        sin_val = np.sin(radians)
        cos_val = np.cos(radians)
        return np.array((
            (cos_val, sin_val, 0),
            (-sin_val, cos_val, 0),
            (0, 0, 1)
        ))

    @staticmethod
    def horizontal_flip() -> np.ndarray:
        return np.array((
            (-1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        ))

    @staticmethod
    def translation(x_distance: float, y_distance: float) -> np.ndarray:
        return np.array((
            (1, 0, x_distance),
            (0, 1, y_distance),
            (0, 0, 1)
        ))
