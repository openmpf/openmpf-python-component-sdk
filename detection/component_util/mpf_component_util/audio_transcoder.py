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

import os
import subprocess
from typing import Optional

import pydub.audio_segment

import mpf_component_api as mpf


def transcode_to_wav(filepath: str, start_time: float = 0,
                     stop_time: Optional[float] = None) -> bytes:
    """
    Transcodes the audio contained in filepath (can be an audio or video file) from
    start_time to stop_time to WAVE format using ffmpeg, and returns it as a bytes object

    :param filepath: The path to the file (job.data_uri).
    :param start_time: The time (in milliseconds) associated with the beginning of audio segment.
                       Default 0.
    :param stop_time: The time (in milliseconds) associated with the end of the audio segment.
                      To go to the end of the file, pass None. Default None.
    """

    if not os.path.exists(filepath):
        raise mpf.DetectionError.COULD_NOT_OPEN_DATAFILE.exception(
            'Input file does not exist: ' + filepath)

    # Construct ffmpeg call
    # Note: ffmpeg options apply to the next specified file. Order matters.
    # Note: Previously, pydub was used to perform this process. However, a
    #  persistent bug in the tool (https://github.com/jiaaro/pydub/issues/328)
    #  prevents us from selecting the codec. Further, the sample rate, start
    #  and stop times, output channels, and filtergraph are not applied directly
    #  through ffmpeg. Therefore, we perform the transcoding with ffmpeg
    #  directly, and only use pydub to fix headers in the output bytes.
    command = ['ffmpeg', '-i', filepath]
    if start_time and start_time > 0:
        command += ['-ss', str(start_time / 1000.0)]  # Audio clip start time
    if stop_time and stop_time > 0:
        command += ['-to', str(stop_time / 1000.0)]  # Audio clip end time
    command += [
        '-ac', '1',  # Channels
        '-ar', '8000',  # Sampling rate
        '-acodec', 'pcm_s16le',  # Audio codec
        '-af', 'highpass=f=200,lowpass=f=3000',  # Audio filter graph
        '-f', 'wav',  # Save as WAV file
        '-vn',  # Disable video
        '-y',  # Overwrite output files
        '-loglevel', 'error',  # Suppress logs
        '-'  # Send output to stdout
    ]

    try:
        proc = subprocess.run(command, capture_output=True, check=True)
        if len(proc.stdout) == 0:
            raise mpf.DetectionError.COULD_NOT_READ_DATAFILE.exception(
                'The ffmpeg process exited without error, but failed to produce any audio data.')

        output = bytearray(proc.stdout)
        # If WAVE headers are not fixed, downstream processors may refuse to read
        #  the data, as the file appears to be invalid (maximum wav data size)
        pydub.audio_segment.fix_wav_headers(output)
        return bytes(output)

    except subprocess.CalledProcessError as err:
        error_msg = 'The ffmpeg process exited '
        if err.returncode > 0:
            error_msg += f'with exit code: {err.returncode}.'
        else:
            # When exit code is negative, it is the signal number that
            # caused the process to exit
            error_msg += f'due to signal number: {-err.returncode}.'
        if err.stderr:
            decoded_stderr = err.stderr.decode('utf-8')
            error_msg += f' Error message: {decoded_stderr}'

        if 'does not contain any stream' in error_msg:
            raise mpf.DetectionError.UNSUPPORTED_DATA_TYPE.exception(error_msg) from err
        else:
            raise mpf.DetectionError.COULD_NOT_READ_DATAFILE.exception(error_msg) from err




