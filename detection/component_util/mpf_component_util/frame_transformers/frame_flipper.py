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

from . import frame_transformer
import cv2


class FrameFlipper(frame_transformer.BaseDecoratedFrameTransformer):

    def _do_frame_transform(self, frame, frame_index):
        #  Flip around y-axis
        return cv2.flip(frame, 1)


    def _do_reverse_transform(self, image_location, frame_index):
        top_right_x = image_location.x_left_upper + image_location.width
        width = self.get_frame_size(frame_index).width
        image_location.x_left_upper = width - top_right_x


    def get_frame_size(self, frame_index):
        return self._get_inner_frame_size(frame_index)
