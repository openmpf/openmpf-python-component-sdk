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

from __future__ import annotations

from typing import Callable

from .. import utils

ResolveEdgeFunc = Callable[[float, float], int]

class RegionEdge(object):
    # Used when a value was not provided for an edge.
    @staticmethod
    def default() -> ResolveEdgeFunc:
        return lambda default_size, _: int(round(default_size))

    # Used when the value for an edge is specified as pixel coordinate.
    @staticmethod
    def absolute(value: int) -> ResolveEdgeFunc:
        if value < 0:
            return RegionEdge.default()
        return lambda _, max_size: int(round(min(value, max_size)))

    # Used when the value for an edge is specified as a percentage.
    @staticmethod
    def percentage(percentage: float) -> ResolveEdgeFunc:
        if percentage < 0:
            return RegionEdge.default()

        def calc_percentage(_, max_size):
            if percentage >= 100:
                return max_size
            return int(round(percentage * max_size / 100))
        return calc_percentage




class SearchRegion(object):
    """
    Holds the information about a search region as described by job properties. When a frame is going to be
    rotated the frame size is not known at the same time the job properties are parsed. This class can be
    constructed when parsing the job properties. Then, when the frame size is known, get_rect can be called.
    """
    def __init__(self, left=RegionEdge.default(), top=RegionEdge.default(), right=RegionEdge.default(),
                 bottom=RegionEdge.default()):
        self.__left = left
        self.__top = top
        self.__right = right
        self.__bottom = bottom


    def get_rect(self, frame_size) -> utils.Rect[int]:
        frame_size = utils.Size.as_size(frame_size)
        left_value = self.__left(0, frame_size.width)
        top_value = self.__top(0, frame_size.height)
        right_value = self.__right(frame_size.width, frame_size.width)
        bottom_value = self.__bottom(frame_size.height, frame_size.height)
        return utils.Rect.from_corners((left_value, top_value), (right_value, bottom_value))
