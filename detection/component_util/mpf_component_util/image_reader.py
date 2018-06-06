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

from . import frame_transformers
from . import utils
import cv2


class ImageReader(object):
    def __init__(self, image_job):
        image = cv2.imread(image_job.data_uri, cv2.IMREAD_IGNORE_ORIENTATION + cv2.IMREAD_COLOR)
        size = utils.Size.from_frame(image)
        self.__frame_transformer = frame_transformers.factory.get_transformer(image_job, size)
        self.__image = self.__frame_transformer.transform_frame(image, 0)

    def get_image(self):
        return self.__image

    def reverse_transform(self, image_location):
        self.__frame_transformer.reverse_transform(image_location, 0)



def image_reader_wrapper(image_job, get_detections_fn):
    image_reader = ImageReader(image_job)
    results = get_detections_fn(image_job, image_reader)
    for result in results:
        image_reader.reverse_transform(result)
        yield result


class ImageReaderMixin(object):
    def get_detections_from_image(self, image_job):
        return image_reader_wrapper(image_job, self.get_detections_from_image_reader)

    def get_detections_from_image_reader(self, image_job, image_reader):
        raise NotImplementedError()


