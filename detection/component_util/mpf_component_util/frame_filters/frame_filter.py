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

from __future__ import division

import abc


class FrameFilter(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def segment_to_original_frame_position(self, segment_position):
        """
        Map a frame position within the segment to a frame position in the original video.
        :param segment_position: A frame position within the segment
        :return: The matching frame position in the original video.
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def original_to_segment_frame_position(self, original_position):
        """
        Map a frame position in the original video, to a position in the segment
        :param original_position: A frame position in the original video
        :return: The matching frame position in the segment
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def get_available_initialization_frame_count(self):
        """
        Returns the number of frames before the beginning of the segment. Skipped frames are not counted.
        :return: Number of available initialization frames
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def get_segment_frame_count(self):
        """
        :return: The number of frames in the segment
        """
        raise NotImplementedError()


    @abc.abstractmethod
    def get_segment_duration(self, original_frame_rate):
        """
        Gets the amount of time from the segment start to the segment end. The frame rate is adjusted so that
        the time from the start frame to the stop frame is the same as the original video.
        :param original_frame_rate: Frame rate of original video
        :return: The duration of the segment in seconds
        """
        raise NotImplementedError()


    def is_past_end_of_segment(self, original_position):
        last_segment_pos = self.get_segment_frame_count() - 1
        last_original_pos = self.segment_to_original_frame_position(last_segment_pos)
        return original_position > last_original_pos


    def get_segment_frame_rate(self, original_frame_rate):
        """
        Gets the frame rate of the segment. The frame rate is calculated so that the duration between the start
        frame and stop frame is the same as the original video.
        :param original_frame_rate: Frame rate of original video
        :return: Frames per second of the video segment
        """
        return self.get_segment_frame_count() / self.get_segment_duration(original_frame_rate)


    def get_current_segment_time_in_millis(self, original_position, original_frame_rate):
        """
        Gets the time in milliseconds between the segment start frame and the current position.
        :param original_position: Frame position in original video
        :param original_frame_rate: Frame rate of original video
        :return: Time in milliseconds since the segment started
        """
        segment_pos = self.original_to_segment_frame_position(original_position)
        frames_per_second = self.get_segment_frame_rate(original_frame_rate)
        time_in_seconds = segment_pos / frames_per_second
        return time_in_seconds * 1000


    def millis_to_segment_frame_position(self, original_frame_rate, segment_milliseconds):
        """
        Gets the segment position that is the specified number of milliseconds since the start of the segment
        :param original_frame_rate: Frame position in original video
        :param segment_milliseconds: Time since start of segment in milliseconds
        :return: Segment frame position for the specified number of milliseconds
        """
        segment_fps = self.get_segment_frame_rate(original_frame_rate)
        return segment_fps * segment_milliseconds // 1000


    def get_segment_frame_position_ratio(self, original_position):
        """
        Returns a number between 0 (start of video) and 1 (end of video) that indicates the current position
        in the video
        :param original_position: Frame position in original video
        :return: Number between 0 and 1 indicating current position in video
        """
        segment_position = self.original_to_segment_frame_position(original_position)
        return segment_position / self.get_segment_frame_count()


    def ratio_to_original_frame_position(self, ratio):
        """
        Returns the position in the original video for the given ratio
        :param ratio: Number between 0 and 1 that indicates position in video
        :return: Position in the original video
        """
        segment_position = int(self.get_segment_frame_count() * ratio)
        return self.segment_to_original_frame_position(segment_position)
