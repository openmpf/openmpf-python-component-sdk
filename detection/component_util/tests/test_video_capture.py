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

import unittest

import cv2

import mpf_component_api as mpf
import mpf_component_util as mpf_util
from mpf_component_util.frame_filters import FeedForwardFrameFilter, IntervalFrameFilter, seek_strategies



class FrameFilterTest(unittest.TestCase):
    def test_calculate_segment_frame_count(self):
        self.assert_segment_frame_count((0, 0, 1), 1)
        self.assert_segment_frame_count((0, 20, 4), 6)
        self.assert_segment_frame_count((0, 20, 3), 7)
        self.assert_segment_frame_count((4, 10, 1), 7)
        self.assert_segment_frame_count((4, 10, 2), 4)
        self.assert_segment_frame_count((4, 10, 3), 3)
        self.assert_segment_frame_count((4, 10, 20), 1)
        self.assert_segment_frame_count((0, 9, 1), 10)
        self.assert_segment_frame_count((0, 9, 2), 5)
        self.assert_segment_frame_count((0, 9, 3), 4)
        self.assert_segment_frame_count((3, 22, 7), 3)
        self.assert_segment_frame_count((3, 22, 4), 5)


    def assert_segment_frame_count(self, filter_args, expected_count):
        for frame_filter in get_filters(filter_args):
            actual_count = frame_filter.get_segment_frame_count()
            self.assertIsInstance(actual_count, int)
            self.assertEqual(expected_count, actual_count)


    def test_map_segment_to_original_frame_position(self):
        self.assert_segment_to_original_frame_position((0, 10, 1), 0, 0)
        self.assert_segment_to_original_frame_position((0, 10, 1), 1, 1)

        self.assert_segment_to_original_frame_position((4, 10, 1), 0, 4)
        self.assert_segment_to_original_frame_position((4, 10, 1), 2, 6)

        self.assert_segment_to_original_frame_position((0, 20, 3), 0, 0)
        self.assert_segment_to_original_frame_position((0, 20, 3), 2, 6)

        self.assert_segment_to_original_frame_position((2, 20, 3), 0, 2)
        self.assert_segment_to_original_frame_position((2, 20, 3), 4, 14)


    def assert_segment_to_original_frame_position(self, filter_args, segment_position, expected_original_position):
        for frame_filter in get_filters(filter_args):
            actual_original_position = frame_filter.segment_to_original_frame_position(segment_position)
            self.assertIsInstance(actual_original_position, int)
            self.assertEqual(expected_original_position, actual_original_position)


    def test_map_original_to_segment_indices(self):
        self.assert_original_to_segment_frame_position((0, 10, 1), 0, 0)
        self.assert_original_to_segment_frame_position((0, 10, 1), 1, 1)

        self.assert_original_to_segment_frame_position((4, 10, 1), 4, 0)
        self.assert_original_to_segment_frame_position((4, 10, 1), 6, 2)

        self.assert_original_to_segment_frame_position((0, 20, 3), 0, 0)
        self.assert_original_to_segment_frame_position((0, 20, 3), 3, 1)

        self.assert_original_to_segment_frame_position((2, 20, 3), 2, 0)
        self.assert_original_to_segment_frame_position((2, 20, 3), 14, 4)


    def assert_original_to_segment_frame_position(self, filter_args, original_position, expected_segment_position):
        for frame_filter in get_filters(filter_args):
            actual_segment_position = frame_filter.original_to_segment_frame_position(original_position)
            self.assertIsInstance(actual_segment_position, int)
            self.assertEqual(expected_segment_position, actual_segment_position)


    def test_get_segment_duration(self):
        self.assert_segment_duration((0, 9, 100), 10, 1, 0.1)
        self.assert_segment_duration((0, 9, 100), 30, 1 / 3, 1 / 30)
        self.assert_segment_duration((0, 199, 100), 10, 20, 10.1)
        self.assert_segment_duration((0, 149, 100), 10, 15, 10.1)

        self.assert_segment_duration((7, 16, 100), 10, 1, 0.1)
        self.assert_segment_duration((7, 16, 100), 30, 1 / 3, 1 / 30)
        self.assert_segment_duration((7, 206, 100), 10, 20, 10.1)
        self.assert_segment_duration((7, 156, 100), 10, 15, 10.1)


    def assert_segment_duration(self, filter_args, original_frame_rate,
                                expected_interval_duration, expected_feed_forward_duration):

        interval_filter, ff_filter = get_filters(filter_args)
        self.assertAlmostEqual(expected_interval_duration, interval_filter.get_segment_duration(original_frame_rate))
        self.assertAlmostEqual(expected_feed_forward_duration, ff_filter.get_segment_duration(original_frame_rate))



    def test_calculate_segment_frame_rate(self):
        self.assert_segment_frame_rate((0, 9, 1), 30, 30)
        self.assert_segment_frame_rate((100, 9000, 1), 30, 30)

        self.assert_segment_frame_rate((0, 9, 2), 15, 50 / 3)
        self.assert_segment_frame_rate((0, 10, 2), 180 / 11, 180 / 11)
        self.assert_segment_frame_rate((1, 12, 2), 15, 180 / 11)

        self.assert_segment_frame_rate((0, 8, 3), 10, 90 / 7)
        self.assert_segment_frame_rate((0, 9, 3), 12, 12)


    def assert_segment_frame_rate(self, filter_args, expected_interval_frame_rate, expected_feed_forward_frame_rate):
        interval_filter, ff_filter = get_filters(filter_args)
        self.assertAlmostEqual(expected_interval_frame_rate, interval_filter.get_segment_frame_rate(30))
        self.assertAlmostEqual(expected_feed_forward_frame_rate, ff_filter.get_segment_frame_rate(30))



    def test_get_current_segment_time(self):
        self.assert_current_segment_time((0, 9, 1), 0, 0, 0)
        self.assert_current_segment_time((0, 9, 2), 0, 0, 0)
        self.assert_current_segment_time((1, 10, 2), 1, 0, 0)

        self.assert_current_segment_time((0, 9, 1), 1, 100 / 3, 100 / 3)
        self.assert_current_segment_time((1, 10, 1), 2, 100 / 3, 100 / 3)

        self.assert_current_segment_time((0, 9, 1), 2, 200 / 3, 200 / 3)
        self.assert_current_segment_time((0, 9, 2), 2, 200 / 3, 60)
        self.assert_current_segment_time((1, 10, 2), 3, 200 / 3, 60)

        self.assert_current_segment_time((0, 9, 1), 8, 800 / 3, 800 / 3)
        self.assert_current_segment_time((0, 9, 2), 8, 800 / 3, 240)
        self.assert_current_segment_time((1, 10, 2), 9, 800 / 3, 240)

        self.assert_current_segment_time((0, 9, 1), 9, 300, 300)
        self.assert_current_segment_time((1, 10, 1), 10, 300, 300)

        self.assert_current_segment_time((2, 12, 1), 6, 400 / 3, 400 / 3)
        self.assert_current_segment_time((2, 12, 2), 6, 1100 / 9, 1100 / 9)


    def assert_current_segment_time(self, filter_args, original_position,
                                    expected_interval_time, expected_feed_forward_time):
        interval_filter, ff_filter = get_filters(filter_args)

        self.assertAlmostEqual(expected_interval_time,
                               interval_filter.get_current_segment_time_in_millis(original_position, 30))

        self.assertAlmostEqual(expected_feed_forward_time,
                               ff_filter.get_current_segment_time_in_millis(original_position, 30))



    def test_calculate_segment_frame_position_ratio(self):
        self.assert_segment_frame_position_ratio((0, 9, 1), 0, 0)
        self.assert_segment_frame_position_ratio((0, 9, 1), 2, 0.2)
        self.assert_segment_frame_position_ratio((0, 9, 1), 10, 1)

        self.assert_segment_frame_position_ratio((10, 29, 1), 10, 0)
        self.assert_segment_frame_position_ratio((10, 29, 1), 14, 0.2)
        self.assert_segment_frame_position_ratio((10, 29, 1), 30, 1)

        self.assert_segment_frame_position_ratio((10, 29, 2), 10, 0)
        self.assert_segment_frame_position_ratio((10, 29, 2), 14, 0.2)
        self.assert_segment_frame_position_ratio((10, 29, 2), 30, 1)

        self.assert_segment_frame_position_ratio((1, 11, 2), 1, 0)
        self.assert_segment_frame_position_ratio((1, 11, 2), 3, 1 / 6)
        self.assert_segment_frame_position_ratio((1, 11, 2), 5, 1 / 3)


    def assert_segment_frame_position_ratio(self, filter_args, original_position, expected_ratio):
        for frame_filter in get_filters(filter_args):
            self.assertAlmostEqual(expected_ratio, frame_filter.get_segment_frame_position_ratio(original_position))
            if expected_ratio >= 1:
                self.assertTrue(frame_filter.is_past_end_of_segment(original_position))
            else:
                self.assertFalse(frame_filter.is_past_end_of_segment(original_position))



    def test_calculate_ratio_to_original_frame_position(self):
        self.assert_ratio_to_original_frame_position((0, 4, 1), 0.5, 2)
        self.assert_ratio_to_original_frame_position((0, 5, 1), 0.5, 3)

        self.assert_ratio_to_original_frame_position((0, 4, 1), 1 / 3, 1)
        self.assert_ratio_to_original_frame_position((0, 5, 1), 1 / 3, 2)

        self.assert_ratio_to_original_frame_position((3, 14, 2), 0.5, 9)
        self.assert_ratio_to_original_frame_position((3, 15, 2), 0.5, 9)


    def assert_ratio_to_original_frame_position(self, filter_args, ratio, expected_frame_position):
        for frame_filter in get_filters(filter_args):
            actual_frame_position = frame_filter.ratio_to_original_frame_position(ratio)
            self.assertIsInstance(actual_frame_position, int)
            self.assertEqual(expected_frame_position, actual_frame_position)



    def test_calculate_millis_to_segment_frame_position(self):
        self.assert_millis_to_segment_frame_position((0, 21, 1), 10, 600, 6)
        self.assert_millis_to_segment_frame_position((0, 21, 2), 10, 600, 3)
        self.assert_millis_to_segment_frame_position((0, 21, 3), 10, 600, 2)

        self.assert_millis_to_segment_frame_position((5, 26, 1), 10, 600, 6)
        self.assert_millis_to_segment_frame_position((5, 26, 2), 10, 600, 3)
        self.assert_millis_to_segment_frame_position((5, 26, 3), 10, 600, 2)

        self.assert_millis_to_segment_frame_position((5, 260, 1), 10, 600, 6)
        self.assert_millis_to_segment_frame_position((5, 260, 2), 10, 600, 3)
        self.assert_millis_to_segment_frame_position((5, 260, 3), 10, 600, 2)


    def assert_millis_to_segment_frame_position(self, filter_args, original_frame_rate, segment_millis,
                                                expected_segment_position):
        for frame_filter in get_filters(filter_args):
            actual = frame_filter.millis_to_segment_frame_position(original_frame_rate, segment_millis)
            self.assertIsInstance(actual, int)
            self.assertEqual(expected_segment_position, actual)



    def test_determine_available_initialization_frames(self):
        self.assert_available_initialization_frames(0, 1, 0)
        self.assert_available_initialization_frames(1, 1, 1)
        self.assert_available_initialization_frames(2, 1, 2)
        self.assert_available_initialization_frames(10, 1, 10)

        self.assert_available_initialization_frames(0, 2, 0)
        self.assert_available_initialization_frames(10, 2, 5)
        self.assert_available_initialization_frames(11, 2, 5)

        self.assert_available_initialization_frames(2, 3, 0)
        self.assert_available_initialization_frames(5, 3, 1)
        self.assert_available_initialization_frames(10, 3, 3)

        self.assert_available_initialization_frames(10, 12, 0)


    def assert_available_initialization_frames(self, start_frame, frame_interval, expected_num_available):
        interval_filter = IntervalFrameFilter(start_frame, start_frame + 10, frame_interval)
        actual_num_available = interval_filter.get_available_initialization_frame_count()
        self.assertIsInstance(actual_num_available, int)
        self.assertEqual(expected_num_available, actual_num_available)



    def assert_read_fails(self, cap):
        self.assertRaises(StopIteration, next, cap)


    def assert_expected_frames_shown(self, cap_or_cap_args, expected_frames):
        if isinstance(cap_or_cap_args, mpf_util.VideoCapture):
            cap = cap_or_cap_args
        else:
            cap = create_video_capture(*cap_or_cap_args)

        self.assertEqual(len(expected_frames), cap.frame_count)
        num_read = 0
        for expected_frame_idx, frame in zip(expected_frames, cap):
            num_read += 1
            self.assertEqual(expected_frame_idx, get_frame_number(frame))

        self.assertEqual(len(expected_frames), num_read)
        self.assert_read_fails(cap)


    def test_no_frames_skipped_when_filter_params_provided_but_frame_filtering_disabled(self):
        cap = mpf_util.VideoCapture(create_video_job(0, 1, 3), True, False)
        self.assert_expected_frames_shown(cap, range(30))


    def test_no_frames_skipped_when_default_values(self):
        cap = create_video_capture(0, 29)
        self.assert_expected_frames_shown(cap, range(30))


    def test_can_handle_start_stop_frame(self):
        self.assert_expected_frames_shown((10, 16, 1), (10, 11, 12, 13, 14, 15, 16))
        self.assert_expected_frames_shown((26, 29, 1), (26, 27, 28, 29))


    def test_can_filter_frames(self):
        self.assert_expected_frames_shown((0, 19, 2), (0, 2, 4, 6, 8, 10, 12, 14, 16, 18))
        self.assert_expected_frames_shown((0, 19, 3), (0, 3, 6, 9, 12, 15, 18))
        self.assert_expected_frames_shown((0, 19, 4), (0, 4, 8, 12, 16))
        self.assert_expected_frames_shown((0, 19, 5), (0, 5, 10, 15))


    def test_can_handle_start_stop_frame_with_interval(self):
        self.assert_expected_frames_shown((15, 29, 2), (15, 17, 19, 21, 23, 25, 27, 29))
        self.assert_expected_frames_shown((15, 29, 3), (15, 18, 21, 24, 27))
        self.assert_expected_frames_shown((15, 29, 4), (15, 19, 23, 27))
        self.assert_expected_frames_shown((15, 29, 5), (15, 20, 25))
        self.assert_expected_frames_shown((20, 29, 4), (20, 24, 28))
        self.assert_expected_frames_shown((21, 29, 4), (21, 25, 29))
        self.assert_expected_frames_shown((20, 28, 4), (20, 24, 28))
        self.assert_expected_frames_shown((21, 28, 4), (21, 25))


    def test_can_not_set_position_beyond_segment(self):
        cap = create_video_capture(10, 15)

        self.assertTrue(cap.set_frame_position(4))
        self.assertEqual(4, cap.current_frame_position)

        self.assertFalse(cap.set_frame_position(10))
        self.assertEqual(4, cap.current_frame_position)

        self.assertFalse(cap.set_frame_position(-1))
        self.assertEqual(4, cap.current_frame_position)

        # cv2.VideoCapture does not allow you to set the frame position to the number of frames in the video.
        # However, after you read the last frame in the video, cv::VideoCapture's frame position will equal the number
        # of frames in the video.
        self.assertFalse(cap.set_frame_position(cap.frame_count))
        self.assertEqual(4, cap.current_frame_position)

        self.assertTrue(cap.set_frame_position(5))
        self.assertEqual(5, cap.current_frame_position)

        self.assertEqual(15, get_frame_number(next(cap)))

        self.assertEqual(cap.frame_count, cap.current_frame_position)

        # At end of segment so there shouldn't be any frames left to process.
        self.assert_read_fails(cap)


    def test_can_fix_frame_pos_in_reverse_transform(self):
        cap = create_video_capture(5, 19, 2)
        il = mpf.ImageLocation(0, 1, 2, 3)
        track = mpf.VideoTrack(1, 6, frame_locations={1: il, 2: il, 6: il})
        cap.reverse_transform(track)
        self.assertEqual(7, track.start_frame)
        self.assertEqual(17, track.stop_frame)
        self.assert_dict_contains_keys((7, 9, 17), track.frame_locations)


    def assert_dict_contains_keys(self, dict_, expected_keys):
        for key in expected_keys:
            self.assertIn(key, dict_)


    def test_can_get_initialization_frames(self):
        self.assert_initialization_frame_ids(0, 1, 100, ())
        self.assert_initialization_frame_ids(1, 1, 100, (0,))
        self.assert_initialization_frame_ids(2, 1, 100, (0, 1))
        self.assert_initialization_frame_ids(3, 1, 100, (0, 1, 2))

        self.assert_initialization_frame_ids(10, 1, 1, (9,))
        self.assert_initialization_frame_ids(10, 1, 2, (8, 9))
        self.assert_initialization_frame_ids(10, 1, 5, (5, 6, 7, 8, 9))

        self.assert_initialization_frame_ids(0, 4, 100, ())
        self.assert_initialization_frame_ids(3, 4, 100, ())
        self.assert_initialization_frame_ids(4, 4, 100, (0,))
        self.assert_initialization_frame_ids(7, 4, 100, (3,))
        self.assert_initialization_frame_ids(8, 4, 100, (0, 4))
        self.assert_initialization_frame_ids(9, 4, 100, (1, 5))

        self.assert_initialization_frame_ids(10, 3, 1, (7,))
        self.assert_initialization_frame_ids(10, 3, 2, (4, 7))
        self.assert_initialization_frame_ids(10, 3, 3, (1, 4, 7))
        self.assert_initialization_frame_ids(10, 3, 4, (1, 4, 7))
        self.assert_initialization_frame_ids(10, 3, 5, (1, 4, 7))
        self.assert_initialization_frame_ids(10, 3, 100, (1, 4, 7))


    def assert_initialization_frame_ids(self, start_frame, frame_interval, num_requested, expected_init_frames):
        cap = create_video_capture(start_frame, 29, frame_interval)
        init_frames = cap.get_initialization_frames_if_available(num_requested)
        self.assertEqual(len(expected_init_frames), len(init_frames))

        for expected_index, frames in zip(expected_init_frames, init_frames):
            self.assertEqual(expected_index, get_frame_number(frames))


    def test_initialization_frames_independent_of_current_position(self):
        cap = create_video_capture(10, 29, 5)
        cap.set_frame_position(2)

        self.assertEqual(20, get_frame_number(next(cap)))
        self.assertEqual(3, cap.current_frame_position)

        init_frames = cap.get_initialization_frames_if_available(2)
        self.assertEqual(2, len(init_frames))
        self.assertEqual(0, get_frame_number(init_frames[0]))
        self.assertEqual(5, get_frame_number(init_frames[1]))

        self.assertEqual(3, cap.current_frame_position)
        self.assertEqual(25, get_frame_number(next(cap)))


    def test_can_handle_feed_forward_track(self):
        ff_track = mpf.VideoTrack(0, 29, frame_locations={
            1: mpf.ImageLocation(5, 5, 5, 10),
            3: mpf.ImageLocation(4, 4, 5, 6),
            7: mpf.ImageLocation(5, 5, 8, 9),
            11: mpf.ImageLocation(4, 5, 5, 6),
            12: mpf.ImageLocation(4, 4, 1, 2),
            20: mpf.ImageLocation(5, 5, 5, 5),
            25: mpf.ImageLocation(4, 4, 5, 5)
        })

        job = mpf.VideoJob('TEST', FRAME_FILTER_TEST_VIDEO, 0, -1,
                           dict(FEED_FORWARD_TYPE='SUPERSET_REGION'), {}, ff_track)

        cap = mpf_util.VideoCapture(job)
        self.assertEqual(7, cap.frame_count)
        self.assertFalse(cap.get_initialization_frames_if_available(100))

        min_x = ff_track.frame_locations[3].x_left_upper
        max_x = ff_track.frame_locations[7].x_left_upper + ff_track.frame_locations[7].width
        min_y = ff_track.frame_locations[3].y_left_upper
        max_y = ff_track.frame_locations[1].y_left_upper + ff_track.frame_locations[1].height
        expected_size = mpf_util.Size(max_x - min_x, max_y - min_y)
        self.assertEqual(expected_size, cap.frame_size)

        self.assert_frame_read(cap, 1, expected_size, 0)
        self.assert_frame_read(cap, 3, expected_size, 1 / 7)
        self.assert_frame_read(cap, 7, expected_size, 2 / 7)
        self.assert_frame_read(cap, 11, expected_size, 3 / 7)
        self.assert_frame_read(cap, 12, expected_size, 4 / 7)
        self.assert_frame_read(cap, 20, expected_size, 5 / 7)
        self.assert_frame_read(cap, 25, expected_size, 6 / 7)

        self.assertAlmostEqual(1, cap.frame_position_ratio)
        self.assert_read_fails(cap)

        il = mpf.ImageLocation(0, 1, 2, 3)
        track = mpf.VideoTrack(0, 6, frame_locations={1: il, 2: il, 4: il, 5: il})
        cap.reverse_transform(track)
        self.assertEqual(1, track.start_frame)
        self.assertEqual(25, track.stop_frame)
        self.assert_dict_contains_keys(track.frame_locations, (3, 7, 12, 20))



    def assert_frame_read(self, cap, expected_frame_number, expected_size, expected_ratio):
        self.assertEqual(expected_ratio, cap.frame_position_ratio)

        frame = next(cap)
        self.assertEqual(expected_frame_number, get_frame_number(frame))

        height, width, _ = frame.shape
        self.assertEqual((width, height), expected_size)
        self.assertEqual(mpf_util.Size.from_frame(frame), expected_size)


    def test_can_use_search_region_with_feed_forward_frame_type(self):
        ff_track = mpf.VideoTrack(0, 15, frame_locations={1: mpf.ImageLocation(5, 5, 5, 5)})
        job_properties = dict(
            FEED_FORWARD_TYPE='FRAME',
            SEARCH_REGION_ENABLE_DETECTION='True',
            SEARCH_REGION_TOP_LEFT_X_DETECTION='3',
            SEARCH_REGION_TOP_LEFT_Y_DETECTION='3',
            SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='6',
            SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='8')

        job = mpf.VideoJob('TEST', FRAME_FILTER_TEST_VIDEO, 0, -1, job_properties, {}, ff_track)
        cap = mpf_util.VideoCapture(job)

        expected_size = mpf_util.Size(3, 5)
        self.assertEqual(expected_size, cap.frame_size)

        frame = next(cap)
        self.assertEqual(expected_size.width, frame.shape[1])
        self.assertEqual(expected_size.height, frame.shape[0])


    def test_cv_video_capture_get_frame_position_issue(self):
        # This test demonstrates the issue that led us to keep track of frame position in mpf_util.VideoCapture
        # instead of depending on cv2.VideoCapture.
        # This test may fail in a future version of OpenCV. If this test fails,
        # then mpf_util.VideoCapture no longer needs to handle frame position.
        # The test_mpf_video_capture_does_not_have_get_frame_position_issue test case shows that
        # mpf_util.VideoCapture does not have the same issue demonstrated here.
        cv_cap = cv2.VideoCapture(VIDEO_WITH_SET_FRAME_ISSUE)

        cv_cap.read()
        cv_cap.set(cv2.CAP_PROP_POS_FRAMES, 10)
        cv_cap.read()

        frame_position = int(cv_cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.assertNotEqual(11, frame_position,
                            'If this test fails, then a bug with OpenCV has been fixed. See test for details')


    def test_mpf_video_capture_does_not_have_get_frame_position_issue(self):
        # This test verifies that mpf_util.VideoCapture does not have the same issue demonstrated in the
        # test_cv_video_capture_get_frame_position_issue test case.
        job = mpf.VideoJob('Test', VIDEO_WITH_SET_FRAME_ISSUE, 0, 1000, {}, {}, None)
        cap = mpf_util.VideoCapture(job, False, False)

        cap.read()
        cap.set_frame_position(10)
        cap.read()

        frame_position = cap.current_frame_position
        self.assertEqual(11, frame_position)


    def test_cv_video_capture_set_frame_position_issue(self):
        # This test demonstrates the issue that led us to implement SeekStrategy with fall-backs instead of just
        # using cv2.VideoCapture.set(cv2.CAP_PROP_POS_FRAMES, int).
        # This test may fail in a future version of OpenCV. If this test fails, then mpf_util.VideoCapture no longer
        # needs to use the SeekStrategy classes.
        # The test_mpf_video_capture_does_not_have_set_frame_position_issue test case shows that mpf_util.VideoCapture
        # does not have the same issue demonstrated here.
        cv_cap = cv2.VideoCapture(VIDEO_WITH_SET_FRAME_ISSUE)
        frame_count = int(cv_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cv_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 5)

        was_read, _ = cv_cap.read()
        self.assertFalse(was_read, 'If this test fails, then a bug with OpenCV has been fixed. See test for details')



    def test_mpf_video_capture_does_not_have_set_frame_position_issue(self):
        # This test verifies that mpf_util.VideoCapture does not have the same issue demonstrated in the
        # test_cv_video_capture_set_frame_position_issue test case.
        job = mpf.VideoJob('Test', VIDEO_WITH_SET_FRAME_ISSUE, 0, 1000, {}, {}, None)
        cap = mpf_util.VideoCapture(job, False, False)
        frame_count = cap.frame_count
        cap.set_frame_position(frame_count - 5)

        was_read, _ = cap.read()
        self.assertTrue(was_read)


    def assert_can_change_frame_position(self, seek_strategy):
        cv_cap = cv2.VideoCapture(FRAME_FILTER_TEST_VIDEO)
        frame_position = 0

        frame_position = seek_strategy.change_position(cv_cap, frame_position, 28)
        self.assertEqual(28, frame_position, 'Failed to seek forward')
        was_read, frame = cv_cap.read()
        self.assertTrue(was_read, 'Failed to read frame after forward seek')
        self.assertEqual(28, get_frame_number(frame), 'Incorrect frame read after forward seek')
        frame_position += 1

        frame_position = seek_strategy.change_position(cv_cap, frame_position, 5)
        self.assertEqual(5, frame_position, 'Failed to seek backward')
        was_read, frame = cv_cap.read()
        self.assertTrue(was_read, 'Failed to read frame after backward seek')
        self.assertEqual(5, get_frame_number(frame), 'Incorrect frame read after backward seek')
        frame_position += 1

        frame_position = seek_strategy.change_position(cv_cap, frame_position, 20)
        self.assertEqual(20, frame_position, 'Failed to seek forward after backward seek')
        was_read, frame = cv_cap.read()
        self.assertTrue(was_read, 'Failed to read frame when seeking forward after backward seek')
        self.assertEqual(20, get_frame_number(frame), 'Incorrect frame read when seeking forward after backward seek')


    def test_set_frame_position_seek(self):
        self.assert_can_change_frame_position(seek_strategies.SetFramePositionSeek())

    def test_grab_seek(self):
        self.assert_can_change_frame_position(seek_strategies.GrabSeek())

    def test_read_seek(self):
        self.assert_can_change_frame_position(seek_strategies.ReadSeek())


    def test_can_filter_on_key_frames(self):
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 0, 1000, dict(USE_KEY_FRAMES='true'), {}, None)
        cap = mpf_util.VideoCapture(job)
        self.assert_expected_frames_shown(cap, (0, 5, 10, 15, 20, 25))


    def test_can_filter_on_key_frames_and_start_stop_frame(self):
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 6, 21, dict(USE_KEY_FRAMES='true'), {}, None)
        cap = mpf_util.VideoCapture(job)
        self.assert_expected_frames_shown(cap, (10, 15, 20))


    def test_can_filter_on_key_frames_and_interval(self):
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 0, 1000, dict(USE_KEY_FRAMES='true', FRAME_INTERVAL='2'),
                           {}, None)
        cap = mpf_util.VideoCapture(job)
        self.assert_expected_frames_shown(cap, (0, 10, 20))

        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 0, 1000, dict(USE_KEY_FRAMES='true', FRAME_INTERVAL='3'),
                           {}, None)
        cap = mpf_util.VideoCapture(job)
        self.assert_expected_frames_shown(cap, (0, 15))


    def test_can_filter_on_key_frames_and_start_stop_frame_and_interval(self):
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 5, 21, dict(USE_KEY_FRAMES='true', FRAME_INTERVAL='2'),
                           {}, None)
        cap = mpf_util.VideoCapture(job)
        self.assert_expected_frames_shown(cap, (5, 15))


    def test_reverse_transform_no_feed_forward_no_search_region(self):
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 0, 30, {}, {}, None)
        cap = mpf_util.VideoCapture(job)

        track = create_test_track()
        cap.reverse_transform(track)
        self.assertEqual(5, track.start_frame)
        self.assertEqual(10, track.stop_frame)

        self.assertEqual(3, len(track.frame_locations))
        self.assert_dict_contains_keys(track.frame_locations, (5, 7, 10))

        location = track.frame_locations[5]
        self.assertEqual(20, location.x_left_upper)
        self.assertEqual(30, location.y_left_upper)
        self.assertEqual(15, location.width)
        self.assertEqual(5, location.height)


    def test_reverse_transform_no_feed_forward_with_search_region(self):
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 0, 30,
                           dict(
                               SEARCH_REGION_ENABLE_DETECTION='true',
                               SEARCH_REGION_TOP_LEFT_X_DETECTION='3',
                               SEARCH_REGION_TOP_LEFT_Y_DETECTION='4',
                               SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION='40',
                               SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION='50'
                           ),
                           {}, None)
        cap = mpf_util.VideoCapture(job)

        self.assertEqual((37, 46), cap.frame_size)

        track = create_test_track()
        cap.reverse_transform(track)

        self.assertEqual(track.start_frame, 5)
        self.assertEqual(track.stop_frame, 10)
        self.assertEqual(3, len(track.frame_locations))
        self.assert_dict_contains_keys(track.frame_locations, (5, 7, 10))

        location = track.frame_locations[5]
        self.assertEqual(23, location.x_left_upper)
        self.assertEqual(34, location.y_left_upper)
        self.assertEqual(15, location.width)
        self.assertEqual(5, location.height)


    def test_feed_forward_cropper_crop_to_exact_region(self):
        ff_track = mpf.VideoTrack(4, 29, frame_locations={
            4: mpf.ImageLocation(10, 60, 65, 125),
            15: mpf.ImageLocation(60, 20, 100, 200),
            29: mpf.ImageLocation(70, 0, 30, 240)
        })
        job = mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, 4, 29, dict(FEED_FORWARD_TYPE='REGION'), {}, ff_track)
        cap = mpf_util.VideoCapture(job)
        output_track = mpf.VideoTrack(0, 2)

        frame_pos = cap.current_frame_position
        frame = next(cap)
        self.assertEqual(4, get_frame_number(frame))
        self.assertEqual((65, 125), mpf_util.Size.from_frame(frame))
        output_track.frame_locations[frame_pos] = mpf.ImageLocation(0, 0, frame.shape[1], frame.shape[0])

        frame_pos = cap.current_frame_position
        frame = next(cap)
        self.assertEqual(15, get_frame_number(frame))
        self.assertEqual((100, 200), mpf_util.Size.from_frame(frame))
        output_track.frame_locations[frame_pos] = mpf.ImageLocation(0, 0, frame.shape[1], frame.shape[0])

        frame_pos = cap.current_frame_position
        frame = next(cap)
        self.assertEqual(29, get_frame_number(frame))
        self.assertEqual((30, 240), mpf_util.Size.from_frame(frame))
        output_track.frame_locations[frame_pos] = mpf.ImageLocation(5, 40, 15, 60)

        self.assert_read_fails(cap)

        cap.reverse_transform(output_track)
        self.assertEqual(len(ff_track.frame_locations), len(output_track.frame_locations))

        self.assertEqual(ff_track.frame_locations[4], output_track.frame_locations[4])
        self.assertEqual(ff_track.frame_locations[15], output_track.frame_locations[15])

        last_detection = output_track.frame_locations[29]
        self.assertEqual(75, last_detection.x_left_upper)
        self.assertEqual(40, last_detection.y_left_upper)
        self.assertEqual(15, last_detection.width)
        self.assertEqual(60, last_detection.height)


