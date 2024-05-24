#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2024 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2024 The MITRE Corporation                                      #
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

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, NamedTuple, Optional, Tuple, Union

import mpf_component_api as mpf
import mpf_component_util as mpf_util

MpfSpeechJob = Union[mpf.AudioJob, mpf.VideoJob]


class NoInBoundsSpeechSegments(Exception):
    def __init__(self, n_early: int, n_late: int):
        self.n_early = n_early
        self.n_late = n_late

    def __str__(self):
        return (
            f"All segments out-of-bounds ({self.n_early} segments before "
            f"job start time, {self.n_late} after job end time)."
        )


class SpeakerInfo(NamedTuple):
    speaker_id: str
    language: str
    language_scores: Dict[str, float]
    speech_segs: List[Tuple[int, int]]
    gender: Optional[str] = None
    gender_score: Optional[float] = None


class DynamicSpeechJobConfig:
    """ Handles job parsing logic for components that may be part of a dynamic
        speech pipeline

    :ivar job_name: Job name
    :ivar target_file: File location of input data
    :ivar start_time: Start time of the audio (in milliseconds)
    :ivar stop_time: Stop time of the audio (in milliseconds)
    :ivar fps: Frames per second for video jobs
    :ivar speaker_id_prefix: Prefix for SPEAKER_ID
    :ivar override_default_language: A default ISO 639-3 language to use when
        languages defined in the speaker are not supported. If the feed-forward
        track does not exist, this is None
    :ivar speaker: The speaker information contained in the feed-forward track
        if feed-forward track exists, otherwise None
    """
    def __init__(self, job: MpfSpeechJob):
        self.job_name = job.job_name
        self.target_file = Path(job.data_uri)
        self.start_time: int
        self.stop_time: Optional[int] = None
        self.fps: Optional[float] = None
        self.speaker_id_prefix: str

        self._add_media_info(job)
        self._add_job_properties(job.job_properties)

        # Properties related to dynamic speech pipelines
        self.speaker: Optional[SpeakerInfo] = None
        self.override_default_language: Optional[str] = None
        if (job.feed_forward_track and
                'VOICED_SEGMENTS' in job.feed_forward_track.detection_properties):
            self._add_feed_forward_properties(job)


    def _add_job_properties(self, job_properties: Mapping[str, str]):
        raise NotImplementedError()


    def _add_media_info(self, job: MpfSpeechJob):
        media_duration = float(job.media_properties.get('DURATION', -1))
        if isinstance(job, mpf.VideoJob):
            start_frame = job.start_frame
            stop_frame = job.stop_frame
            if stop_frame < 0:
                stop_frame = None
            self.speaker_id_prefix = f"{start_frame}-{stop_frame or 'EOF'}-"

            if 'FPS' not in job.media_properties:
                raise mpf.DetectionException(
                    'FPS must be included in video job media properties.',
                    mpf.DetectionError.MISSING_PROPERTY
                )
            self.fps = float(job.media_properties['FPS'])
            fpms = self.fps / 1000.0
            media_frame_count = int(job.media_properties.get('FRAME_COUNT', -1))

            # Convert frame locations to timestamps
            self.start_time = int(start_frame / fpms)

            # The WFM will pass a job stop frame equal to FRAME_COUNT-1 for the
            #  last video segment. We want to use the detected DURATION in such
            #  cases instead to ensure we process the entire audio track.
            #  Only use the job stop frame if it differs from FRAME_COUNT-1.
            if stop_frame is not None and stop_frame < media_frame_count - 1:
                self.stop_time = int(stop_frame / fpms)
            elif media_duration > 0:
                self.stop_time = int(media_duration)
            elif media_frame_count > 0:
                self.stop_time = int(media_frame_count / fpms)
            else:
                self.stop_time = None
        elif isinstance(job, mpf.AudioJob):
            self.start_time = job.start_time
            self.stop_time = job.stop_time
            if self.stop_time < 0:
                self.stop_time = None
            self.speaker_id_prefix = f"{self.start_time}-{self.stop_time or 'EOF'}-"


    def _add_feed_forward_properties(self, job: MpfSpeechJob):
        feed_forward_properties = job.feed_forward_track.detection_properties
        speaker_id = mpf_util.get_property(
            properties=feed_forward_properties,
            key='SPEAKER_ID',
            default_value='0-EOF-1',
            prop_type=str
        )

        gender = mpf_util.get_property(
            properties=feed_forward_properties,
            key='GENDER',
            default_value=None,
            prop_type=str
        )

        gender_score = mpf_util.get_property(
            properties=feed_forward_properties,
            key='GENDER_CONFIDENCE',
            default_value=None,
            prop_type=float
        )

        languages = mpf_util.get_property(
            properties=feed_forward_properties,
            key='SPEAKER_LANGUAGES',
            default_value='',
            prop_type=str
        )

        language_scores = mpf_util.get_property(
            properties=feed_forward_properties,
            key='SPEAKER_LANGUAGE_CONFIDENCES',
            default_value='',
            prop_type=str
        )

        languages = [lab.strip().lower() for lab in languages.split(',')]
        language_scores = [float(s.strip()) for s in language_scores.split(',')]
        language_scores = defaultdict(
            lambda: -1.0,
            zip(languages, language_scores)
        )

        segments_str = mpf_util.get_property(
            properties=feed_forward_properties,
            key='VOICED_SEGMENTS',
            default_value='',
            prop_type=str
        )
        speech_segs = self._parse_segments_str(
            segments_string=segments_str,
            media_start_time=self.start_time,
            media_stop_time=self.stop_time
        )

        language = mpf_util.get_property(
            properties=feed_forward_properties,
            key='LANGUAGE',
            default_value='',
            prop_type=str
        )
        language = language.strip().lower()

        self.override_default_language = mpf_util.get_property(
            properties=feed_forward_properties,
            key='DEFAULT_LANGUAGE',
            default_value='',
            prop_type=str
        )
        self.override_default_language = self.override_default_language.strip().lower()

        self.speaker = SpeakerInfo(
            speaker_id=speaker_id,
            language=language,
            language_scores=language_scores,
            speech_segs=speech_segs,
            gender=gender,
            gender_score=gender_score
        )


    @staticmethod
    def _parse_segments_str(
                segments_string: str,
                media_start_time: int = 0,
                media_stop_time: Optional[int] = None
            ) -> List[Tuple[int, int]]:
        """ Converts a string of the form
                'start_1-stop_1, start_2-stop_2, ..., start_n-stop_n'
            where start_x and stop_x are in milliseconds, to a list of int pairs
        """
        n_early = 0
        n_late = 0
        try:
            segments = []
            start_stops = segments_string.split(",")
            for ss in start_stops:
                start, stop = ss.strip().split("-")
                start = int(start)
                stop = int(stop)

                # Limit to media start and stop times. If entirely
                #  outside the limits, drop the segment
                if media_stop_time is not None and start > media_stop_time:
                    n_late += 1
                    continue
                if stop < media_start_time:
                    n_early += 1
                    continue
                start = max(start, media_start_time)
                if media_stop_time is not None:
                    stop = min(stop, media_stop_time)

                # Offset by media_start_time so that segments are
                #  relative to the transcoded waveform
                start -= media_start_time
                stop -= media_start_time

                segments.append((start, stop))
        except Exception as e:
            raise mpf.DetectionException(
                'Exception raised while parsing voiced segments '
                f'"{segments_string}": {e}',
                mpf.DetectionError.INVALID_PROPERTY
            )

        # If all the voiced segments are outside the time range, signal that
        #  we should halt and return an empty list.
        if not segments:
            raise NoInBoundsSpeechSegments(n_early, n_late)

        return sorted(segments)
