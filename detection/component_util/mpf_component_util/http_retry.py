#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2022 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2022 The MITRE Corporation                                      #
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

import time
from typing import Callable, Any, Literal, Optional, Mapping
import urllib.error
import urllib.request

import mpf_component_api as mpf
import mpf_component_util as mpf_util

ShouldRetryFunc = Callable[[str, urllib.error.URLError, Optional[str]], bool]

def always_retry(url: str, exception: urllib.error.URLError, body: Optional[str]) -> Literal[True]:
    return True


class HttpRetry:
    def __init__(self, max_attempts: int, starting_delay_ms: int, max_delay_ms: int,
                 printer: Callable[[str], Any] = print):
        self._max_attempts = max_attempts
        self._starting_delay_ms = starting_delay_ms
        self._max_delay_ms = max_delay_ms
        self._printer = printer


    @classmethod
    def from_properties(cls, properties: Mapping[str, str], printer: Callable[[str], Any] = print):
        return cls(
            mpf_util.get_property(properties, 'COMPONENT_HTTP_RETRY_MAX_ATTEMPTS', 10),
            mpf_util.get_property(properties, 'COMPONENT_HTTP_RETRY_INITIAL_DELAY_MS', 200),
            mpf_util.get_property(properties, 'COMPONENT_HTTP_RETRY_MAX_DELAY_MS', 30_000),
            printer)


    def urlopen(self, *args, should_retry: ShouldRetryFunc = always_retry, **kwargs):
        remaining_attempts = self._max_attempts
        delay = self._starting_delay_ms
        url = self._get_url(*args, **kwargs)
        while True:
            try:
                return urllib.request.urlopen(*args, **kwargs)
            except urllib.error.URLError as e:
                error_body = self._get_error_body(e)
                message = self._get_failure_message(url, e, error_body)
                remaining_attempts -= 1
                if not should_retry(url, e, error_body) or remaining_attempts <= 0:
                    raise mpf.DetectionError.NETWORK_ERROR.exception(message) from e

                retry_after_header = self._get_retry_after_header_ms(e)
                if retry_after_header and retry_after_header > delay:
                    delay = retry_after_header
                    self._printer(message +
                                  f' There are {remaining_attempts} remaining attempts and the '
                                  f'next one will begin in {delay} milliseconds because the '
                                  f'Retry-After header was set to {retry_after_header // 1000} '
                                  '(seconds).')
                else:
                    self._printer(message +
                                  f' There are {remaining_attempts} remaining attempts and the '
                                  f'next one will begin in {delay} milliseconds.')

                time.sleep(delay / 1000)
                delay = min(2 * delay, self._max_delay_ms)


    @staticmethod
    def _get_url(*args, **kwargs) -> str:
        request_obj = args[0] if args else kwargs.get('url', '')
        if isinstance(request_obj, urllib.request.Request):
            return request_obj.full_url
        else:
            return request_obj

    @staticmethod
    def _get_error_body(exception: urllib.error.URLError) -> Optional[str]:
        if isinstance(exception, urllib.error.HTTPError):
            return exception.read().decode('utf-8', errors='replace')
        else:
            return None

    @staticmethod
    def _get_failure_message(url: str, exception: Exception, error_body: Optional[str]) -> str:
        if isinstance(exception, urllib.error.HTTPError):
            return f'HTTP request to "{url}" failed with status {exception.code} and message: ' \
                   f'"{error_body}"'
        else:
            return f'HTTP request to {url} failed due to: "{exception}".'


    @staticmethod
    def _get_retry_after_header_ms(exception: Exception) -> Optional[int]:
        if not isinstance(exception, urllib.error.HTTPError):
            return None
        retry_after_header = exception.headers.get('Retry-After', '').strip()
        if retry_after_header.isdigit():
            return int(retry_after_header) * 1000
        else:
            return None
