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

import sys

import cv2


# For certain videos cv2.VideoCapture.set(cv2.CAP_PROP_POS_FRAMES, int) # does not work properly.
# If mpf_component_util.VideoCapture detects that cv2.VideoCapture is not setting the frame position
# properly it will fallback to different SeekStrategy.

class SetFramePositionSeek(object):
    # When setting frame position, OpenCV sets the frame position to 16 frames before the requested
    # frame in order to locate the closest key frame. Once OpenCV locates the key frame, it uses
    # cv2.VideoCapture.grab to advance cv2.VideoCapture's position. This means that when you need
    # to advance 16 or fewer frames, it is more efficient to just use cv2.VideoCapture.grab.
    # https://github.com/opencv/opencv/blob/4.5.0/modules/videoio/src/cap_ffmpeg_impl.hpp#L1459
    SET_POS_MIN_FRAMES = 16

    @classmethod
    def change_position(cls, cv_video_cap, current_position, requested_position):
        frame_diff = requested_position - current_position
        if 0 < frame_diff <= cls.SET_POS_MIN_FRAMES:
            return GrabSeek.change_position(cv_video_cap, current_position, requested_position)
        elif cv_video_cap.set(cv2.CAP_PROP_POS_FRAMES, requested_position):
            return requested_position
        else:
            return current_position

    @staticmethod
    def fallback():
        print('SetFramePositionSeek failed: falling back to GrabSeek', file=sys.stderr)
        return GrabSeek()



class _SequentialSeek(object):
    @classmethod
    def change_position(cls, cv_video_cap, current_position, requested_position):
        new_position_in_future = requested_position > current_position
        if new_position_in_future:
            start = current_position
        else:
            # The current position is past the requested position. We need to start reading from the very
            # beginning of the video. If it were possible to set the frame position to a frame in the middle
            #  of the video, then SetFramePositionSeek would not have failed.
            if not cv_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0):
                return current_position
            start = 0

        num_frames_to_discard = requested_position - start

        num_success = 0
        for i in range(num_frames_to_discard):
            if cls._advance(cv_video_cap):
                num_success += 1
            else:
                break
        return start + num_success

    @staticmethod
    def _advance(cv_video_cap):
        raise NotImplementedError()



class GrabSeek(_SequentialSeek):

    @staticmethod
    def _advance(cv_video_cap):
        return cv_video_cap.grab()

    @staticmethod
    def fallback():
        print('GrabSeek failed: falling back to ReadSeek', file=sys.stderr)
        return ReadSeek()


class ReadSeek(_SequentialSeek):
    @staticmethod
    def _advance(cv_video_cap):
        was_read, _ = cv_video_cap.read()
        return was_read

    @staticmethod
    def fallback():
        print('ReadSeek failed: No more fallbacks', file=sys.stderr)
        return None
