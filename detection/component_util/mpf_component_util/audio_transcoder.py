#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2020 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2020 The MITRE Corporation                                      #
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

from io import BytesIO
import os
import subprocess
from typing import Optional

from pydub.audio_segment import fix_wav_headers

def transcode_to_wav(filepath: str, start_time: float = 0, stop_time: Optional[float] = None) -> bytes:
    """
    Transcodes the audio contained in filepath (can be an audio or video file)
    from from start_time to stop_time to WAVE format using ffmpeg, and returns it as a byte string (read from a BytesIO object).

    :param filepath: The path to the file (job.data_uri).
    :param start_time: The time (in milliseconds) associated with the beginning of audio segment. Default 0.
    :param stop_time: The time (in milliseconds) associated with the end of the audio segment. To go to the end of the file, pass None. Default None.
    """
    # Confirm that input file exists
    if not os.path.exists(filepath):
        raise ValueError("Input file does not exist: " + filepath)

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
        command += ['-ss', str(start_time/1000.0)]  # Audio clip start time
    if stop_time and stop_time > 0:
        command += ['-to', str(stop_time/1000.0)]   # Audio clip end time
    command += [
        '-ac', '1',                                 # Channels
        '-ar', '8000',                              # Sampling rate
        '-acodec', 'pcm_s16le',                     # Audio codec
        '-af', 'highpass=f=200,lowpass=f=3000',     # Audio filter graph
        '-f', 'wav',                                # Save as WAV file
        '-vn',                                      # Disable video
        '-y',                                       # Overwrite output files
        '-loglevel', 'error',                       # Suppress logs
        '-'                                         # Send output to stdout
    ]

    # Call ffmpeg
    try:
        proc = subprocess.Popen(
            command,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except OSError as err:
        # 2 corresponds to errno.ENOENT (no such file or directory)
        if err.errno == 2:
            raise EnvironmentError(
                err.errno,
                'ffmpeg does not appear to be installed'
            )
        else:
            raise err

    # Wait for ffmpeg to complete, get stdout and stderr
    p_out, p_err = proc.communicate()

    # If we get a nonzero exit status, raise exception
    exit_code = proc.returncode
    if exit_code != 0:
        error_msg = 'The ffmpeg process exited '
        if exit_code > 0:
            error_msg += 'with exit code: {c:d}.'.format(c=exit_code)
        else:
            # When exit code is negative, it is the signal number that
            # caused the process to exit
            error_msg += 'due to signal number: {c:d}.'.format(c=-exit_code)
            exit_code = 128 - exit_code
        if p_err:
            error_msg += ' Error message: {e:s}'.format(e=p_err.decode('utf-8'))
        raise EnvironmentError(exit_code, error_msg)
    elif len(p_out) == 0:
        error_msg = "The ffmpeg process exited without error, but failed to produce any audio data."
        raise ValueError(error_msg)

    p_out = bytearray(p_out)

    # If WAVE headers are not fixed, downstream processors may refuse to read
    #  the data, as the file appears to be invalid (maximum wav data size)
    fix_wav_headers(p_out)

    bytes_io = BytesIO(p_out)
    bytes_io.seek(0)
    return bytes_io.read()
