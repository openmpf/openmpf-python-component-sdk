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

import abc


class IFrameTransformer(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def transform_frame(self, frame, frame_index):
        raise NotImplementedError()

    @abc.abstractmethod
    def reverse_transform(self, image_location, frame_index):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_frame_size(self, frame_index):
        raise NotImplementedError()



class NoOpTransformer(IFrameTransformer):
    def __init__(self, frame_size):
        self.__frame_size = frame_size

    def get_frame_size(self, frame_index):
        return self.__frame_size

    def transform_frame(self, frame, frame_index):
        return frame

    def reverse_transform(self, image_location, frame_index):
        pass



class BaseDecoratedFrameTransformer(IFrameTransformer):
    __metaclass__ = abc.ABCMeta

    def __init__(self, inner_transform):
        self.__inner_transform = inner_transform


    def transform_frame(self, frame, frame_index):
        frame = self.__inner_transform.transform_frame(frame, frame_index)
        return self._do_frame_transform(frame, frame_index)


    def reverse_transform(self, image_location, frame_index):
        self._do_reverse_transform(image_location, frame_index)
        self.__inner_transform.reverse_transform(image_location, frame_index)


    def _get_inner_frame_size(self, frame_index):
        return self.__inner_transform.get_frame_size(frame_index)


    @abc.abstractmethod
    def _do_frame_transform(self, frame, frame_index):
        raise NotImplementedError()


    @abc.abstractmethod
    def _do_reverse_transform(self, image_location, frame_index):
        raise NotImplementedError()

