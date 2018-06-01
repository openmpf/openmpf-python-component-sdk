#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2018 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2018 The MITRE Corporation                                      #
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

from . import frame_transformer
from .. import utils
import cv2


class FrameRotator(frame_transformer.BaseDecoratedFrameTransformer):

    def __init__(self, inner_transform, rotation_degrees):
        super(FrameRotator, self).__init__(inner_transform)
        self.__rotation_degrees = rotation_degrees
        if rotation_degrees not in (0, 90, 180, 270):
            raise ValueError('Rotation degrees must be 0, 90, 180, or 270.')


    def _do_frame_transform(self, frame, frame_index):
        degrees = self.__rotation_degrees
        if degrees == 90:
            frame = cv2.transpose(frame)
            # Flip around y-axis
            return cv2.flip(frame, 1)
        elif degrees == 180:
            # Flip around both axes
            return cv2.flip(frame, -1)
        elif degrees == 270:
            frame = cv2.transpose(frame)
            # Flip around x-axis
            return cv2.flip(frame, 0)
        return frame



    def _do_reverse_transform(self, image_location, frame_index):
        top_left = self.__get_reverted_top_left_corner(image_location, frame_index)

        image_location.x_left_upper = top_left.x
        image_location.y_left_upper = top_left.y

        if self.__rotation_degrees in (90, 270):
            image_location.width, image_location.height = image_location.height, image_location.width



    def __get_reverted_top_left_corner(self, image_location, frame_index):
        detection_rect = utils.Rect.from_image_location(image_location)
        original_size = self._get_inner_frame_size(frame_index)

        degrees = self.__rotation_degrees
        if degrees == 90:
            return utils.Point(detection_rect.y,
                               original_size.height - detection_rect.br.x)
        elif degrees == 180:
            return utils.Point(original_size.width - detection_rect.br.x,
                               original_size.height - detection_rect.br.y)
        elif degrees == 270:
            return utils.Point(original_size.width - detection_rect.br.y,
                               detection_rect.x)
        else:
            return detection_rect.tl


    def get_frame_size(self, frame_index):
        inner_size = self._get_inner_frame_size(frame_index)
        if self.__rotation_degrees in (90, 270):
            return utils.Size(inner_size.height, inner_size.width)
        else:
            return inner_size
