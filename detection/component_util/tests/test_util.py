#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2022 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2022 The MITRE Corporation                                      #
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

import os
import itertools
import sys
from typing import Iterable

import cv2
import numpy as np

import mpf_component_api as mpf
import mpf_component_util as mpf_util


def add_local_component_libs_to_sys_path():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../api'))


def get_data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)


def is_all_same_color(image, color_tuple):
    if image.size <= 0:
        raise ValueError(f'Image has a dimension with 0 size: {image.shape}')
    return (image == color_tuple).all()


def is_all_black(image):
    return is_all_same_color(image, (0, 0, 0))


def is_all_white(image):
    return is_all_same_color(image, (255, 255, 255))


def markup_image(original_image: np.ndarray, image_locations: Iterable[mpf.ImageLocation]) -> np.ndarray:
    image = original_image.copy()

    colors = get_colors()
    thickness = int(max(2, 0.0018 * max(image.shape[:2])))
    radius = 3 if thickness == 1 else thickness + 5

    for il in image_locations:
        detection_rect = mpf_util.RotatedRect(
            il.x_left_upper, il.y_left_upper, il.width, il.height,
            float(il.detection_properties.get('ROTATION', 0)),
            mpf_util.get_property(il.detection_properties, 'HORIZONTAL_FLIP', False))

        corners = [(int(c.x), int(c.y)) for c in detection_rect.corners]
        color = next(colors)
        cv2.line(image, corners[0], corners[1], color, thickness, cv2.LINE_AA)
        cv2.line(image, corners[1], corners[2], color, thickness, cv2.LINE_AA)
        cv2.line(image, corners[2], corners[3], color, thickness, cv2.LINE_AA)
        cv2.line(image, corners[3], corners[0], color, thickness, cv2.LINE_AA)

        cv2.circle(image, corners[0], radius, color, -1, cv2.LINE_AA)

    return image


def get_colors():
    colors = (
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (0, 255, 255),
        (255, 0, 255),
        (255, 0, 0)
    )
    return itertools.cycle(colors)

