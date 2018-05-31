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


import cv2
import mpf_component_api as mpf
import mpf_component_util as mpf_util


logger = mpf.configure_logging('python-ocv-test.log', __name__ == '__main__')


class OcvComponent(mpf_util.ImageReaderMixin, mpf_util.VideoCaptureMixin, object):
    detection_type = 'TEST OCV DETECTION TYPE'


    @staticmethod
    def get_detections_from_image_reader(image_job, image_reader):
        logger.info('[%s] Received image job: %s', image_job.job_name, image_job)

        img = image_reader.get_image()

        height, width, _ = img.shape
        logger.info('[%s] Image at %s: width = %s, height = %s', image_job.job_name, image_job.data_uri, width, height)

        detection_sz = 20
        yield mpf.ImageLocation(width / 2 - detection_sz, 0, detection_sz, height - 1, -1.0,
                                mpf.Properties(METADATA='full_height'))

        yield mpf.ImageLocation(0, 0, width / 4, height / 4, -1,
                                mpf.Properties(METADATA='top left corner, .25 width and .25 height of image'))



    @staticmethod
    def get_detections_from_video_capture(video_job, video_capture):
        logger.info('[%s] Received video job: %s', video_job.job_name, video_job)

        width, height = video_capture.get_frame_size()

        detections = mpf.FrameLocationMap()
        last_il = mpf.ImageLocation(width / 2 - 1, height / 2 - 1, 2, 2)
        last_frame_read = 0
        for idx, frame in enumerate(video_capture):
            last_frame_read = idx
            last_il = mpf.ImageLocation(
                max(0, last_il.x_left_upper - 1),
                max(0, last_il.y_left_upper - 1),
                min(width - 1, last_il.width + 2),
                min(height - 1, last_il.height + 2))
            detections[idx] = last_il

        if not detections:
            return ()
        return [mpf.VideoTrack(0, last_frame_read, frame_locations=detections)]



