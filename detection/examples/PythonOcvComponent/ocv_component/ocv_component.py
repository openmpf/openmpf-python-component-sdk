#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2023 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2023 The MITRE Corporation                                      #
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

import logging
import pkg_resources
import os
from typing import Iterable

import mpf_component_api as mpf
import mpf_component_util as mpf_util

logger = logging.getLogger('OcvComponent')

class OcvComponent(mpf_util.ImageReaderMixin, mpf_util.VideoCaptureMixin):

    def get_detections_from_image_reader(
            self,
            image_job: mpf.ImageJob,
            image_reader: mpf_util.ImageReader) -> Iterable[mpf.ImageLocation]:

        logger.info('[%s] Received image job: %s', image_job.job_name, image_job)
        model = get_model(image_job)  # A real component would use the model.

        img = image_reader.get_image()

        height, width, _ = img.shape
        logger.info('[%s] Image at %s: width = %s, height = %s',
                    image_job.job_name, image_job.data_uri, width, height)

        detection_sz = 20
        yield mpf.ImageLocation(width // 2 - detection_sz, 0, detection_sz, height - 1, -1.0,
                                dict(METADATA='full_height'))

        yield mpf.ImageLocation(0, 0, width // 4, height // 4, -1,
                                dict(METADATA='top left corner, .25 width and .25 height of image'))


    def get_detections_from_video_capture(
            self,
            video_job: mpf.VideoJob,
            video_capture: mpf_util.VideoCapture) -> Iterable[mpf.VideoTrack]:
        logger.info('[%s] Received video job: %s', video_job.job_name, video_job)
        model = get_model(video_job)  # A real component would use the model.

        width, height = video_capture.frame_size

        detections = dict()
        expand_rate = 5
        last_il = mpf.ImageLocation(0, 0, 1, 1)
        last_frame_read = 0
        for idx, frame in enumerate(video_capture):
            last_frame_read = idx
            last_il = mpf.ImageLocation(
                0, 0,
                min(width - 1, last_il.width + expand_rate),
                min(height - 1, last_il.height + expand_rate))
            detections[idx] = last_il

        if not detections:
            return ()
        return [mpf.VideoTrack(0, last_frame_read, frame_locations=detections)]




ModelSettings = (mpf_util.ModelsIniParser(pkg_resources.resource_filename(__name__, 'models'))
                 .register_path_field('network')
                 .register_path_field('names')
                 .register_int_field('num_classes')
                 .build_class())


def get_model(job):
    model_name = job.job_properties.get('MODEL_NAME', 'animal model')
    models_dir_path = os.path.join(job.job_properties.get('MODELS_DIR_PATH', '.'),
                                   'PythonOcvComponent')
    model_settings = ModelSettings(model_name, models_dir_path)
    logger.info('[%s] Successfully retrieved settings file for the "%s" model: '
                '{ network = "%s", names = "%s", num_classes = %s }',
                job.job_name, model_name, model_settings.network, model_settings.names, model_settings.num_classes)
    return load_model(model_settings)


def load_model(model_settings):
    # A real component would actually load the model here.
    with open(model_settings.names) as f:
        names = [line.strip() for line in f]
    logger.info('Successfully loaded names file from "%s": %s', model_settings.names, names)
    return object()
