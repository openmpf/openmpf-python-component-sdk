#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2022 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2022 The MITRE Corporation                                      #
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
from typing import Optional, List, Tuple

import pydub.audio_segment

import mpf_component_api as mpf


_ERROR_MESSAGE_MAX_LENGTH = 5000


def transcode_to_wav(
        filepath: str,
        *,
        highpass: Optional[int] = 200,
        lowpass: Optional[int] = 3000,
        start_time: Optional[int] = None,
        stop_time: Optional[int] = None,
        segments: Optional[List[Tuple[float, float]]] = None) -> bytes:
    """
    Transcodes the audio contained in filepath (can be an audio or video file)
    from start_time to stop_time to WAVE format using ffmpeg, and returns it as
    a bytes object

    :param filepath: The path to the file (job.data_uri).
    :param highpass: Apply a double-pole high-pass filter with 3dB point
        frequency. The filter roll off at 6dB per pole per octave (20dB per
        pole per decade). Pass None to disable.
    :param lowpass: Apply a double-pole low-pass filter with 3dB point
        frequency. The filter roll off at 6dB per pole per octave (20dB per
        pole per decade). Pass None to disable.
    :param start_time: The time (in milliseconds) associated with the beginning
        of audio segment. Default None.
    :param stop_time: The time (in milliseconds) associated with the end of the
        audio segment. To go to the end of the file, pass None. Default None.
    :param segments: A list of segments to trim and concatenate from the audio
        in advance of transcoding. Each segment is represented by a tuple pair
        of start and stop time (in milliseconds). If either the start or stop
        time in a pair is None, the segment will extend to the start or end of
        the audio, respectively.
        If start_time and/or stop_time are supplied, the segments should be
        relative to those times; i.e. the start_time will be added to each
        segment time, and only segments within the start_time-stop_time span
        will be included in the output.
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
    if segments is None:
        if start_time is not None and start_time > 0:
            command += ['-ss', str(start_time / 1000.0)]  # Audio clip start time
        if stop_time is not None and stop_time > 0:
            command += ['-to', str(stop_time / 1000.0)]  # Audio clip end time
    else:
        # Construct complex filter to trim and concatenate audio
        trim_str_components = []
        concat_str_components = []
        for i, (t0, t1) in enumerate(segments):
            # Offset by start_time so that segments are relative to the full
            #  audio file (not the trimmed waveform)
            if start_time is not None:
                t0 = t0 + start_time if t0 is not None else start_time
                t1 = t1 + start_time if t1 is not None else t1

            if stop_time is not None:
                # If stop_time is before the segment, skip it
                if t0 is not None and t0 >= stop_time:
                    continue

                # Limit to stop_time
                if t1 is None or t1 > stop_time:
                    t1 = stop_time

            # If either start or stop is not included, segment extends to limit
            tr = []
            if t0 is not None:
                tr.append(f"start={t0 / 1000.0:f}")
            if t1 is not None:
                tr.append(f"end={t1 / 1000.0:f}")
            tr = ':'.join(tr)
            trim_str_components.append(f"[0:a]atrim={tr},asetpts=PTS-STARTPTS[a{i}];")
            concat_str_components.append(f"[a{i}]")
        trim_str = ''.join(trim_str_components)
        concat_str = ''.join(concat_str_components) + f"concat=n={len(segments)}:v=0:a=1"
        complex_str = trim_str + concat_str

        # Apply filtergraph unless highpass or lowpass both None
        if not (highpass is None and lowpass is None):
            filtergraph = []
            if highpass is not None:
                filtergraph.append(f'highpass=f={highpass}')
            if lowpass is not None:
                filtergraph.append(f'lowpass=f={lowpass}')
            complex_str += "[unf];[unf]" + ','.join(filtergraph)

        complex_str += "[out]"
        command += ['-filter_complex', complex_str, '-map', '[out]']

    command += [
        '-ac', '1',  # Channels
        '-ar', '8000',  # Sampling rate
        '-acodec', 'pcm_s16le',  # Audio codec
    ]

    # Apply filtergraph (can't use -af and -filter_complex together)
    if segments is None and not (highpass is None and lowpass is None):
        filtergraph = []
        if highpass is not None:
            filtergraph.append(f'highpass=f={highpass}')
        if lowpass is not None:
            filtergraph.append(f'lowpass=f={lowpass}')
        command += ['-af', ','.join(filtergraph)]

    command += [
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
                'The ffmpeg process exited without error, but failed to produce'
                ' any audio data.')

        output = bytearray(proc.stdout)
        # If WAVE headers are not fixed, downstream processors may refuse to
        #  read the data, as the file appears to be invalid
        #  (maximum wav data size)
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

        if len(error_msg) > _ERROR_MESSAGE_MAX_LENGTH:
            error_msg = error_msg[:_ERROR_MESSAGE_MAX_LENGTH] + ' <truncated>'

        if 'does not contain any stream' in error_msg:
            raise mpf.DetectionError.UNSUPPORTED_DATA_TYPE.exception(error_msg) from err
        else:
            raise mpf.DetectionError.COULD_NOT_READ_DATAFILE.exception(error_msg) from err
