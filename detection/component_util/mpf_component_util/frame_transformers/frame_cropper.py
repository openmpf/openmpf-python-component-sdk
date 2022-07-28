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

import abc
from typing import List, Mapping

import numpy as np

import mpf_component_api as mpf
from . frame_transformer import BaseDecoratedFrameTransformer, IFrameTransformer
from .. import utils


class _BaseFrameCropper(BaseDecoratedFrameTransformer, abc.ABC):

    def get_frame_size(self, frame_index: int) -> utils.Size:
        return self._get_region_of_interest(frame_index).size


    def _do_frame_transform(self, frame: np.ndarray, frame_index: int) -> np.ndarray:
        region = self._get_region_of_interest(frame_index)
        return frame[region.y:region.br.y, region.x:region.br.x]


    def _do_reverse_transform(self, image_location: mpf.ImageLocation, frame_index: int) -> None:
        region = self._get_region_of_interest(frame_index)
        image_location.x_left_upper += region.x
        image_location.y_left_upper += region.y


    def _get_intersecting_region(
            self, region_of_interest: utils.Rect, frame_index: int) -> utils.Rect:
        frame_rect = utils.Rect.from_corner_and_size(
            utils.Point(0, 0), self._get_inner_frame_size(frame_index))
        return region_of_interest.intersection(frame_rect)


    @abc.abstractmethod
    def _get_region_of_interest(self, frame_index: int) -> utils.Rect:
        raise NotImplementedError()



class SearchRegionFrameCropper(_BaseFrameCropper):
    def __init__(self, search_region: utils.Rect, inner_transform: IFrameTransformer):
        super().__init__(inner_transform)
        self.__search_region: utils.Rect = self._get_intersecting_region(search_region, 0)


    def _get_region_of_interest(self, frame_index: int) -> utils.Rect:
        return self.__search_region


class FeedForwardFrameCropper(_BaseFrameCropper):
    def __init__(self, frame_location_map: Mapping[int, mpf.ImageLocation],
                 inner_transform: IFrameTransformer):
        super().__init__(inner_transform)
        self.__fed_forward_detections: List[utils.Rect] = \
            [self._get_intersecting_region(utils.Rect.from_image_location(loc), idx)
             for idx, loc in utils.dict_items_ordered_by_key(frame_location_map)]


    def _get_region_of_interest(self, frame_index: int) -> utils.Rect:
        try:
            return self.__fed_forward_detections[frame_index]
        except IndexError:
            raise IndexError(
                f'Attempted to get feed forward region of interest for frame: {frame_index}, '
                f'but there are only {len(self.__fed_forward_detections)} entries in the '
                f'feed forward track.')