class TestVideoCaptureMixin(unittest.TestCase):
    def test_video_capture_mixin(self):
        job_properties = {
            'ROTATION': '270', 'HORIZONTAL_FLIP': 'True',
            'SEARCH_REGION_ENABLE_DETECTION': 'true',
            'SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION': '80',
            'SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION': '100'
        }

        # Image is treated like a single frame video.
        job = mpf.VideoJob('Test', test_util.get_data_file_path('test_img.png'), 0, 0, job_properties,
                           dict(FRAME_COUNT='1'), None)

        component = VideoCaptureMixinComponent(self)
        results = list(component.get_detections_from_video(job))
        self.assertEqual(4, len(results))
        self.assertEqual((319, 199, 30, 20), mpf_util.Rect.from_image_location(results[0].frame_locations[0]))
        self.assertEqual((239, 149, 30, 20), mpf_util.Rect.from_image_location(results[1].frame_locations[0]))
        self.assertEqual((319, 149, 30, 20), mpf_util.Rect.from_image_location(results[2].frame_locations[0]))
        self.assertEqual((239, 199, 30, 20), mpf_util.Rect.from_image_location(results[3].frame_locations[0]))



class VideoCaptureMixinComponent(mpf_util.VideoCaptureMixin):
    def __init__(self, test_obj):
        self._test = test_obj

    def get_detections_from_video_capture(self, video_job, video_capture):
        test = self._test

        for frame_index, frame in enumerate(video_capture):
            top_left_corner = frame[:20, :30]
            test.assertTrue(test_util.is_all_black(top_left_corner))
            bottom_right_corner = frame[80:, 50:]
            test.assertTrue(test_util.is_all_black(bottom_right_corner))

            top_right_corner = frame[:20, 50:]
            test.assertTrue(test_util.is_all_white(top_right_corner))
            bottom_left_corner = frame[80:, :30]
            test.assertTrue(test_util.is_all_white(bottom_left_corner))

            for corner in (top_left_corner, bottom_right_corner, top_right_corner, bottom_left_corner):
                test.assertEqual(mpf_util.Size(30, 20), mpf_util.Size.from_frame(corner))

            yield mpf.VideoTrack(frame_index, frame_index,
                                 frame_locations={frame_index: mpf.ImageLocation(0, 0, 30, 20)})
            yield mpf.VideoTrack(frame_index, frame_index,
                                 frame_locations={frame_index: mpf.ImageLocation(50, 80, 30, 20)})
            yield mpf.VideoTrack(frame_index, frame_index,
                                 frame_locations={frame_index: mpf.ImageLocation(50, 0, 30, 20)})
            yield mpf.VideoTrack(frame_index, frame_index,
                                 frame_locations={frame_index: mpf.ImageLocation(0, 80, 30, 20)})




