#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2023 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2023 The MITRE Corporation                                      #
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

from nlp_text_splitter import TextSplitterModel, TextSplitter


TEST_DATA = pathlib.Path(__file__).parent / 'test_data'

class TestTextSplitter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wtp_model = TextSplitterModel("wtp-bert-mini", "cpu", "en")
        cls.wtp_adv_model = TextSplitterModel("wtp-canine-s-1l", "cpu", "zh")
        cls.spacy_model = TextSplitterModel("xx_sent_ud_sm", "cpu", "en")

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

    def test_guess_split_simple_sentence(self):
        input_text = 'Hello, what is your name? My name is John.'
        actual = list(TextSplitter.split(input_text,
            28,
            28,
            len,
            self.wtp_model))
        self.assertEqual(input_text, ''.join(actual))
        self.assertEqual(2, len(actual))

        # "Hello, what is your name?"
        self.assertEqual('Hello, what is your name? ', actual[0])
        # " My name is John."
        self.assertEqual('My name is John.', actual[1])

        input_text = 'Hello, what is your name? My name is John.'
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
        self.assertEqual('My name is John.', actual[1])

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

        print(actual)
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
