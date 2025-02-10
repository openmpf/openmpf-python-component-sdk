#!/usr/bin/env python3
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

import unittest
import sys
import pathlib
import logging

import mpf_subject_api as mpf_sub
import mpf_component_api as mpf

logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from subject_component import SubjectExampleComponent


class TestSubjectComponent(unittest.TestCase):

    def test_component(self):
        face_track = mpf.VideoTrack(0, 100, 0.9, {}, {})
        face_track_id = mpf_sub.TrackId('face_track1')
        video_job1 = mpf_sub.VideoDetectionJobResults(
            '/path/to/media',
            mpf_sub.MediaId('media_id'),
            'Test algorithm',
            mpf_sub.DetectionComponentType('FACE'),
            {},
            {},
            {face_track_id: face_track})

        object_track = mpf.VideoTrack(0, 100, 0.8, {}, {'CLASSIFICATION': 'person'})
        object_track_id = mpf_sub.TrackId('object_track_1')
        video_job2 = mpf_sub.VideoDetectionJobResults(
            '/path/to/media',
            mpf_sub.MediaId('media_id'),
            'Test algorithm',
            mpf_sub.DetectionComponentType('CLASS'),
            {},
            {},
            {object_track_id: object_track}) # tracks

        job = mpf_sub.SubjectTrackingJob('Test job', {}, (video_job1, video_job2), (), (), ())
        component = SubjectExampleComponent()

        subject_results = component.get_subjects(job)

        entities = subject_results.entities[mpf_sub.EntityType('example entity type')]
        self.assertEqual(2, len(entities))
        entity1, entity2 = entities

        if track_is_in_entity(face_track_id, entity1):
            self.assertTrue(track_is_in_entity(object_track_id, entity2))
        else:
            self.assertTrue(track_is_in_entity(object_track_id, entity1))
            self.assertTrue(track_is_in_entity(face_track_id, entity2))


def track_is_in_entity(track_id: mpf_sub.TrackId, entity: mpf_sub.Entity):
    return any(track_id in track_group for track_group in entity.tracks.values())


if __name__ == '__main__':
    unittest.main(verbosity=2)
