#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2025 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2025 The MITRE Corporation                                      #
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

import bisect
import re
from typing import Callable, Literal, Optional, Union

import mpf_component_api as mpf

# Languages that typically do NOT use spaces between words
NO_SPACE_LANGS = ('JA', 'YUE', 'ZH-HANS', 'ZH-HANT')

class ChineseAndJapaneseCodePoints:
    # From http://www.unicode.org/charts/
    RANGES = sorted((
        range(0x2e80, 0x2fe0),
        range(0x2ff0, 0x3130),
        range(0x3190, 0x3300),
        range(0x3400, 0x4dc0),
        range(0x4e00, 0xa4d0),
        range(0xf900, 0xfb00),
        range(0xfe10, 0xfe20),
        range(0xfe30, 0xfe70),
        range(0xff00, 0xffa0),
        range(0x16f00, 0x16fa0),
        range(0x16fe0, 0x18d09),
        range(0x1b000, 0x1b300),
        range(0x1f200, 0x1f300),
        range(0x20000, 0x2a6de),
        range(0x2a700, 0x2ebe1),
        range(0x2f800, 0x2fa20),
        range(0x30000, 0x3134b)
    ), key=lambda r: r.start)

    RANGE_BEGINS = [r.start for r in RANGES]

    @classmethod
    def check_char(cls, char: str) -> bool:
        """
        Determine whether or not the given character is in the Unicode code point ranges assigned
        to Chinese and Japanese.
        """
        code_point = ord(char[0])
        if code_point < cls.RANGE_BEGINS[0]:
            return False
        else:
            idx = bisect.bisect_right(cls.RANGE_BEGINS, code_point)
            return code_point in cls.RANGES[idx - 1]


class NewLineBehavior:
    """
    Provides a callable to normalize *single* newline events while preserving intended breaks.
    Modes:
      - 'GUESS'  : choose ' ' for space-separated langs; '' for CJK.
      - 'SPACE'  : always replace with a single space.
      - 'REMOVE' : always remove (no space).
      - 'NONE'   : no change.

    Users can also provide a custom callable to augment NewLineBehavior.
    """

    Behavior = Union[
        Literal['GUESS', 'SPACE', 'REMOVE', 'NONE'],
        Callable[[str, Optional[str]], str],
        None

    ]

    @classmethod
    def get(cls, behavior: Behavior) -> Callable[[str, Optional[str]], str]:
        if callable(behavior):
            return behavior

        # Default to GUESS if None or invalid string
        if behavior is None:
            behavior = 'GUESS'

        behavior = behavior.upper()

        if behavior == 'GUESS':
            return lambda s, l: cls._replace_new_lines(s, cls._guess_lang_separator(s, l))
        elif behavior == 'REMOVE':
            return lambda s, _: cls._replace_new_lines(s, '')
        elif behavior == 'SPACE':
            return lambda s, _: cls._replace_new_lines(s, ' ')
        elif behavior == 'NONE':
            return lambda s, _: s
        else:
            raise mpf.DetectionError.INVALID_PROPERTY.exception(
                f'"{behavior}" is not a valid value for the "STRIP_NEW_LINE_BEHAVIOR" property. '
                'Valid value are GUESS, REMOVE, SPACE, NONE.')

    @staticmethod
    def _guess_lang_separator(text: str, language: Optional[str]) -> Literal['', ' ']:
        if language:
            if language.upper() in NO_SPACE_LANGS:
                return ''
            else:
                return ' '
        else:
            first_alpha_letter = next((ch for ch in text if ch.isalpha()), 'a')
            if ChineseAndJapaneseCodePoints.check_char(first_alpha_letter):
                return ''
            else:
                return ' '


    REPLACE_NEW_LINE_REGEX = re.compile(r'''
        \s? # Include preceding whitespace character if present
        (?<!\n) # Make sure previous character isn't a newline
        \n
        (?!\n) # Make sure next character isn't a newline
        \s? # Include next character if it is whitespace
        ''', flags=re.MULTILINE | re.IGNORECASE | re.UNICODE | re.DOTALL | re.VERBOSE)


    @classmethod
    def _replace_new_lines(cls, text: str, replacement: str) -> str:

        def do_replacement(match: Match[str]) -> str:
            match_text = match.group(0)
            if match_text == '\n':
                # Surrounding characters are not whitespace.
                return replacement
            else:
                # There is already whitespace next to newline character, so it can just be removed.
                return match_text.replace('\n', '', 1)

        return cls.REPLACE_NEW_LINE_REGEX.sub(do_replacement, text)