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

import itertools
import logging
import uuid

import mpf_subject_api as mpf_sub

logger = logging.getLogger('SubjectExampleComponent')

class SubjectExampleComponent:
    def __init__(self) -> None:
        logger.info('Created instance of SubjectExampleComponent.')

    def get_subjects(self, job: mpf_sub.SubjectTrackingJob) -> mpf_sub.SubjectTrackingResults:
        logger.info(f'Received job: {job.job_name}')
        jobs = itertools.chain(job.video_jobs, job.image_jobs)
        entities = []
        relationships = []
        for detection_job in jobs:
            for track_id in detection_job.results:
                entity = get_single_track_entity(track_id)
                entities.append(entity)
                relationships.append(get_relationship(entity, detection_job.media_id))

        logger.info(f'Sending response with {len(entities)} entities.')
        return mpf_sub.SubjectTrackingResults(
                {mpf_sub.EntityType("example entity type"): entities},
                {mpf_sub.RelationshipType("example relationship"): relationships},
                {"TEST_PROP": "TEST_VAL"})


def get_single_track_entity(track_id: mpf_sub.TrackId) -> mpf_sub.Entity:
    return mpf_sub.Entity(
            uuid.uuid4(), 1, {mpf_sub.TrackType("example track type"): (track_id,)})


def get_relationship(entity: mpf_sub.Entity, media_id: mpf_sub.MediaId) -> mpf_sub.Relationship:
    return mpf_sub.Relationship((entity.id,), (mpf_sub.MediaReference(media_id, (0,)),))
