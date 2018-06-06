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

from . import frame_filter
from .. import utils

import bisect
import subprocess
import sys


class _FrameListFilter(frame_filter.FrameFilter):

    def __init__(self, frames_to_show):
        super(_FrameListFilter, self).__init__()
        self.__frames_to_show = frames_to_show


    def segment_to_original_frame_position(self, segment_position):
        try:
            return self.__frames_to_show[segment_position]
        except IndexError:
            raise IndexError(
                'Attempted to get the original position for segment position: %s, '
                'but the maximum segment position is %s' % (segment_position, self.get_segment_frame_count() - 1))


    def original_to_segment_frame_position(self, original_position):
        return bisect.bisect_left(self.__frames_to_show, original_position)


    def get_segment_frame_count(self):
        return len(self.__frames_to_show)


    def get_segment_duration(self, original_frame_rate):
        frame_range = self.__frames_to_show[-1] - self.__frames_to_show[0] + 1
        return frame_range / float(original_frame_rate)


    def get_available_initialization_frame_count(self):
        return 0



class FeedForwardFrameFilter(_FrameListFilter):
    def __init__(self, feed_forward_track):
        super(FeedForwardFrameFilter, self).__init__(sorted(feed_forward_track.frame_locations))



class KeyFrameFilter(_FrameListFilter):
    def __init__(self, video_job):
        super(KeyFrameFilter, self).__init__(self.get_key_frames(video_job))


    LINE_PREFIX = 'frame.'

    @staticmethod
    def get_key_frames(video_job):
        command = ('ffprobe', '-loglevel', 'warning', '-select_streams', 'v', '-show_entries', 'frame=key_frame',
                   '-print_format', 'flat=h=0', video_job.data_uri)
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        except OSError as err:
            if err.errno == 2:
                raise EnvironmentError(err.errno, 'ffprobe does not appear to be installed')
            else:
                raise

        key_frames = []
        num_key_frames_seen = 0
        frame_interval = max(1, utils.get_property(video_job.job_properties, 'FRAME_INTERVAL', 1))
        stop_frame = video_job.stop_frame
        if stop_frame < 0:
            stop_frame = float('inf')

        for line in proc.stdout:
            # Expected line format for key frame: frame.209.key_frame=1
            # Expected line format for non-key frame: frame.210.key_frame=0
            if not line.startswith(KeyFrameFilter.LINE_PREFIX):
                print >> sys.stderr, ('Expected each line of output from ffprobe to start with "%s", '
                                      'but the following line was found "%s"'
                                      % (KeyFrameFilter.LINE_PREFIX, line))
                continue

            line_parts = line.split('.')
            frame_number = int(line_parts[1])
            if frame_number < video_job.start_frame:
                continue

            if frame_number > stop_frame:
                proc.terminate()
                return key_frames

            if 'key_frame=1' not in line_parts[2]:
                continue

            if num_key_frames_seen % frame_interval == 0:
                key_frames.append(frame_number)
            num_key_frames_seen += 1

        exit_code = proc.wait()
        if exit_code == 0:
            return key_frames

        error_msg = 'The ffprobe process '
        if exit_code > 0:
            error_msg += 'exited with exit code: %s.' % exit_code
        else:
            # When exit code is negative, it is the number of the signal that caused the process exit.
            error_msg += 'exited due to signal number: %s.' % (-1 * exit_code)
            exit_code = 128 - exit_code
        raise EnvironmentError(exit_code, error_msg)
