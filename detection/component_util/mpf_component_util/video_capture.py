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

from . import frame_filters
from . import frame_transformers
from . import utils
import mpf_component_api as mpf

import cv2
import sys


class VideoCapture(object):
    def __init__(self, video_job, enable_frame_transformers=True, enable_frame_filtering=True):
        self.__cv_video_capture = cv2.VideoCapture(video_job.data_uri)
        self.__frame_filter = self.__get_frame_filter(enable_frame_filtering, video_job, self.__cv_video_capture)
        self.__frame_transformer = self.__get_frame_transformer(enable_frame_transformers, video_job)
        self.__seek_strategy = frame_filters.SetFramePositionSeek()
        self.__frame_position = 0

        self.set_frame_position(0)


    def read(self):
        original_pos_before_read = self.__frame_position
        if self.__frame_filter.is_past_end_of_segment(original_pos_before_read):
            return False, None

        was_read, frame = self.__read_and_transform()
        if was_read:
            self.__move_to_next_frame_in_segment()
            return was_read, frame

        if self.__seek_fallback() and self.__update_original_frame_position(original_pos_before_read):
            return self.read()
        return False, None


    def __iter__(self):
        return self

    def next(self):
        was_read, frame = self.read()
        if was_read:
            return frame
        else:
            raise StopIteration()


    def is_opened(self):
        return self.__cv_video_capture.isOpened()


    def release(self):
        self.__cv_video_capture.release()


    def get_frame_count(self):
        return self.__frame_filter.get_segment_frame_count()


    def set_frame_position(self, frame_index):
        if frame_index < 0 or frame_index >= self.__frame_filter.get_segment_frame_count():
            return False

        original_position = self.__frame_filter.segment_to_original_frame_position(frame_index)
        return self.__update_original_frame_position(original_position)


    def get_current_frame_position(self):
        return self.__frame_filter.original_to_segment_frame_position(self.__frame_position)


    def get_frame_rate(self):
        original_frame_rate = self.__get_property(cv2.CAP_PROP_FPS)
        return self.__frame_filter.get_segment_frame_rate(original_frame_rate)


    def get_frame_size(self):
        return self.__frame_transformer.get_frame_size(max(0, self.get_current_frame_position() - 1))


    def get_original_frame_size(self):
        width = int(self.__get_property(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.__get_property(cv2.CAP_PROP_FRAME_HEIGHT))
        return utils.Size(width, height)


    def get_frame_position_ratio(self):
        return self.__frame_filter.get_segment_frame_position_ratio(self.__frame_position)


    def set_frame_position_ratio(self, position_ratio):
        if position_ratio < 0 or position_ratio > 1:
            return False
        frame_position = self.__frame_filter.ratio_to_original_frame_position(position_ratio)
        return self.__update_original_frame_position(frame_position)


    def get_current_time_in_millis(self):
        original_frame_rate = self.__get_property(cv2.CAP_PROP_FPS)
        return self.__frame_filter.get_current_segment_time_in_millis(self.__frame_position, original_frame_rate)


    def set_frame_position_in_millis(self, millis):
        original_frame_rate = self.__get_property(cv2.CAP_PROP_FPS)
        new_frame_position = self.__frame_filter.millis_to_segment_frame_position(original_frame_rate, millis)
        return self.set_frame_position(new_frame_position)


    def get_property(self, property_id):
        if property_id == cv2.CAP_PROP_FRAME_WIDTH:
            return self.get_frame_size().width
        elif property_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.get_frame_size().height
        elif property_id == cv2.CAP_PROP_FPS:
            return self.get_frame_rate()
        elif property_id == cv2.CAP_PROP_POS_FRAMES:
            return self.get_current_frame_position()
        elif property_id == cv2.CAP_PROP_POS_AVI_RATIO:
            return self.get_frame_position_ratio()
        elif property_id == cv2.CAP_PROP_POS_MSEC:
            return self.get_current_time_in_millis()
        else:
            return self.__get_property(property_id)


    def set_property(self, property_id, value):
        if property_id in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS):
            return False
        elif property_id == cv2.CAP_PROP_POS_FRAMES:
            return self.set_frame_position(int(value))
        elif property_id == cv2.CAP_PROP_POS_AVI_RATIO:
            return self.set_frame_position_ratio(value)
        elif property_id == cv2.CAP_PROP_POS_MSEC:
            return self.set_frame_position_in_millis(value)
        else:
            return self.__set_property(property_id, value)


    def get_four_char_codec_code(self):
        return int(self.__get_property(cv2.CAP_PROP_FOURCC))


    def reverse_transform(self, video_track):
        video_track.start_frame = self.__frame_filter.segment_to_original_frame_position(video_track.start_frame)
        video_track.stop_frame = self.__frame_filter.segment_to_original_frame_position(video_track.stop_frame)

        new_frame_locations = mpf.FrameLocationMap()
        for frame_pos, image_loc in video_track.frame_locations.iteritems():
            self.__frame_transformer.reverse_transform(image_loc, frame_pos)

            fixed_frame_index = self.__frame_filter.segment_to_original_frame_position(frame_pos)
            new_frame_locations[fixed_frame_index] = image_loc

        video_track.frame_locations = new_frame_locations


    def get_initialization_frames_if_available(self, num_requested_frames):
        num_init_frames_available = self.__frame_filter.get_available_initialization_frame_count()
        num_frames_to_get = min(num_init_frames_available, num_requested_frames)
        if num_frames_to_get < 0:
            return ()

        initial_frame_pos = self.__frame_position

        first_init_frame_idx = self.__frame_filter.segment_to_original_frame_position(-1 * num_frames_to_get)
        if not self.__update_original_frame_position(first_init_frame_idx):
            return ()

        initialization_frames = []
        for i in xrange(num_frames_to_get):
            was_read, frame = self.read()
            if was_read:
                initialization_frames.append(frame)

        # If self. __update_original_frame_position does not succeed that means it is not possible to
        # read any more frames from the video, so all future reads will fail. If any initialization frames were read,
        # they will be returned.
        self.__update_original_frame_position(initial_frame_pos)

        return initialization_frames



    def __get_property(self, property_id):
        return self.__cv_video_capture.get(property_id)


    def __set_property(self, property_id, value):
        return self.__cv_video_capture.set(property_id, value)


    def __get_frame_transformer(self, frame_transformers_enabled, video_job):
        if frame_transformers_enabled:
            return frame_transformers.factory.get_transformer(video_job, self.get_original_frame_size())
        else:
            return frame_transformers.NoOpTransformer(self.get_original_frame_size())


    def __read_and_transform(self):
        was_read, frame = self.__cv_video_capture.read()
        if was_read:
            frame = self.__frame_transformer.transform_frame(frame, self.get_current_frame_position())
            self.__frame_position += 1
        return was_read, frame


    def __move_to_next_frame_in_segment(self):
        if not self.__frame_filter.is_past_end_of_segment(self.__frame_position):
            seg_pos_before_read = self.__frame_filter.original_to_segment_frame_position(self.__frame_position - 1)
            next_original_frame = self.__frame_filter.segment_to_original_frame_position(seg_pos_before_read + 1)
            # At this point a frame was successfully read. If self.__update_original_frame_position does not succeed
            # that means it is not possible to read any more frames from the video, so all future reads will fail
            self.__update_original_frame_position(next_original_frame)


    def __seek_fallback(self):
        if self.__seek_strategy is None:
            return False

        self.__seek_strategy = self.__seek_strategy.fallback()
        if self.__seek_strategy is None:
            return False

        # In order to fallback to a different seek strategy, self.__cv_video_capture must be capable of setting the
        # frame position to 0.
        was_set = self.__set_property(cv2.CAP_PROP_POS_FRAMES, 0)
        if was_set:
            self.__frame_position = 0
            return True

        self.__seek_strategy = None
        return False


    def __update_original_frame_position(self, requested_original_position):
        if self.__frame_position == requested_original_position:
            return True
        if self.__seek_strategy is None:
            return False

        self.__frame_position = self.__seek_strategy.change_position(self.__cv_video_capture, self.__frame_position,
                                                                     requested_original_position)
        if self.__frame_position == requested_original_position:
            return True

        return self.__seek_fallback() and self.__update_original_frame_position(requested_original_position)


    @staticmethod
    def __get_frame_filter(frame_filtering_enabled, video_job, cv_video_capture):
        frame_count = VideoCapture.__get_frame_count(video_job, cv_video_capture)
        if not frame_filtering_enabled:
            return frame_filters.get_no_op_filter(frame_count)

        if video_job.feed_forward_track is not None:
            if not video_job.feed_forward_track.frame_locations:
                raise ValueError('The video job, %s, had a feed forward track, but it was empty.' % video_job.job_name)

            first_track_frame = min(video_job.feed_forward_track.frame_locations)
            last_track_frame = max(video_job.feed_forward_track.frame_locations)
            if first_track_frame != video_job.start_frame or last_track_frame != video_job.stop_frame:
                print >> sys.stderr, (
                    'The feed forward track for Job: %s starts at frame %s and ends at frame %s, '
                    'but the job\'s start frame is %s and its stop frame is %s. '
                    'The job had a feed forward track so the entire feed forward track will be used.'
                    % (video_job.job_name, first_track_frame, last_track_frame, video_job.start_frame,
                       video_job.stop_frame))
            return frame_filters.FeedForwardFrameFilter(video_job.feed_forward_track)

        if utils.get_property(video_job.job_properties, 'USE_KEY_FRAMES', False):
            try:
                return frame_filters.KeyFrameFilter(video_job)
            except EnvironmentError as err:
                print >> sys.stderr, 'Unable to get key frames due to:', err
                print >> sys.stderr, 'Falling back to IntervalFrameFilter'


        return frame_filters.IntervalFrameFilter.from_job(video_job, frame_count)


    @staticmethod
    def __get_frame_count(video_job, cv_video_capture):
        frame_count = utils.get_property(video_job.media_properties, 'FRAME_COUNT', -1)
        if frame_count > 0:
            return frame_count
        return int(cv_video_capture.get(cv2.CAP_PROP_FRAME_COUNT))


def video_capture_wrapper(video_job, get_detections_fn):
    video_capture = VideoCapture(video_job)
    results = get_detections_fn(video_job, video_capture)
    for result in results:
        video_capture.reverse_transform(result)
        yield result


class VideoCaptureMixin(object):
    def get_detections_from_video(self, video_job):
        return video_capture_wrapper(video_job, self.get_detections_from_video_capture)

    def get_detections_from_video_capture(self, video_job, video_capture):
        raise NotImplementedError()