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

import dataclasses
import enum
import logging
import logging.handlers
import os
import sys
from typing import Any, Mapping, NamedTuple, Optional, Dict


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
    feed_forward_location: Optional[ImageLocation]


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
    UNRECOGNIZED_DATA_TYPE = 3
    UNSUPPORTED_DATA_TYPE = 4
    INVALID_DATAFILE_URI = 5
    COULD_NOT_OPEN_DATAFILE = 6
    COULD_NOT_READ_DATAFILE = 7
    FILE_WRITE_ERROR = 8
    IMAGE_READ_ERROR = 9
    BAD_FRAME_SIZE = 10
    BOUNDING_BOX_SIZE_ERROR = 11
    INVALID_FRAME_INTERVAL = 12
    INVALID_START_FRAME = 13
    INVALID_STOP_FRAME = 14
    DETECTION_FAILED = 15
    DETECTION_TRACKING_FAILED = 16
    INVALID_PROPERTY = 17
    MISSING_PROPERTY = 18
    PROPERTY_IS_NOT_INT = 19
    PROPERTY_IS_NOT_FLOAT = 20
    INVALID_ROTATION = 21
    MEMORY_ALLOCATION_FAILED = 22
    GPU_ERROR = 23

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



def configure_logging(log_file_name: str, debug: bool = False) -> logging.Logger:
    # Change default level names to match what WFM expects
    # Change default level name for logger.warn and logger.warning from 'WARNING' to 'WARN'
    logging.addLevelName(logging.WARN, 'WARN')
    # Change default level name for logger.fatal and logger.critical from 'CRITICAL' to 'FATAL'
    logging.addLevelName(logging.FATAL, 'FATAL')

    logger = logging.getLogger(_get_log_name(log_file_name))
    logger.propagate = False
    if debug:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
    else:
        logger.setLevel(logging.INFO)
        handler = logging.handlers.TimedRotatingFileHandler(_get_full_log_path(log_file_name), when='midnight')

    # Example log line: 2018-05-03 14:41:11,703 INFO  [test_component.py:44] - Logged message
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)d] - %(message)s'))
    logger.addHandler(handler)
    return logger


def _get_full_log_path(filename):
    log_dir = os.path.expandvars('$MPF_LOG_PATH/$THIS_MPF_NODE/log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, filename)
    return os.path.expandvars(log_path)


def _get_log_name(filename):
    log_name, _ = os.path.splitext(os.path.basename(filename if filename else ''))
    return log_name if log_name else 'component_logger'
