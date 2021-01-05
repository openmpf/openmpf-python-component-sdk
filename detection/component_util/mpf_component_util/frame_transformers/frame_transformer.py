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

from .. import utils


class IFrameTransformer(abc.ABC):

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
        self.__frame_size = utils.Size.as_size(frame_size)

    def get_frame_size(self, frame_index):
        return self.__frame_size

    def transform_frame(self, frame, frame_index):
        return frame

    def reverse_transform(self, image_location, frame_index):
        pass



class BaseDecoratedFrameTransformer(IFrameTransformer, abc.ABC):
    """
    This class implements both a decorator pattern (the design pattern not Python decorators) and a template
    method pattern. The decorator pattern is used to make it possible to combine any number of frame transformers.
    The template method pattern is used encapsulate the process of calling the inner transform in the right
    order. When doing the forward transform, the inner transform gets called first. The reverse_transform
    occurs in the opposite order, so the subclass's reverseTransform is called first, then the inner
    reverse_transform occurs.
    """

    def __init__(self, inner_transform):
        self.__inner_transform = inner_transform


    def transform_frame(self, frame, frame_index):
        """
        Calls in the inner transform before calling the subclass's _do_frame_transform method.

        :param frame: Frame to transform.
        :param frame_index: 0-based index of the frame's position in video or 0 if frame is from image.
        :return: The transformed frame.
        """
        frame = self.__inner_transform.transform_frame(frame, frame_index)
        return self._do_frame_transform(frame, frame_index)


    def reverse_transform(self, image_location, frame_index):
        """
        Calls the subclass's _do_reverse_transform before calling the inner transformer's reverse_transform.

        :param image_location: The image location to do the reverse transform on.
        :param frame_index: 0-based index of the frame in which the detection was found or 0 if found in image.
        """
        self._do_reverse_transform(image_location, frame_index)
        self.__inner_transform.reverse_transform(image_location, frame_index)


    def _get_inner_frame_size(self, frame_index):
        return self.__inner_transform.get_frame_size(frame_index)


    @abc.abstractmethod
    def _do_frame_transform(self, frame, frame_index):
        """
        Subclasses override this method to implement the reverse transform

        :param frame: Frame to transform.
        :param frame_index: 0-based index of the frame's position in video or 0 if frame is from image.
        :return: The transformed frame.
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def _do_reverse_transform(self, image_location, frame_index):
        """
        Subclasses override this method to implement the reverse transform.

        :param image_location: The image location to do the reverse transform on.
        :param frame_index: 0-based index of the frame's position in video or 0 if frame is from image.
        """
        raise NotImplementedError()
