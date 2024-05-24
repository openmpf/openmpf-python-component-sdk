#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2024 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2024 The MITRE Corporation                                      #
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

from . import frame_filter
from .. import utils


class IntervalFrameFilter(frame_filter.FrameFilter):
    """
    If a video file is long enough, the Workflow Manager will create multiple jobs, each with different start
    and stop frames. Additionally many components support a FRAME_INTERVAL property.
    These values tell components to only process certain frames in the video. Instead of having components
    figure out which frames to process and which frames to skip, this class performs the calculations necessary
    to filter out frames that shouldn't be processed. From the component's point of view, it is processing
    the entire video, but it is really only processing a particular segment of the video.
    """

    def __init__(self, start_frame, stop_frame, frame_interval):
        super(IntervalFrameFilter, self).__init__()
        self.__start_frame = int(start_frame)
        self.__stop_frame = int(stop_frame)
        self.__frame_interval = int(frame_interval)


    @staticmethod
    def from_job(job, original_frame_count):
        return IntervalFrameFilter(job.start_frame,
                                   IntervalFrameFilter.get_stop_frame(job, original_frame_count),
                                   IntervalFrameFilter.get_frame_interval(job))

    @staticmethod
    def get_stop_frame(job, original_frame_count):
        if 0 <= job.stop_frame < original_frame_count:
            return job.stop_frame

        stop_frame = original_frame_count - 1
        if stop_frame < job.start_frame:
            raise IndexError('Unable to handle segment: %s - %s because original media only has %s frames.'
                             % (job.start_frame, job.stop_frame, original_frame_count))
        return stop_frame


    @staticmethod
    def get_frame_interval(job):
        interval = utils.get_property(job.job_properties, 'FRAME_INTERVAL', 1)
        return max(interval, 1)


    def segment_to_original_frame_position(self, segment_position):
        return self.__frame_interval * segment_position + self.__start_frame


    def original_to_segment_frame_position(self, original_position):
        return (original_position - self.__start_frame) // self.__frame_interval


    def get_segment_frame_count(self):
        frame_range = self.__stop_frame - self.__start_frame + 1
        full_segments = frame_range // self.__frame_interval
        has_remainder = frame_range % self.__frame_interval != 0
        if has_remainder:
            return full_segments + 1
        else:
            return full_segments


    def get_segment_duration(self, original_frame_rate):
        frame_range = self.__stop_frame - self.__start_frame + 1
        return frame_range / original_frame_rate


    def get_available_initialization_frame_count(self):
        return self.__start_frame // self.__frame_interval
