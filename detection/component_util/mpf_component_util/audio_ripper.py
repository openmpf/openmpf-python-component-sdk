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

from __future__ import print_function, division

import os
import subprocess

import mpf_component_api as mpf

logger = mpf.configure_logging('audio-ripper.log', __name__ == '__main__')

def rip_audio(video_path, audio_path, start_time=0, stop_time=None):
    """
    Rips the audio from from start_time to stop_time in video_path and writes
    it to audio_path (a .wav file)

    :param video_path: The path to the video file (video_job.data_uri).
    :param audio_path: The path at which to save the audio.
    :param start_time: The time (0-based index, in milliseconds) associated with the beginning of audio segment to rip from the video. Default 0.
    :param stop_time: The time (0-based index, in milliseconds) associated with the end of the audio segment to rip from the video. To go to the end of the file, pass None. Default None.
    """
    logger.info((
            'Ripping audio from {video_path:s} into {audio_path:s}'
        ).format(
            video_path=video_path,
            audio_path=audio_path
        )
    )

    # Resolve symbolic paths if necessary
    video_path = os.path.realpath(video_path)
    audio_path = os.path.realpath(audio_path)

    # Confirm that input file exists
    if not os.path.isfile(video_path):
        raise ValueError("Input file does not exist: " + video_path)

    # Confirm that output file can be created
    audio_dir = os.path.split(audio_path)[0]
    if not os.path.isdir(audio_dir):
        raise ValueError("Output directory does not exist: " + audio_dir)

    # Construct ffmpeg call
    # Note: ffmpeg options apply to the next specified file. Order matters.
    command = ('ffmpeg', '-i', video_path)
    if start_time:
        command += ('-ss', str(start_time/1000.0))  # Audio clip start time (ms)
    if stop_time:
        command += ('-to', str(stop_time/1000.0))   # Audio clip end time (ms)
    command += (
        '-ac', '1',                                 # Channels
        '-ar', '16000',                             # Sampling rate
        '-acodec', 'pcm_s16le',                     # Audio codec
        '-af', 'highpass=f=200,lowpass=f=3000',     # Audio filter graph
        '-f', 'wav',                                # Save as WAV file
        audio_path,
        '-vn',                                      # Disable video
        '-y',                                       # Overwrite output files
        '-loglevel', 'error'                        # Suppress logs
    )

    # Call ffmpeg
    try:
        proc = subprocess.Popen(command, stderr=subprocess.PIPE)
    except OSError as err:
        # 2 corresponds to errno.ENOENT (no such file or directory)
        if err.errno == 2:
            raise EnvironmentError(
                err.errno,
                'ffmpeg does not appear to be installed'
            )
        else:
            raise

    # Wait for ffmpeg to complete, get stderr
    outs, errs = proc.communicate()

    # If we get a nonzero exit status, raise exception for it
    exit_code = proc.returncode
    if exit_code != 0:
        error_msg = 'The ffmpeg process exited '
        if exit_code > 0:
            error_msg += 'with exit code: {c:d}.'.format(c=exit_code)
        else:
            # When exit code is negative, it is the number of the signal that
            # caused the process to exit
            error_msg += 'due to signal number: {c:d}.'.format(c=-exit_code)
            exit_code = 128 - exit_code
        if errs:
            error_msg += ' Error message: {e:s}'.format(e=errs)
        logger.error(error_msg)
        raise EnvironmentError(exit_code, error_msg)


    # If the file doesn't exist now, we failed to write it
    if not os.path.isfile(audio_path):
        error_str = "Unable to transcode input file: " + video_path
        logger.error(error_str)
        raise mpf.DetectionException(
            error_str,
            mpf.DetectionError.OTHER_DETECTION_ERROR_TYPE
        )
