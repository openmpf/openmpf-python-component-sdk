#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2018 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2018 The MITRE Corporation                                      #
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

import test_util
test_util.add_local_component_libs_to_sys_path()

import unittest
import mpf_component_api as mpf
import mpf_component_util as mpf_util


def is_all_same_color(image, color_tuple):
    return (image == color_tuple).all()


def is_all_black(image):
    return is_all_same_color(image, (0, 0, 0))


def is_all_white(image):
    return is_all_same_color(image, (255, 255, 255))


def images_equal(im1, im2):
    return (im1 == im2).all()


# Black regions middle: Rect(80, 50, 160, 100) and  bottom right: Rect(300, 170, 20, 30)


class TestImageReader(unittest.TestCase):

    def test_image_load(self):
        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'), {}, {}, None)
        image_reader = mpf_util.ImageReader(job)
        image = image_reader.get_image()
        image_size = mpf_util.Size.from_frame(image)
        self.assertEqual((320, 200), image_size)


    def test_image_crop(self):
        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'), {
            'SEARCH_REGION_ENABLE_DETECTION': 'true',
            'SEARCH_REGION_TOP_LEFT_X_DETECTION': '80',
            'SEARCH_REGION_TOP_LEFT_Y_DETECTION': '50',
            'SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION': '240',
            'SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION': '150'
        }, {}, None)

        image_reader = mpf_util.ImageReader(job)
        image = image_reader.get_image()
        image_size = mpf_util.Size.from_frame(image)
        self.assertEqual((160, 100), image_size)

        # Check if all black
        self.assertTrue(is_all_black(image))

        self._assert_reverse_transform(image_reader, (0, 0, 160, 100), (80, 50, 160, 100))


        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'), {
            'SEARCH_REGION_ENABLE_DETECTION': 'true',
            'SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION': '40'
        }, {}, None)

        image_reader = mpf_util.ImageReader(job)
        image = image_reader.get_image()
        image_size = mpf_util.Size.from_frame(image)
        self.assertEqual((320, 40), image_size)

        # Check if all white
        self.assertTrue((image == (255, 255, 255)).all())
        self.assertTrue(is_all_white(image))


    def test_frame_flip(self):
        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'), {}, {}, None)
        original_image_reader = mpf_util.ImageReader(job)
        original_image = original_image_reader.get_image()
        original_white_corner = original_image[170:, :20]
        original_black_corner = original_image[170:, 300:]

        self.assertEqual((320, 200), mpf_util.Size.from_frame(original_image))
        self.assertTrue(is_all_white(original_white_corner))
        self.assertTrue(is_all_black(original_black_corner))

        self._assert_reverse_transform(original_image_reader, (0, 170, 20, 30), (0, 170, 20, 30))

        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'),
                           {'HORIZONTAL_FLIP': 'True'}, {}, None)
        flipped_image_reader = mpf_util.ImageReader(job)
        flipped_image = flipped_image_reader.get_image()

        self.assertEqual(original_image.shape, flipped_image.shape)
        flipped_black_corner = flipped_image[170:, :20]
        flipped_white_corner = flipped_image[170:, 300:]

        self.assertTrue(is_all_black(flipped_black_corner))
        self.assertTrue(is_all_white(flipped_white_corner))
        self.assertTrue(images_equal(original_black_corner, flipped_black_corner))
        self.assertTrue(images_equal(original_white_corner, flipped_white_corner))

        self._assert_reverse_transform(flipped_image_reader, (0, 170, 20, 30), (300, 170, 20, 30))


    def test_rotation(self):
        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'),
                           {'ROTATION': '90'}, {}, None)
        image_reader = mpf_util.ImageReader(job)
        image = image_reader.get_image()

        self.assertEqual((200, 320), mpf_util.Size.from_frame(image))
        self.assertTrue(is_all_black(image[300:, :30]))
        self._assert_reverse_transform(image_reader, (0, 300, 30, 20), (300, 170, 20, 30))



    def _assert_reverse_transform(self, image_reader, pre_transform_values, post_transform_values):
        il = mpf.ImageLocation(*pre_transform_values)
        expected_il = mpf.ImageLocation(*post_transform_values)
        image_reader.reverse_transform(il)
        self.assertEqual(expected_il, il)


    def test_combined(self):
        job_properties = {
            'HORIZONTAL_FLIP': 'True', 'ROTATION': '270',
            'SEARCH_REGION_ENABLE_DETECTION': 'true',
            'SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION': '80',
            'SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION': '100'
        }

        job = mpf.ImageJob('Test Job', test_util.get_data_file_path('test_img.png'),
                           job_properties, {}, None)

        component = ImageReaderMixinComponent(self)
        results = list(component.get_detections_from_image(job))
        self.assertEqual(4, len(results))
        self.assertEqual((300, 170, 20, 30), mpf_util.Rect.from_image_location(results[0]))
        self.assertEqual((220, 120, 20, 30), mpf_util.Rect.from_image_location(results[1]))
        self.assertEqual((300, 120, 20, 30), mpf_util.Rect.from_image_location(results[2]))
        self.assertEqual((220, 170, 20, 30), mpf_util.Rect.from_image_location(results[3]))



class ImageReaderMixinComponent(mpf_util.ImageReaderMixin, object):
    def __init__(self, test_obj):
        self._test = test_obj

    def get_detections_from_image_reader(self, image_job, image_reader):
        test = self._test

        image = image_reader.get_image()
        top_left_corner = image[:20, :30]
        test.assertTrue(is_all_black(top_left_corner))
        bottom_right_corner = image[80:, 50:]
        test.assertTrue(is_all_black(bottom_right_corner))

        top_right_corner = image[:20, 50:]
        test.assertTrue(is_all_white(top_right_corner))
        bottom_left_corner = image[80:, :30]
        test.assertTrue(is_all_white(bottom_left_corner))

        for corner in (top_left_corner, bottom_right_corner, top_right_corner, bottom_left_corner):
            test.assertEqual(mpf_util.Size(30, 20), mpf_util.Size.from_frame(corner))

        yield mpf.ImageLocation(0, 0, 30, 20)
        yield mpf.ImageLocation(50, 80, 30, 20)
        yield mpf.ImageLocation(50, 0, 30, 20)
        yield mpf.ImageLocation(0, 80, 30, 20)