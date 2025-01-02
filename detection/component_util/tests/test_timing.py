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
from unittest import mock
from unittest.mock import Mock


import test_util
test_util.add_local_component_libs_to_sys_path()
import mpf_component_api as mpf

class TestTiming(unittest.TestCase):

    def setUp(self):
        clock_patcher = mock.patch('time.perf_counter')
        self._mock_clock = clock_patcher.start()
        self.addCleanup(clock_patcher.stop)

        self._mock_reporter = Mock()
        self._timing = mpf.Timing(self._mock_reporter)


    def _set_clock_times(self, *times: float):
        self._mock_clock.side_effect = [*times, Exception('all times used.')]


    def test_context_manager(self):
        self._set_clock_times(3, 8)
        with self._timing.timer_ctx('test-timer') as timer:
            timer.add_metric('2x time', lambda sec: 2 * sec)

        self._mock_reporter.assert_called_once_with({
            'name': 'test-timer',
            'seconds': 5.0,
            'metrics': {'2x time': 10.0}
        })


    def test_decorator_with_args(self):

        @self._timing.time_func('test-timer', {'3x time': lambda sec: 3 * sec})
        def func_to_time(a, b):
            return a + b

        self._set_clock_times(5, 12, 13, 16)
        self.assertEqual('ab', func_to_time('a', 'b'))
        self.assertEqual('cd', func_to_time('c', 'd'))
        self._mock_reporter.assert_has_calls([
            mock.call({
                'name': 'test-timer',
                'seconds': 7.0,
                'metrics': {'3x time': 21.0}
            }),
            mock.call({
                'name': 'test-timer',
                'seconds': 3.0,
                'metrics': {'3x time': 9.0}
            })
        ])


    def test_decorator_no_args(self):

        @self._timing.time_func
        def func_to_time(a, b):
            return a + b

        self._set_clock_times(5, 12, 13, 16)
        self.assertEqual('ab', func_to_time('a', 'b'))
        self.assertEqual('cd', func_to_time('c', 'd'))
        self._mock_reporter.assert_has_calls([
            mock.call({
                'name': 'func_to_time',
                'seconds': 7.0,
                'metrics': {}
            }),
            mock.call({
                'name': 'func_to_time',
                'seconds': 3.0,
                'metrics': {}
            })
        ])


    def test_iterator(self):
        self._set_clock_times(120, 125)
        expected_values = iter(range(20))
        for value in self._timing.iterator('test-timer', range(20)):
            self.assertEqual(value, next(expected_values))

        self._mock_reporter.assert_called_once_with({
            'name': 'test-timer',
            'seconds': 5.0,
            'metrics': {'iterations/sec': 4.0}
        })


    def test_detailed_iterator(self):
        start_time = 100
        iter1_start = 108
        iter1_stop = 119
        iter2_start = 121
        iter2_stop = 129
        stop_time = 140
        self._set_clock_times(
            start_time, iter1_start, iter1_stop, iter2_start, iter2_stop, stop_time
        )
        expected_values = iter(range(2))
        for value in self._timing.detailed_iter('test-timer', range(2)):
            self.assertEqual(value, next(expected_values))

        self._mock_reporter.assert_called_once_with({
            'name': 'test-timer',
            'seconds': 40.0,
            'metrics': {
                'iterations/sec': 0.05,
                'loop body time (s)': 19.0,
                'iterator time (s)': 21.0
            }})


    def test_time_segments(self):
        self._set_clock_times(3, 10, 16, 20)
        with self._timing.timer_ctx('test-timer', started=False) as timer:
            with timer.time_segment():
                pass
            with timer.time_segment():
                pass

        self._mock_reporter.assert_called_once_with({
            'name': 'test-timer',
            'seconds': 11.0,
            'metrics': {}
        })


    def test_generator_decorator_with_args(self):
        @self._timing.time_func('test-timer', metrics={'4x time': lambda sec: sec * 4})
        def generator_func():
            yield 1
            yield 2
            return 3

        self._set_clock_times(51, 61)
        generator = generator_func()
        self.assertEqual(1, next(generator))
        self.assertEqual(2, next(generator))
        self._mock_reporter.assert_not_called()

        with self.assertRaises(StopIteration) as cm:
            next(generator)
        self.assertEqual(3, cm.exception.value)

        self._mock_reporter.assert_called_once_with({
            'name': 'test-timer',
            'seconds': 10.0,
            'metrics': {'4x time': 40.0}
        })


    def test_generator_decorator_no_args(self):
        @self._timing.time_func
        def generator_func():
            yield 3
            yield 4
            return 5

        self._set_clock_times(34, 40)
        generator = generator_func()
        self.assertEqual(3, next(generator))
        self.assertEqual(4, next(generator))
        self._mock_reporter.assert_not_called()

        with self.assertRaises(StopIteration) as cm:
            next(generator)
        self.assertEqual(5, cm.exception.value)

        self._mock_reporter.assert_called_once_with({
            'name': 'generator_func',
            'seconds': 6.0,
            'metrics': {}
        })
