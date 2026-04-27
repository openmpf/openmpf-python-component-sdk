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

import pathlib
import unittest

from nlp_text_splitter import TextSplitterModel, TextSplitter, SentencePieces
from nlp_text_splitter.newline_behavior import NewLineBehavior


TEST_DATA = pathlib.Path(__file__).parent / 'test_data'


class ConfigurableMockSplitter:
    """
    Reusable fake sentence splitter for contrived branch-coverage tests.

    Modes:
      - "empty_list"        : return []
      - "empty_string_list" : return [""]
      - "whole"             : return [text]
      - "pieces"            : return the configured pieces
      - "callback"          : call the configured callback(text, lang)
    """

    def __init__(self, mode="whole", pieces=None, callback=None, name="ConfigurableMockSplitter"):
        self.mode = mode
        self.pieces = list(pieces or [])
        self.callback = callback
        self.name = name
        self.calls = []

    def split(self, text, lang=None):
        self.calls.append((text, lang))
        # Uncomment to debug particular mock tests.
        # print(f"DEBUG [{self.name}] mode={self.mode} lang={lang!r} text={text[:80]!r}")

        if self.mode == "empty_list":
            return []
        if self.mode == "empty_string_list":
            return [""]
        if self.mode == "whole":
            return [text]
        if self.mode == "pieces":
            return list(self.pieces)
        if self.mode == "callback":
            if self.callback is None:
                raise AssertionError("callback mode requires a callback")
            return list(self.callback(text, lang))

        raise AssertionError(f"Unknown ConfigurableMockSplitter mode: {self.mode}")


