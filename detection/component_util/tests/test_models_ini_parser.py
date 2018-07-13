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

from __future__ import division, print_function

import test_util
test_util.add_local_component_libs_to_sys_path()
import unittest
import tempfile
import shutil
import os

import mpf_component_util as mpf_util


MODELS_INI = """
[test_model]
string_field=hello world
int_field = 567
path_field=test_file.txt

[other_model]
string_field=other
int_field = 765
path_field=other_file.txt
"""


class ModelsIniParserTest(unittest.TestCase):

    def setUp(self):
        self._plugin_dir = tempfile.mkdtemp()
        self._plugin_models_dir = os.path.join(self._plugin_dir, 'models')
        os.mkdir(self._plugin_models_dir)
        with open(os.path.join(self._plugin_models_dir, 'models.ini'), 'w') as f:
            f.write(MODELS_INI)

        self._ModelSettings = (mpf_util.ModelsIniParser(self._plugin_models_dir)
                               .register_field('string_field')
                               .register_int_field('int_field')
                               .register_path_field('path_field')
                               .build_class())

        self._root_common_models_dir = tempfile.mkdtemp()
        self._common_models_dir = os.path.join(self._root_common_models_dir, 'test_component')

    def tearDown(self):
        shutil.rmtree(self._plugin_dir)
        shutil.rmtree(self._root_common_models_dir)


    def test_load_from_plugin_dir(self):
        test_file_path = os.path.join(self._plugin_models_dir, 'test_file.txt')
        with open(os.path.join(test_file_path), 'w') as f:
            f.write('test')

        model_settings = self._ModelSettings('test_model', self._common_models_dir)
        self.assertEqual('hello world', model_settings.string_field)
        self.assertEqual(567, model_settings.int_field)
        self.assertEqual(test_file_path, model_settings.path_field)


    def test_load_from_common_dir(self):
        os.mkdir(self._common_models_dir)
        test_file_path = os.path.join(self._common_models_dir, 'test_file.txt')
        with open(os.path.join(test_file_path), 'w') as f:
            f.write('test')

        model_settings = self._ModelSettings('test_model', self._common_models_dir)
        self.assertEqual('hello world', model_settings.string_field)
        self.assertEqual(567, model_settings.int_field)
        self.assertEqual(test_file_path, model_settings.path_field)


    def test_model_settings_class_is_reusable(self):
        test_file_path = os.path.join(self._plugin_models_dir, 'test_file.txt')
        with open(os.path.join(test_file_path), 'w') as f:
            f.write('test')

        other_file_path = os.path.join(self._plugin_models_dir, 'other_file.txt')
        with open(os.path.join(other_file_path), 'w') as f:
            f.write('test')

        for i in xrange(2):
            model_settings = self._ModelSettings('test_model', self._common_models_dir)
            self.assertEqual('hello world', model_settings.string_field)
            self.assertEqual(567, model_settings.int_field)
            self.assertEqual(test_file_path, model_settings.path_field)

            model_settings = self._ModelSettings('other_model', self._common_models_dir)
            self.assertEqual('other', model_settings.string_field)
            self.assertEqual(765, model_settings.int_field)
            self.assertEqual(other_file_path, model_settings.path_field)


    def test_prefers_common_models_dir(self):
        test_file_plugin_path = os.path.join(self._plugin_models_dir, 'test_file.txt')
        with open(os.path.join(test_file_plugin_path), 'w') as f:
            f.write('test')

        os.mkdir(self._common_models_dir)
        test_file_common_path = os.path.join(self._common_models_dir, 'test_file.txt')
        with open(os.path.join(test_file_common_path), 'w') as f:
            f.write('test')

        model_settings = self._ModelSettings('test_model', self._common_models_dir)
        self.assertEqual('hello world', model_settings.string_field)
        self.assertEqual(567, model_settings.int_field)
        self.assertEqual(test_file_common_path, model_settings.path_field)


    def test_throws_when_file_not_found(self):
        self.assertRaises(IOError, self._ModelSettings, 'test_model', self._common_models_dir)


    def test_unknown_model(self):
        with self.assertRaises(mpf_util.ModelNotFoundError) as err:
            self._ModelSettings('not_a_model', self._common_models_dir)

        self.assertEqual('not_a_model', err.exception.requested_model)
        self.assertItemsEqual(('test_model', 'other_model'), err.exception.available_models)

