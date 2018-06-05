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
import sys


# For certain videos cv2.VideoCapture.set(cv2.CAP_PROP_POS_FRAMES, int) # does not work properly.
# If mpf_component_util.VideoCapture detects that cv2.VideoCapture is not setting the frame position
# properly it will fallback to different SeekStrategy.

class SetFramePositionSeek(object):
    @staticmethod
    def change_position(cv_video_cap, current_position, requested_position):
        if cv_video_cap.set(cv2.CAP_PROP_POS_FRAMES, requested_position):
            return requested_position
        else:
            return current_position

    @staticmethod
    def fallback():
        print >> sys.stderr, 'SetFramePositionSeek failed: falling back to GrabSeek'
        return GrabSeek()



class _SequentialSeek(object):
    def change_position(self, cv_video_cap, current_position, requested_position):
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
        for i in xrange(num_frames_to_discard):
            if self._advance(cv_video_cap):
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
        print >> sys.stderr, 'GrabSeek failed: falling back to ReadSeek'
        return ReadSeek()


class ReadSeek(_SequentialSeek):
    @staticmethod
    def _advance(cv_video_cap):
        was_read, _ = cv_video_cap.read()
        return was_read

    @staticmethod
    def fallback():
        print >> sys.stderr, 'ReadSeek failed: No more fallbacks'
        return None
