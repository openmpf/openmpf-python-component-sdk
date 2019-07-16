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

logger = mpf.configure_logging('audio-transcoder.log', __name__ == '__main__')

def transcode_audio_to_wav(audio_in_path, audio_out_path):
    """
    Transcodes the audio from audio_in_path and writes it to audio_out_path as
    a .wav file

    :param audio_in_path: The path to the input audio file (audio_job.data_uri).
    :param audio_out_path: The path at which to save the transcoded audio.
    """
    logger.info((
            'Transcoding audio from {audio_in_path:s} into {audio_out_path:s}'
        ).format(
            audio_in_path=audio_in_path,
            audio_out_path=audio_out_path
        )
    )

    # Resolve symbolic paths if necessary
    audio_in_path = os.path.realpath(audio_in_path)
    audio_out_path = os.path.realpath(audio_out_path)

    # Confirm that input file exists
    if not os.path.isfile(audio_in_path):
        raise ValueError("Input file does not exist: " + audio_in_path)

    # Confirm that output file can be created
    out_dir = os.path.split(audio_out_path)[0]
    if not os.path.isdir(out_dir):
        raise ValueError("Output directory does not exist: " + out_dir)

    # Construct ffmpeg call
    # Note: ffmpeg options apply to the next specified file. Order matters.
    command = (
        'ffmpeg', '-i', audio_in_path,
        '-ac', '1',                                 # Channels
        '-ar', '16000',                             # Sampling rate
        '-acodec', 'pcm_s16le',                     # Audio codec
        '-af', 'highpass=f=200,lowpass=f=3000',     # Audio filter graph
        '-f', 'wav',                                # Save as WAV file
        audio_out_path,
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
    if not os.path.isfile(audio_out_path):
        error_str = "Unable to transcode input file: " + audio_in_path
        logger.error(error_str)
        raise mpf.DetectionException(
            error_str,
            mpf.DetectionError.OTHER_DETECTION_ERROR_TYPE
        )
