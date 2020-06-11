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

from . import test_util
test_util.add_local_component_libs_to_sys_path()

import typing
import unittest

import cv2
import numpy as np

import mpf_component_api as mpf
import mpf_component_util as mpf_util
from mpf_component_util.frame_transformers.affine_frame_transformer import AffineFrameTransformer
from mpf_component_util.frame_transformers.frame_transformer import NoOpTransformer
from mpf_component_util.frame_transformers import frame_transformer_factory, SearchRegion, RegionEdge




class TestAffineTransformer(unittest.TestCase):

    def test_can_handle_rotated_detection_near_middle(self):
        self.verify_correctly_rotated('20deg-bounding-box.png',
                                      mpf.ImageLocation(116, 218, 100, 40, -1, dict(ROTATION='20')))


    def test_can_handle_rotated_detection_touching_corner(self):
        self.verify_correctly_rotated('30deg-bounding-box-top-left-corner.png',
                                      mpf.ImageLocation(0, 51, 100, 40, -1, dict(ROTATION='30.5')))

        self.verify_correctly_rotated('60deg-bounding-box-top-left-corner.png',
                                      mpf.ImageLocation(0, 86, 100, 40, -1, dict(ROTATION='60')))

        self.verify_correctly_rotated('200deg-bounding-box-top-left-corner.png',
                                      mpf.ImageLocation(108, 38, 100, 40, -1, dict(ROTATION='200')))

        self.verify_correctly_rotated('20deg-bounding-box-bottom-left-corner.png',
                                      mpf.ImageLocation(0, 367, 30, 120, -1, dict(ROTATION='20')))

        self.verify_correctly_rotated('160deg-bounding-box-bottom-right-corner.png',
                                      mpf.ImageLocation(599, 480, 30, 120, -1, dict(ROTATION='160')))

        self.verify_correctly_rotated('260deg-bounding-box-top-right-corner.png',
                                      mpf.ImageLocation(640, 21, 30, 120, -1, dict(ROTATION='260')))

        self.verify_correctly_rotated('270deg-bounding-box-top-right-corner.png',
                                      mpf.ImageLocation(640, 0, 30, 120, -1, dict(ROTATION='270')))



    def verify_correctly_rotated(self, file_name, feed_forward_detection):
        full_path = test_util.get_data_file_path('rotation/' + file_name)
        job = mpf.ImageJob('Test', full_path, dict(FEED_FORWARD_TYPE='REGION'), {}, feed_forward_detection)
        image_reader = mpf_util.ImageReader(job)
        img = image_reader.get_image()

        height, width = img.shape[:2]

        self.assertEqual(feed_forward_detection.width, width)
        self.assertEqual(feed_forward_detection.height, height)

        self.assert_image_color(img, (255, 0, 0))

        detection = mpf.ImageLocation(0, 0, width, height)
        image_reader.reverse_transform(detection)
        self.assert_detections_same_location(detection, feed_forward_detection)



    def assert_image_color(self, img, color):
        # Color of pixels along edges gets blended with nearby pixels during interpolation.
        rows, cols = img.shape[:2]
        for row in range(1, rows):
            for col in range(1, cols):
                self.assertTrue(np.all(closest_color(img[row, col]) == color))


    def assert_detections_same_location(self, il1, il2):
        self.assertEqual(il1.x_left_upper, il2.x_left_upper)
        self.assertEqual(il1.y_left_upper, il2.y_left_upper)
        self.assertEqual(il1.width, il2.width)
        self.assertEqual(il1.height, il2.height)



    def test_full_frame_non_orthogonal_rotation(self):
        width = 640
        height = 480

        # noinspection PyTypeChecker
        img = np.full(shape=(height, width, 3), fill_value=(255, 255, 255), dtype=np.uint8)
        transformer = AffineFrameTransformer.rotate_full_frame(
            20, False, NoOpTransformer((width, height)))

        transformed_img = transformer.transform_frame(img, 0)

        num_white = count_matching_pixels(transformed_img, (255, 255, 255))

        area = width * height
        # Color of pixels along edges gets blended with nearby pixels during interpolation.
        self.assertGreaterEqual(num_white, area - height - width)
        self.assertLessEqual(num_white, area)

        self.assertEqual(670, transformed_img.shape[0])
        self.assertEqual(765, transformed_img.shape[1])


    def test_full_frame_orthogonal_rotation(self):
        size = mpf_util.Size(640, 480)

        # noinspection PyTypeChecker
        img = np.full(shape=(size.height, size.width, 3), fill_value=(255, 255, 255), dtype=np.uint8)


        for rotation in (0, 90, 180, 270):
            transformer = AffineFrameTransformer.rotate_full_frame(rotation, False, NoOpTransformer(size))
            transformed_img = transformer.transform_frame(img, 0)

            num_white = count_matching_pixels(transformed_img, (255, 255, 255))
            self.assertEqual(num_white, size.area)

            if rotation in (90, 270):
                self.assertEqual((size.height, size.width), mpf_util.Size.from_frame(transformed_img))
            else:
                self.assertEqual(size, mpf_util.Size.from_frame(transformed_img))


    def test_feed_forward_exact_region(self):
        ff_track = mpf.VideoTrack(
            0, 2, -1,
            {
                0: mpf.ImageLocation(60, 300, 100, 40, -1, dict(ROTATION='260')),
                1: mpf.ImageLocation(160, 350, 130, 20, -1, dict(ROTATION='60')),
                2: mpf.ImageLocation(260, 340, 60, 60, -1, dict(ROTATION='20'))
            }, {})
        job = mpf.VideoJob('Test', test_util.get_data_file_path('rotation/feed-forward-rotation-test.png'),
                           ff_track.start_frame, ff_track.stop_frame, dict(FEED_FORWARD_TYPE='REGION'), {}, ff_track)

        test_img = cv2.imread(job.data_uri)

        transformer = frame_transformer_factory.get_transformer(job, mpf_util.Size.from_frame(test_img))

        for frame_number, ff_detection in ff_track.frame_locations.items():
            frame = transformer.transform_frame(test_img, frame_number)
            frame_size = mpf_util.Size.from_frame(frame)
            self.assertEqual(frame_size, (ff_detection.width, ff_detection.height))
            self.assert_image_color(frame, (255, 0, 0))

            size_as_tuple = typing.cast(typing.Tuple[int, int], frame_size)
            new_detection = mpf.ImageLocation(0, 0, *size_as_tuple)
            transformer.reverse_transform(new_detection, frame_number)
            self.assert_detections_same_location(new_detection, ff_detection)


    def test_feed_forward_superset_region(self):
        ff_track = mpf.VideoTrack(
            0, 2, -1,
            {
                0: mpf.ImageLocation(60, 300, 100, 40, -1, dict(ROTATION='260')),
                1: mpf.ImageLocation(160, 350, 130, 20, -1, dict(ROTATION='60')),
                2: mpf.ImageLocation(260, 340, 60, 60, -1, dict(ROTATION='20'))
            }, {})

        for rotation in range(0, 361, 20):
            job = mpf.VideoJob('Test', test_util.get_data_file_path('rotation/feed-forward-rotation-test.png'),
                               ff_track.start_frame, ff_track.stop_frame,
                               dict(FEED_FORWARD_TYPE='SUPERSET_REGION', ROTATION=str(rotation)), {}, ff_track)
            expected_min_num_blue = 0
            expected_max_num_blue = 0
            for il in ff_track.frame_locations.values():
                area = il.width * il.height
                perimeter = 2 * il.width + 2 * il.height
                expected_min_num_blue += area - perimeter
                expected_max_num_blue += area + perimeter

            frame = next(mpf_util.VideoCapture(job))
            actual_num_blue = count_matching_pixels(frame, (255, 0, 0))
            # Color of pixels along edges gets blended with nearby pixels during interpolation.
            self.assertLessEqual(actual_num_blue, expected_max_num_blue)
            self.assertGreaterEqual(actual_num_blue, expected_min_num_blue)


    def test_reverse_transform_with_flip(self):
        frame_width = 100
        frame_height = 200

        transformer = AffineFrameTransformer.rotate_full_frame(0, True, NoOpTransformer((frame_width, frame_height)))

        # Test without existing flip
        detection = mpf.ImageLocation(10, 20, 40, 50)
        detection_reversed = mpf.ImageLocation(10, 20, 40, 50)
        transformer.reverse_transform(detection_reversed, 0)

        self.assertEqual(frame_width - detection.x_left_upper - 1, detection_reversed.x_left_upper)
        self.assertEqual(detection.y_left_upper, detection_reversed.y_left_upper)
        self.assertEqual(detection.width, detection_reversed.width)
        self.assertEqual(detection.height, detection_reversed.height)
        self.assertIn('HORIZONTAL_FLIP', detection_reversed.detection_properties)
        self.assertTrue(mpf_util.get_property(detection_reversed.detection_properties, 'HORIZONTAL_FLIP', False))

        # Test with existing flip
        detection = mpf.ImageLocation(10, 20, 40, 50, -1, dict(HORIZONTAL_FLIP='True'))
        detection_reversed = mpf.ImageLocation(10, 20, 40, 50, -1, dict(HORIZONTAL_FLIP='True'))
        transformer.reverse_transform(detection_reversed, 0)

        self.assertEqual(frame_width - detection.x_left_upper - 1, detection_reversed.x_left_upper)
        self.assertEqual(detection.y_left_upper, detection_reversed.y_left_upper)
        self.assertEqual(detection.width, detection_reversed.width)
        self.assertEqual(detection.height, detection_reversed.height)
        self.assertNotIn('HORIZONTAL_FLIP', detection_reversed.detection_properties)


    def test_normalize_angle(self):
        angle1 = 20.5
        angle2 = 380.5
        angle3 = -339.5
        angle4 = -699.5
        angle5 = -1059.5

        self.assertEqual(angle1, mpf_util.normalize_angle(angle1))
        self.assertEqual(angle1, mpf_util.normalize_angle(angle2))
        self.assertEqual(angle1, mpf_util.normalize_angle(angle3))
        self.assertEqual(angle1, mpf_util.normalize_angle(angle4))
        self.assertEqual(angle1, mpf_util.normalize_angle(angle5))

        self.assertTrue(mpf_util.rotation_angles_equal(angle1, angle1))
        self.assertTrue(mpf_util.rotation_angles_equal(angle1, angle2))
        self.assertTrue(mpf_util.rotation_angles_equal(angle1, angle3))
        self.assertTrue(mpf_util.rotation_angles_equal(angle1, angle4))
        self.assertTrue(mpf_util.rotation_angles_equal(angle1, angle5))

        self.assertEqual(0, mpf_util.normalize_angle(0))
        self.assertEqual(0, mpf_util.normalize_angle(360))



    def test_search_region_with_orthogonal_rotation(self):
        absolute_props = dict(
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_TOP_LEFT_X_DETECTION='100',
            SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='50')

        percentage_props = dict(
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_TOP_LEFT_X_DETECTION='50%',
            SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='50%')

        rotate_90_props = dict(
            ROTATION='90',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_TOP_LEFT_X_DETECTION='50',
            SEARCH_REGION_TOP_LEFT_Y_DETECTION='50%')

        rotate_180_props = dict(
            ROTATION='180',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='50%',
            SEARCH_REGION_TOP_LEFT_Y_DETECTION='50%')

        rotate_270_props = dict(
            ROTATION='270',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='50%',
            SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='50%')

        flip_props = dict(
            HORIZONTAL_FLIP='true',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='50%',
            SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='50%')

        rotate_90_and_flip_props = dict(
            ROTATION='90',
            HORIZONTAL_FLIP='true',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='50%',
            SEARCH_REGION_TOP_LEFT_Y_DETECTION='50%')

        rotate_180_and_flip_props = dict(
            ROTATION='180',
            HORIZONTAL_FLIP='true',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_TOP_LEFT_X_DETECTION='50%',
            SEARCH_REGION_TOP_LEFT_Y_DETECTION='50%')

        rotate_270_and_flip_props = dict(
            ROTATION='270',
            HORIZONTAL_FLIP='true',
            SEARCH_REGION_ENABLE_DETECTION='true',
            SEARCH_REGION_TOP_LEFT_X_DETECTION='50%',
            SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='50%')

        prop_sets = (absolute_props, percentage_props, rotate_90_props, rotate_180_props, rotate_270_props,
                     flip_props, rotate_90_and_flip_props, rotate_180_and_flip_props, rotate_270_and_flip_props)

        for props in prop_sets:
            job = mpf.ImageJob('Test', test_util.get_data_file_path('rotation/search-region-test.png'), props, {},
                               None)
            img = mpf_util.ImageReader(job).get_image()
            num_green = count_matching_pixels(img, (0, 255, 0))
            self.assertEqual(5000, img.shape[0] * img.shape[1])
            self.assertEqual(5000, num_green)


    def test_search_region_with_non_orthogonal_rotation(self):
        job = mpf.ImageJob('Test', test_util.get_data_file_path('rotation/20deg-bounding-box.png'),
                           dict(
                               ROTATION='20',
                               SEARCH_REGION_ENABLE_DETECTION='true',
                               SEARCH_REGION_TOP_LEFT_X_DETECTION='199',
                               SEARCH_REGION_TOP_LEFT_Y_DETECTION='245',
                               SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='299',
                               SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='285'),
                           {}, None)
        image_reader = mpf_util.ImageReader(job)
        img = image_reader.get_image()
        self.assert_image_color(img, (255, 0, 0))

        il = mpf.ImageLocation(0, 0, img.shape[1], img.shape[0])
        image_reader.reverse_transform(il)
        self.assertEqual(117, il.x_left_upper)
        self.assertEqual(218, il.y_left_upper)
        self.assertEqual(100, il.width)
        self.assertEqual(40, il.height)
        actual_rotation = mpf_util.get_property(il.detection_properties, 'ROTATION', 0.0)
        self.assertTrue(mpf_util.rotation_angles_equal(20, actual_rotation))


    def test_search_region(self):
        self.assert_search_region_matches_rect(
            (0, 0, 50, 100),
            SearchRegion())

        self.assert_search_region_matches_rect(
            (0, 0, 50, 100),
            SearchRegion(
                RegionEdge.percentage(-1),
                RegionEdge.absolute(-1),
                RegionEdge.percentage(-3),
                RegionEdge.absolute(-4),
            ))

        self.assert_search_region_matches_rect(
            (0, 10, 25, 90),
            SearchRegion(
                RegionEdge.absolute(0),
                RegionEdge.absolute(10),
                RegionEdge.percentage(50),
                RegionEdge.default()
            ))

        self.assert_search_region_matches_rect(
            (0, 0, 50, 100),
            SearchRegion(
                RegionEdge.absolute(0),
                RegionEdge.absolute(0),
                RegionEdge.absolute(10000),
                RegionEdge.absolute(10000)
            ))

        self.assert_search_region_matches_rect(
            (0, 0, 25, 100),
            SearchRegion(
                RegionEdge.absolute(-1),
                RegionEdge.percentage(-10),
                RegionEdge.percentage(50),
                RegionEdge.default()
            ))


    def assert_search_region_matches_rect(self, expected_region, search_region):
        self.assertEqual(expected_region, search_region.get_rect(mpf_util.Size(50, 100)))


    def test_rotate_with_flip_full_frame(self):
        frame_rotation = 345
        job = mpf.ImageJob('test', test_util.get_data_file_path('rotation/hello-world-flip.png'),
                           dict(HORIZONTAL_FLIP='true', ROTATION=str(frame_rotation)), {})

        image_reader = mpf_util.ImageReader(job)
        image = image_reader.get_image()

        il = mpf.ImageLocation(0, 0, image.shape[1], image.shape[0])
        image_reader.reverse_transform(il)

        self.assertEqual(836, il.x_left_upper)
        self.assertEqual(38, il.y_left_upper)
        self.assertEqual(image.shape[1], il.width)
        self.assertEqual(image.shape[0], il.height)
        self.assertEqual('true', il.detection_properties['HORIZONTAL_FLIP'])
        self.assertAlmostEqual(360 - frame_rotation, float(il.detection_properties['ROTATION']))


    def test_rotation_full_frame(self):
        frame_rotation = 15
        job = mpf.ImageJob('test', test_util.get_data_file_path('rotation/hello-world.png'),
                           dict(ROTATION=str(frame_rotation)), {})

        image_reader = mpf_util.ImageReader(job)
        image = image_reader.get_image()

        il = mpf.ImageLocation(0, 0, image.shape[1], image.shape[0])
        image_reader.reverse_transform(il)

        self.assertEqual(-141, il.x_left_upper)
        self.assertEqual(38, il.y_left_upper)
        self.assertEqual(image.shape[1], il.width)
        self.assertEqual(image.shape[0], il.height)
        self.assertNotIn('HORIZONTAL_FLIP', il.detection_properties)
        self.assertAlmostEqual(frame_rotation, float(il.detection_properties['ROTATION']))




def closest_color(sample):
    palette = np.array((
        (0, 0, 0),
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255)
    ))

    dist_to_each_color = np.linalg.norm(palette - sample, axis=1)
    min_dist_idx = dist_to_each_color.argmin()
    return palette[min_dist_idx]


def count_matching_pixels(img, pixel):
    return np.count_nonzero(np.all(img == pixel, axis=2))