class TestTextSplitter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wtp_model = TextSplitterModel("wtp-bert-mini", "cpu", "en")
        cls.wtp_adv_model = TextSplitterModel("wtp-canine-s-1l", "cpu", "zh")
        cls.spacy_model = TextSplitterModel("xx_sent_ud_sm", "cpu", "en")
        cls.sat_model = TextSplitterModel("sat-3l-sm", "cpu", "en")


    def _make_splitter(self, text, limit, model, get_size_fn=len, **kwargs):
        return TextSplitter(
            text=text,
            limit=limit,
            num_boundary_chars=0,
            get_text_size=get_size_fn,
            sentence_model=model,
            **kwargs
        )

    def test_sat_basic_sentence_split(self):
        input_text = 'Hello, what is your name? My name is John.'
        actual = list(TextSplitter.split(input_text,
            100,
            100,
            len,
            self.sat_model,
            split_mode='SENTENCE'))
        self.assertEqual(2, len(actual))
        self.assertEqual('Hello, what is your name? ', actual[0])
        self.assertEqual('My name is John.', actual[1])



    def test_split_engine_difference(self):
        # Note: Only WtP's multilingual models
        # can detect some of '。' characters used for this language.
        text = (TEST_DATA / 'art-of-war.txt').read_text()

        text_without_newlines = text.replace('\n', '')

        actual = self.wtp_model._split_wtp(text_without_newlines)
        self.assertEqual(3, len(actual))
        for line in actual:
            self.assertTrue(line.endswith('。'))

        actual = self.spacy_model._split_spacy(text_without_newlines)
        self.assertEqual(1, len(actual))

        # However, WtP prefers newlines over the '。' character.
        actual = self.wtp_model._split_wtp(text)
        self.assertEqual(10, len(actual))

        # SaT seems to try to split using additional features, in addition to newlines.
        actual = self.sat_model._split_sat(text)
        self.assertFalse(any(s == "" for s in actual))
        self.assertEqual(15, len(actual))

    def test_guess_split_simple_sentence(self):
        input_text = 'Hello, what is your name? My name is John. C. Finn.'

        # WtP Produces a clean split.
        actual = list(TextSplitter.split(input_text,
            30,
            30,
            len,
            self.wtp_model))
        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(2, len(actual))

        # "Hello, what is your name?"
        self.assertEqual('Hello, what is your name? ', actual[0])
        # " My name is John."
        self.assertEqual('My name is John. C. Finn.', actual[1])

        # Seems SaT is a bit more aggressive at splitting text.
        actual = list(TextSplitter.split(input_text,
            500,
            500,
            len,
            self.sat_model,
            split_mode='SENTENCE'))
        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(3, len(actual))

        # "Hello, what is your name?"
        self.assertEqual('Hello, what is your name? ', actual[0])
        # " My name is John."
        self.assertEqual('My name is John. ', actual[1])
        self.assertEqual('C. Finn.', actual[2])

        actual = list(TextSplitter.split(input_text,
            28,
            28,
            len,
            self.spacy_model))
        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(2, len(actual))

        # "Hello, what is your name?"
        self.assertEqual('Hello, what is your name? ', actual[0])
        # " My name is John."
        self.assertEqual('My name is John. C. Finn.', actual[1])

    def test_split_sentence_end_punctuation(self):
        input_text = 'Hello. How are you? asdfasdf'
        actual = list(TextSplitter.split(input_text,
            20,
            10,
            len,
            self.wtp_model))

        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(2, len(actual))

        self.assertEqual('Hello. How are you? ', actual[0])
        self.assertEqual('asdfasdf', actual[1])

        actual = list(TextSplitter.split(input_text,
            20,
            10,
            len,
            self.spacy_model))

        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(2, len(actual))

        self.assertEqual('Hello. How are you? ', actual[0])
        self.assertEqual('asdfasdf', actual[1])


    def test_guess_split_edge_cases(self):
        input_text = ("This is a sentence (Dr.Test). Is this,"
                      " a sentence as well? Maybe...maybe not?"
                      " \n All done, I think!")

        # Split using WtP model.
        actual = list(TextSplitter.split(input_text,
            30,
            30,
            len,
            self.wtp_model,
            newline_behavior = "NONE"))

        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(4, len(actual))

        # WtP should detect and split out each sentence
        self.assertEqual("This is a sentence (Dr.Test). ", actual[0])
        self.assertEqual("Is this, a sentence as well? ", actual[1])
        self.assertEqual("Maybe...maybe not? \n ", actual[2])
        self.assertEqual("All done, I think!", actual[3])

        # Split using WtP model.
        actual = list(TextSplitter.split(input_text,
            30,
            30,
            len,
            self.wtp_model,
            newline_behavior = "GUESS"))

        self.assertEqual(input_text.replace('\n',''), ''.join(actual))
        self.assertEqual(4, len(actual))

        # WtP should detect and split out each sentence
        self.assertEqual("This is a sentence (Dr.Test). ", actual[0])
        self.assertEqual("Is this, a sentence as well? ", actual[1])
        self.assertEqual("Maybe...maybe not?  ", actual[2])
        self.assertEqual("All done, I think!", actual[3])


        actual = list(TextSplitter.split(input_text,
            35,
            35,
            len,
            self.spacy_model,
            newline_behavior = "NONE"))
        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(4, len(actual))

        # Split using spaCy model.
        self.assertEqual("This is a sentence (Dr.Test). ", actual[0])
        self.assertEqual("Is this, a sentence as well? ", actual[1])
        self.assertEqual("Maybe...maybe not? \n ", actual[2])
        self.assertEqual("All done, I think!", actual[3])


    def test_split_wtp_basic(self):
        text = (TEST_DATA / 'art-of-war.txt').read_text().replace('\n','')
        actual = list(TextSplitter.split(text,
            150,
            150,
            len,
            self.wtp_model))

        self.assertEqual(4, len(actual))

        expected_chunk_lengths = [86, 116, 104, 114]
        self.assertEqual(sum(expected_chunk_lengths), len(text.replace('\n','')))

        self.assertTrue(actual[0].startswith('兵者，'))
        self.assertTrue(actual[0].endswith('而不危也；'))
        self.assertEqual(expected_chunk_lengths[0], len(actual[0]))

        self.assertTrue(actual[1].startswith('天者，陰陽'))
        self.assertTrue(actual[1].endswith('兵眾孰強？'))
        self.assertEqual(expected_chunk_lengths[1], len(actual[1]))

        self.assertTrue(actual[2].startswith('士卒孰練？'))
        self.assertTrue(actual[2].endswith('遠而示之近。'))
        self.assertEqual(expected_chunk_lengths[2], len(actual[2]))

        self.assertTrue(actual[3].startswith('利而誘之，'))
        self.assertTrue(actual[3].endswith('勝負見矣。'))
        self.assertEqual(expected_chunk_lengths[3], len(actual[3]))

    def test_split_wtp_advanced(self):
        text = (TEST_DATA / 'art-of-war.txt').read_text().replace('\n','')
        actual = list(TextSplitter.split(text,
            150,
            150,
            len,
            self.wtp_adv_model))

        self.assertEqual(4, len(actual))

        expected_chunk_lengths = [61, 150, 61, 148]
        self.assertEqual(sum(expected_chunk_lengths), len(text.replace('\n','')))

        self.assertTrue(actual[0].startswith('兵者，'))
        self.assertTrue(actual[0].endswith('四曰將，五曰法。'))
        self.assertEqual(expected_chunk_lengths[0], len(actual[0]))

        self.assertTrue(actual[1].startswith('道者，令民於上同意'))
        self.assertTrue(actual[1].endswith('賞罰孰明'))
        self.assertEqual(expected_chunk_lengths[1], len(actual[1]))

        self.assertTrue(actual[2].startswith('？吾以此知勝'))
        self.assertTrue(actual[2].endswith('因利而制權也。'))
        self.assertEqual(expected_chunk_lengths[2], len(actual[2]))

        self.assertTrue(actual[3].startswith('兵者，詭道也。'))
        self.assertTrue(actual[3].endswith('之，勝負見矣。'))
        self.assertEqual(expected_chunk_lengths[3], len(actual[3]))


    def test_isolate_largest_section_empty_sentence_list(self):
        # Confirm edge case where splitter fails to identify a split.
        model = ConfigurableMockSplitter(mode="empty_list", name="empty_list_case")
        splitter = self._make_splitter(
            text="Alpha beta gamma.",
            limit=10,
            model=model
        )

        # Confirm that the isolate_largest_section logic works in this extreme case.
        result = splitter._isolate_largest_section("Alpha beta gamma.")
        self.assertEqual("Alpha beta gamma.", result)

    def test_isolate_largest_section_empty_string_list_piece(self):
        # Confirm edge case where splitter fails to identify a split.
        # This variant introduces one element in the list that's also empty.
        model = ConfigurableMockSplitter(mode="empty_string_list", name="list_with_empty_string_case")
        splitter = self._make_splitter(
            text="Alpha beta gamma.",
            limit=10,
            model=model
        )

        result = splitter._isolate_largest_section("Alpha beta gamma.")
        self.assertEqual("Alpha beta gamma.", result)

    def test_sentence_mode_oversized_sentence_uses_split_sentence_text(self):
        # Confirm that sentence splitting logic is triggered if the splitter can't identify boundary.
        model = ConfigurableMockSplitter(mode="whole", name="whole_sentence_case")
        long_text = "one two three four five six seven eight nine ten"

        splitter = self._make_splitter(
            text=long_text,
            limit=5,
            model=model,
            get_size_fn=lambda s: len(s.split()),
            split_mode="SENTENCE"
        )

        is_called = {"called": False}
        orig = splitter._split_sentence_text

        def wrapped(text):
            is_called["called"] = True
            yield from orig(text)

        splitter._split_sentence_text = wrapped

        chunks = list(splitter._split())
        self.assertTrue(is_called["called"])
        self.assertEqual(chunks, ['one two three four five ', 'six seven eight nine ten'])
        self.assertGreater(len(chunks), 1)

    def test_divide_hits_preferred_limit_branch(self):
        # Confirm that preferred limit is reached.
        text = "one two three. four five six. seven eight."
        model = ConfigurableMockSplitter(
            mode="pieces",
            pieces=["one two three. ", "four five six. ", "seven eight."],
            name="preferred_branch_case"
        )

        chunks = list(TextSplitter.split(
            text=text,
            limit=100,
            num_boundary_chars=0,
            get_text_size=lambda s: len(s.split()),
            sentence_model=model,
            split_mode="DEFAULT",
            preferred_limit=4
        ))

        self.assertEqual(
            ['one two three. four five six. ', 'seven eight.'],
            chunks
        )
        self.assertEqual(text, "".join(chunks))

    def test_mid_word_protection_with_whitespace_backup(self):
        # Confirm that backing up to nearest whitespace works where possible.
        text = "hello world oopsbackup"
        model = ConfigurableMockSplitter(mode="whole", name="midword_whitespace_case")

        chunks = list(TextSplitter.split(
            text=text,
            limit=100,
            num_boundary_chars=0,
            get_text_size=len,
            sentence_model=model,
            preferred_limit=12
        ))

        self.assertEqual(['hello world ', 'oopsbackup'], chunks)
        self.assertEqual(text, "".join(chunks))

    def test_mid_word_protection_no_whitespace_available(self):
        # Confirm that raw text is split if whitespace backup fails.
        text = "averyveryverylongtoken"
        model = ConfigurableMockSplitter(mode="whole", name="midword_no_whitespace_case")

        from nlp_text_splitter import TextSplitter
        chunks = list(TextSplitter.split(
            text=text,
            limit=100,
            num_boundary_chars=0,
            get_text_size=len,
            sentence_model=model,
            preferred_limit=5
        ))

        self.assertEqual(['avery', 'veryv', 'erylo', 'ngtok', 'en'], chunks)
        self.assertEqual(text, "".join(chunks))

    def test_divide_hits_char_per_size_recalculation(self):
        # Confirm that text splitting works in more unusual text size recalculation scenarios.
        # Also to examine if future changes trigger changes in recalculated splits.
        text = "abcdefghij klmnopqrst uvwxyz"
        model = ConfigurableMockSplitter(mode="whole", name="char_per_size_case")

        def weird_size(s):
            value = max(1, len(s) * 2)
            return value

        chunks = list(TextSplitter.split(
            text=text,
            limit=10,
            num_boundary_chars=0,
            get_text_size=weird_size,
            sentence_model=model,
            preferred_limit=-1
        ))

        self.assertEqual(['abcd', 'efgh', 'ij ', 'klmn', 'opqr', 'st ', 'uvwx', 'yz'], chunks)
        self.assertEqual(text, "".join(chunks))

    def test_sat_basic_sentence_split_preserved_whitespace(self):
        # Confirm that using a standard splitter ensures proper reconstruction of whitespace.
        # This uses the whitespace reconstruction logic introduced to SaT splitters.
        input_text = 'Hello, what is your name?            My name is John.'
        actual = list(TextSplitter.split(input_text,
            100,
            100,
            len,
            self.sat_model,
            split_mode='SENTENCE'))
        self.assertEqual(2, len(actual))
        self.assertEqual('Hello, what is your name?            ', actual[0])
        self.assertEqual('My name is John.', actual[1])

    def test_compute_breakpoints_from_sentences_hits_alignment_helper(self):
        # Confirm that using a non-standard splitter ensures proper reconstruction of whitespace.
        model = ConfigurableMockSplitter(
            mode="pieces",
            pieces=["Alpha beta.", "Gamma delta.", "Epsilon zeta."],
            name="breakpoint_alignment_case"
        )
        # Excess whitespace is ignored by the splitter.
        text = "Alpha beta.    Gamma delta.  Epsilon zeta."

        # Split by 4 words, if possible.
        chunks = list(TextSplitter.split(
            text=text,
            limit=100,
            num_boundary_chars=0,
            get_text_size=lambda s: len(s.split()),
            sentence_model=model,
            preferred_limit=4
        ))
        # TextSplitter should properly identify where each breakpoint exists from the truncated pieces.
        # And properly split the input text at the second sentence.
        self.assertEqual(
            ['Alpha beta.    Gamma delta. ', ' Epsilon zeta.'],
            chunks
        )
        self.assertEqual(text, "".join(chunks))


    def test_newline_behavior_none_defaults_to_guess(self):
        fn = NewLineBehavior.get(None)
        out = fn("hello\nworld", "en")
        self.assertEqual("hello world", out)

    def test_newline_behavior_space_remove_none(self):
        text = "abc\ndef"

        out_space = NewLineBehavior.get("SPACE")(text, None)
        self.assertEqual("abc def", out_space)

        out_remove = NewLineBehavior.get("REMOVE")(text, None)
        self.assertEqual("abcdef", out_remove)

        out_none = NewLineBehavior.get("NONE")(text, None)
        self.assertEqual("abc\ndef", out_none)

    def test_guess_lang_separator(self):
        sep = NewLineBehavior._guess_lang_separator("こんにちは\n世界", None)
        self.assertEqual("", sep)

        sep = NewLineBehavior._guess_lang_separator("hello\nworld", None)
        self.assertEqual(" ", sep)

        sep = NewLineBehavior._guess_lang_separator("ignored", "ja")
        self.assertEqual("", sep)

        sep = NewLineBehavior._guess_lang_separator("ignored", "en")
        self.assertEqual(" ", sep)

    def test_replace_new_lines_isolated_newline_branch(self):
        text = "abc\ndef"
        out = NewLineBehavior.get("SPACE")(text, None)
        self.assertEqual("abc def", out)

    def test_divide_empty_left_fallback_makes_progress(self):
        """
        Force the defensive fallback:
            if left == "" and text != "":
                left = text[:1]

        This branch is hard to reach naturally with the current guards, so we
        simulate it by making _isolate_largest_section() return an empty string.
        """
        model = ConfigurableMockSplitter(mode="whole", name="empty_left_fallback_case")

        splitter = self._make_splitter(
            text="abcdef",
            limit=3,
            model=model,
            get_size_fn=len,
            preferred_limit=-1
        )

        # Force the legacy branch path to produce an empty left segment.
        splitter._isolate_largest_section = lambda text: ""

        left, right = splitter._divide("abcdef")

        self.assertEqual("a", left)
        self.assertEqual("bcdef", right)

if __name__ == '__main__':
    unittest.main(verbosity=2)
