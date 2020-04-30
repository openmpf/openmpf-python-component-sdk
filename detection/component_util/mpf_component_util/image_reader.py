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

import abc
from typing import Iterable

import cv2
import numpy as np

from . import frame_transformers
from . import utils
import mpf_component_api as mpf


class ImageReader(object):

    def __init__(self, image_job: mpf.ImageJob):
        video_cap = cv2.VideoCapture(image_job.data_uri)
        if not video_cap.isOpened():
            raise mpf.DetectionError.COULD_NOT_OPEN_DATAFILE.exception('Failed to open "%s".' % image_job.data_uri)

        was_read, image = video_cap.read()
        if not was_read or image is None:
            raise mpf.DetectionError.COULD_NOT_READ_DATAFILE.exception(
                'Failed to read image from "%s".' % image_job.data_uri)

        size = utils.Size.from_frame(image)
        self.__frame_transformer = frame_transformers.factory.get_transformer(image_job, size)
        self.__image = self.__frame_transformer.transform_frame(image, 0)

    def get_image(self) -> np.ndarray:
        return self.__image

    def reverse_transform(self, image_location: mpf.ImageLocation) -> None:
        self.__frame_transformer.reverse_transform(image_location, 0)



class ImageReaderMixin(abc.ABC):

    def get_detections_from_image(self, image_job: mpf.ImageJob) -> Iterable[mpf.ImageLocation]:
        image_reader = ImageReader(image_job)
        results = self.get_detections_from_image_reader(image_job, image_reader)
        for result in results:
            image_reader.reverse_transform(result)
            yield result

    @abc.abstractmethod
    def get_detections_from_image_reader(self, image_job: mpf.ImageJob, image_reader: ImageReader) \
            -> Iterable[mpf.ImageLocation]:
        raise NotImplementedError()
