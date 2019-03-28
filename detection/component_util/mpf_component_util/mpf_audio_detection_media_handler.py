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

import os
import subprocess

import mpf_component_api as mpf

logger = mpf.configure_logging('mpf-audio-detection-media-handler.log', __name__ == '__main__')

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

    # Convert milliseconds to seconds
    offset = start_time / 1000.0
    duration = None
    if stop_time is not None:
        duration = (stop_time - start_time) / 1000.0

    # Construct ffmpeg call
    command = (
        'ffmpeg -i {video_path:s} -ss {offset:f} ' +
        ('-t {duration:f} ' if stop_time is not None else '') +
        '-ac {channels:d} -ar {sampling_rate:d} -acodec {codec:s} ' +
        '-af "highpass=f={highpass:d}, lowpass=f={lowpass:d}" -vn ' +
        '-f {format:s} -y {audio_path:s} -loglevel error'
    ).format(
        video_path=video_path,
        audio_path=audio_path,
        offset=offset,
        duration=duration,
        channels=1,
        sampling_rate=16000,
        codec='pcm_s16le',
        highpass=200,
        lowpass=3000,
        format='wav'
    )

    # Call ffmpeg
    logger.info('query = %s', command)
    subprocess.call(command, shell=True)

    # If the file doesn't exist now, we failed to write it
    if not os.path.isfile(audio_path):
        raise IOError("Unable to transcode input file: " + video_path)
