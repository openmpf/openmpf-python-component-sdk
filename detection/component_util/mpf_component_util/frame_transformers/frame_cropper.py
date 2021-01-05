#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2021 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2021 The MITRE Corporation                                      #
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

from . frame_transformer import BaseDecoratedFrameTransformer
from .. import utils


class _BaseFrameCropper(BaseDecoratedFrameTransformer, abc.ABC):

    def get_frame_size(self, frame_index):
        return self._get_region_of_interest(frame_index).size


    def _do_frame_transform(self, frame, frame_index):
        region = self._get_region_of_interest(frame_index)
        return frame[region.y:region.br.y, region.x:region.br.x]


    def _do_reverse_transform(self, image_location, frame_index):
        region = self._get_region_of_interest(frame_index)
        image_location.x_left_upper += region.x
        image_location.y_left_upper += region.y


    @abc.abstractmethod
    def _get_region_of_interest(self, frame_index):
        raise NotImplementedError()



class SearchRegionFrameCropper(_BaseFrameCropper):
    def __init__(self, search_region, inner_transform):
        super().__init__(inner_transform)
        self.__search_region = self.__get_intersecting_region(search_region, 0)


    def _get_region_of_interest(self, frame_index):
        return self.__search_region

    def __get_intersecting_region(self, search_region, frame_index):
        frame_rect = utils.Rect.from_corner_and_size(utils.Point(0, 0), self._get_inner_frame_size(frame_index))
        return search_region.intersection(frame_rect)



class FeedForwardFrameCropper(_BaseFrameCropper):
    def __init__(self, frame_location_map, inner_transform):
        super().__init__(inner_transform)
        self.__fed_forward_detections = [utils.Rect.from_image_location(loc)
                                         for loc in utils.dict_values_ordered_by_key(frame_location_map)]


    def _get_region_of_interest(self, frame_index):
        try:
            return self.__fed_forward_detections[frame_index]
        except IndexError:
            raise IndexError(
                'Attempted to get feed forward region of interest for frame: %s, '
                'but there are only %s entries in the feed forward track.'
                % (frame_index, len(self.__fed_forward_detections)))
