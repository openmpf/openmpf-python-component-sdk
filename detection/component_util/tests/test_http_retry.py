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

import test_util
test_util.add_local_component_libs_to_sys_path()

import io
import unittest
from unittest import mock
from unittest.mock import Mock
from urllib.error import URLError, HTTPError
import urllib.request

import mpf_component_api as mpf
from mpf_component_util import HttpRetry


class TestHttpRetry(unittest.TestCase):

    def setUp(self) -> None:
        sleep_patcher = mock.patch('time.sleep')
        self._mock_sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

        urlopen_patcher = mock.patch('urllib.request.urlopen')
        self._mock_urlopen = urlopen_patcher.start()
        self.addCleanup(urlopen_patcher.stop)

        self._mock_print = Mock(wraps=print)


    def test_first_attempt_successful(self):
        request = Mock()
        mock_resp = Mock()
        self._mock_urlopen.return_value = mock_resp

        retry = HttpRetry(3, 200, 30_000, self._mock_print)
        result = retry.urlopen(request)

        self.assertIs(result, mock_resp)
        self._mock_urlopen.assert_called_once_with(request)
        self._mock_print.assert_not_called()
        self._mock_sleep.assert_not_called()


    def test_all_attempts_failed(self):
        self._mock_urlopen.side_effect = (URLError('test'), URLError('test'), URLError('asdf'))

        retry = HttpRetry(3, 200, 30_000, self._mock_print)
        with self.assertRaises(mpf.DetectionException) as e_ctx:
            retry.urlopen('http://example.com')

        self.assertEqual(mpf.DetectionError.NETWORK_ERROR, e_ctx.exception.error_code)
        self.assertIn('asdf', str(e_ctx.exception))
        self.assertIn('http://example.com', str(e_ctx.exception))

        self.assertEqual(3, self._mock_urlopen.call_count)
        self.assertEqual(2, self._mock_print.call_count)
        self.assertEqual([mock.call(0.2), mock.call(0.4)], self._mock_sleep.call_args_list)


    def test_failure_then_recovery(self):
        mock_resp = Mock()
        self._mock_urlopen.side_effect = (URLError('test'), URLError('test'), mock_resp)

        retry = HttpRetry(3, 200, 30_000, self._mock_print)
        request = urllib.request.Request('http://example.com', data=b'hello')
        result = retry.urlopen(request)

        self.assertIs(result, mock_resp)
        self.assertEqual([mock.call(request)] * 3, self._mock_urlopen.call_args_list)

        self.assertEqual(2, self._mock_print.call_count)
        self.assertIn('http://example.com', self._mock_print.call_args.args[0])
        self.assertEqual([mock.call(0.2), mock.call(0.4)], self._mock_sleep.call_args_list)


    def test_http_retry_after_header(self):
        mock_resp = Mock()
        self._mock_urlopen.side_effect = (
            create_retry_after_error(3), create_retry_after_error(4), create_retry_after_error(20),
            mock_resp)

        retry = HttpRetry(5, 200, 30_000, self._mock_print)
        result = retry.urlopen('http://example.com')

        self.assertIs(result, mock_resp)
        self.assertEqual(4, self._mock_urlopen.call_count)
        self.assertEqual(3, self._mock_print.call_count)
        self.assertEqual([mock.call(3), mock.call(6), mock.call(20)],
                         self._mock_sleep.call_args_list)


    def test_combined_errors_and_retry_header(self):
        mock_resp = Mock()
        self._mock_urlopen.side_effect = (
            URLError(1),
            create_retry_after_error(3),
            create_retry_after_error(4),
            URLError(2),
            create_retry_after_error(30),
            URLError(3),
            create_retry_after_error(30),
            create_retry_after_error(10),
            mock_resp)

        retry = HttpRetry(10, 200, 25_000, self._mock_print)
        retry.urlopen('http://example.com')

        self.assertEqual(9, self._mock_urlopen.call_count)
        self.assertEqual(8, self._mock_print.call_count)

        self.assertEqual(8, self._mock_sleep.call_count)
        # Regular error
        # Sleep for initial delay
        self.assertAlmostEqual(0.2, self._mock_sleep.call_args_list[0].args[0])
        # Retry header = 3
        # Would have slept for 0.4 due to exponential backoff, but Retry-After was greater.
        self.assertAlmostEqual(3, self._mock_sleep.call_args_list[1].args[0])
        # Retry header = 4
        # Doubled last sleep to get 6 which was already greater than Retry-After.
        self.assertAlmostEqual(6, self._mock_sleep.call_args_list[2].args[0])
        # Regular error
        # Doubled last sleep.
        self.assertAlmostEqual(12, self._mock_sleep.call_args_list[3].args[0])
        # Retry header = 30
        # Would have slept for 24s due to exponential backoff, but Retry-After was greater.
        self.assertAlmostEqual(30, self._mock_sleep.call_args_list[4].args[0])
        # Regular error
        # Doubling last sleep is 60, but that is greater than max_delay.
        self.assertAlmostEqual(25, self._mock_sleep.call_args_list[5].args[0])
        # Retry header = 30
        # Would have used max delay of 25, but Retry-After was greater.
        self.assertAlmostEqual(30, self._mock_sleep.call_args_list[6].args[0])
        # Retry header = 10
        # Used max delay of 25
        self.assertAlmostEqual(25, self._mock_sleep.call_args_list[7].args[0])


    def test_max_delay(self):
        self._mock_urlopen.side_effect = (URLError(i + 1) for i in range(10))

        retry = HttpRetry.from_properties(dict(
                COMPONENT_HTTP_RETRY_MAX_ATTEMPTS='10',
                COMPONENT_HTTP_RETRY_INITIAL_DELAY_MS='100',
                COMPONENT_HTTP_RETRY_MAX_DELAY_MS='5_000'),
            self._mock_print)

        with self.assertRaises(mpf.DetectionException) as e_ctx:
            retry.urlopen('http://example.com')
        self.assertEqual(mpf.DetectionError.NETWORK_ERROR, e_ctx.exception.error_code)
        self.assertIn('10', str(e_ctx.exception))

        self.assertEqual(10, self._mock_urlopen.call_count)
        self.assertEqual(9, self._mock_print.call_count)
        self.assertEqual(9, self._mock_sleep.call_count)
        self.assertAlmostEqual(0.1, self._mock_sleep.call_args_list[0].args[0])
        self.assertAlmostEqual(0.2, self._mock_sleep.call_args_list[1].args[0])
        self.assertAlmostEqual(0.4, self._mock_sleep.call_args_list[2].args[0])
        self.assertAlmostEqual(0.8, self._mock_sleep.call_args_list[3].args[0])
        self.assertAlmostEqual(1.6, self._mock_sleep.call_args_list[4].args[0])
        self.assertAlmostEqual(3.2, self._mock_sleep.call_args_list[5].args[0])
        self.assertAlmostEqual(5, self._mock_sleep.call_args_list[6].args[0])
        self.assertAlmostEqual(5, self._mock_sleep.call_args_list[7].args[0])
        self.assertAlmostEqual(5, self._mock_sleep.call_args_list[8].args[0])


    def test_prevent_retry(self):
        num_checks = 0

        def should_retry(url, error, body):
            nonlocal num_checks
            num_checks += 1
            return num_checks != 2

        self._mock_urlopen.side_effect = HTTPError(
            'http://example.com', 400, 'BAD REQUEST', {}, io.BytesIO(b'specific error'))

        retry = HttpRetry(4, 200, 30_000, self._mock_print)
        with self.assertRaises(mpf.DetectionException) as cm:
            retry.urlopen('http://example.com', should_retry=should_retry)

        self.assertEqual(mpf.DetectionError.NETWORK_ERROR, cm.exception.error_code)
        self.assertEqual(2, self._mock_urlopen.call_count)
        self.assertEqual(2, num_checks)


    def test_prevent_retry_custom_exception(self):

        class SpecificError(Exception):
            pass

        def should_retry(url, error, body):
            if body == 'specific error':
                raise SpecificError()
            else:
                return True

        self._mock_urlopen.side_effect = HTTPError(
            'http://example.com', 400, 'BAD REQUEST', {}, io.BytesIO(b'specific error'))

        retry = HttpRetry(3, 200, 30_000, self._mock_print)
        with self.assertRaises(SpecificError):
            retry.urlopen('http://example.com', should_retry=should_retry)
        self._mock_urlopen.assert_called_once()



def create_retry_after_error(retry_header_value):
    return HTTPError('http://example.com', 419, '', {'Retry-After': str(retry_header_value)},
                     Mock())
