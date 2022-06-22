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

import dataclasses
import enum
from typing import Any, Dict, Mapping, NamedTuple, Optional


@dataclasses.dataclass
class ImageLocation:
    x_left_upper: int
    y_left_upper: int
    width: int
    height: int
    confidence: float = -1
    detection_properties: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class VideoTrack:
    start_frame: int
    stop_frame: int
    confidence: float = -1
    frame_locations: Dict[int, ImageLocation] = dataclasses.field(default_factory=dict)
    detection_properties: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class AudioTrack:
    start_time: int
    stop_time: int
    confidence: float = -1
    detection_properties: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class GenericTrack:
    confidence: float = -1
    detection_properties: Dict[str, str] = dataclasses.field(default_factory=dict)



class VideoJob(NamedTuple):
    job_name: str
    data_uri: str
    start_frame: int
    stop_frame: int
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    feed_forward_track: Optional[VideoTrack] = None


class ImageJob(NamedTuple):
    job_name: str
    data_uri: str
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    feed_forward_location: Optional[ImageLocation] = None


class AudioJob(NamedTuple):
    job_name: str
    data_uri: str
    start_time: int
    stop_time: int
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    feed_forward_track: Optional[AudioTrack] = None


class GenericJob(NamedTuple):
    job_name: str
    data_uri: str
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    feed_forward_track: Optional[GenericTrack] = None


@enum.unique
class DetectionError(enum.IntEnum):
    DETECTION_SUCCESS = 0
    OTHER_DETECTION_ERROR_TYPE = 1
    DETECTION_NOT_INITIALIZED = 2
    UNSUPPORTED_DATA_TYPE = 3
    COULD_NOT_OPEN_DATAFILE = 4
    COULD_NOT_READ_DATAFILE = 5
    FILE_WRITE_ERROR = 6
    BAD_FRAME_SIZE = 7
    DETECTION_FAILED = 8
    INVALID_PROPERTY = 9
    MISSING_PROPERTY = 10
    MEMORY_ALLOCATION_FAILED = 11
    GPU_ERROR = 12
    NETWORK_ERROR = 13
    COULD_NOT_OPEN_MEDIA = 14
    COULD_NOT_READ_MEDIA = 15

    def exception(self, message: str) -> 'DetectionException':
        return DetectionException(message, self)


class DetectionException(Exception):
    error_code: DetectionError

    def __init__(self,
                 message: str,
                 error_code: DetectionError = DetectionError.OTHER_DETECTION_ERROR_TYPE,
                 *args: Any) -> None:
        super(DetectionException, self).__init__(message, error_code, *args)
        if isinstance(error_code, DetectionError):
            self.error_code = error_code
        else:
            self.error_code = DetectionError.OTHER_DETECTION_ERROR_TYPE

    def __str__(self):
        if len(self.args) == 2 and self.args[1] == self.error_code:
            return f'{self.args[0]} (DetectionError.{self.error_code.name})'
        else:
            return super().__str__()


