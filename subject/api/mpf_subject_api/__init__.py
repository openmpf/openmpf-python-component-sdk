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

from __future__ import annotations

import collections
import uuid
from dataclasses import dataclass, field
from typing import Collection, Mapping, NamedTuple, NewType, Sequence, TypeVar

import mpf_component_api as mpf

# Examples: subject, vehicle
EntityType = NewType('EntityType', str)

TrackId = NewType('TrackId', str)
# Examples: face, person, truck
TrackType = NewType('TrackType', str)

# Example: proximity
RelationshipType = NewType('RelationshipType', str)

MediaId = NewType('MediaId', str)

DetectionComponentType = NewType('DetectionComponentType', str)

K = TypeVar('K')
V = TypeVar('V')
Multimap = Mapping[K, Collection[V]]


class SubjectTrackingJob(NamedTuple):
    job_name: str
    job_properties: Mapping[str, str]

    video_jobs: Sequence[VideoDetectionJobResults]
    image_jobs: Sequence[ImageDetectionJobResults]
    audio_jobs: Sequence[AudioJobResults]
    generic_jobs: Sequence[GenericJobResults]


class VideoDetectionJobResults(NamedTuple):
    data_uri: str
    media_id: MediaId
    algorithm: str
    component_type: DetectionComponentType
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    # Keys are Hex-encoded hashes
    results: Mapping[TrackId, mpf.VideoTrack]


class ImageDetectionJobResults(NamedTuple):
    data_uri: str
    media_id: MediaId
    algorithm: str
    component_type: DetectionComponentType
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    results: Mapping[TrackId, mpf.ImageLocation]

class AudioJobResults(NamedTuple):
    data_uri: str
    media_id: MediaId
    algorithm: str
    component_type: DetectionComponentType
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    results: Mapping[TrackId, mpf.AudioTrack]


class GenericJobResults(NamedTuple):
    data_uri: str
    media_id: MediaId
    algorithm: str
    component_type: DetectionComponentType
    job_properties: Mapping[str, str]
    media_properties: Mapping[str, str]
    results: Mapping[TrackId, mpf.GenericTrack]


def _default_multimap():
    return collections.defaultdict(list)


@dataclass
class SubjectTrackingResults:
    # Example keys: subject, vehicle
    entities: Multimap[EntityType, Entity] = field(default_factory=_default_multimap)

    # Example keys: proximity
    relationships: Multimap[RelationshipType, Relationship] = field(
            default_factory=_default_multimap)

    properties: Mapping[str, str] = field(default_factory=dict)


@dataclass
class Entity:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    score: float = -1
    # Example keys: face, person, truck
    tracks: Multimap[TrackType, TrackId] = field(default_factory=_default_multimap)
    properties: Mapping[str, str] = field(default_factory=dict)


@dataclass
class Relationship:
    entities: Collection[uuid.UUID] = field(default_factory=list)
    frames: Collection[MediaReference] = field(default_factory=list)
    properties: Mapping[str, str] = field(default_factory=dict)


@dataclass
class MediaReference:
    id: MediaId
    frames: Collection[int] = field(default_factory=list)