def get_filters(interval_filter_args):
    interval_filter = IntervalFrameFilter(*interval_filter_args)
    yield interval_filter
    yield to_feed_forward_filter(interval_filter)


def to_feed_forward_filter(interval_filter):
    frame_count = interval_filter.get_segment_frame_count()
    frame_location_map = dict()
    for i in range(frame_count):
        original_pos = interval_filter.segment_to_original_frame_position(i)
        frame_location_map[original_pos] = mpf.ImageLocation(0, 0, 0, 0)

    ff_track = mpf.VideoTrack(0, frame_count, frame_locations=frame_location_map)
    return FeedForwardFrameFilter(ff_track)


FRAME_FILTER_TEST_VIDEO = test_util.get_data_file_path('frame_filter_test.mp4')
VIDEO_WITH_SET_FRAME_ISSUE = test_util.get_data_file_path('vid-with-set-position-issues.mov')


def create_video_job(start_frame, stop_frame, frame_interval=None):
    job_properties = dict()
    if frame_interval is not None:
        job_properties['FRAME_INTERVAL'] = str(frame_interval)

    return mpf.VideoJob('Test', FRAME_FILTER_TEST_VIDEO, start_frame, stop_frame, job_properties, {}, None)



def create_video_capture(start_frame, stop_frame, interval=None):
    return mpf_util.VideoCapture(create_video_job(start_frame, stop_frame, interval))


def create_test_track():
    return mpf.VideoTrack(5, 10, frame_locations={
        5: mpf.ImageLocation(20, 30, 15, 5),
        7: mpf.ImageLocation(0, 1, 2, 3),
        10: mpf.ImageLocation(4, 5, 6, 7)})


def get_frame_number(frame):
    # In frame_filter_test.mp4 value of each color channel value is equal to that frame's frame number.
    # For example the color of frame 0 is rgb(0, 0, 0) and frame 1 is rgb(1, 1, 1).
    return frame[0, 0, 0]
