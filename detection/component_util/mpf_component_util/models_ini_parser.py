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

import ConfigParser
import os


class ModelsIniParser(object):
    def __init__(self, plugin_models_dir):
        self._plugin_models_dir = plugin_models_dir
        self._fields = {}
        self._path_fields = set()

    def register_field(self, name, type_=str):
        self._fields[name] = type_
        return self

    def register_int_field(self, name):
        return self.register_field(name, int)

    def register_float_field(self, name):
        return self.register_field(name, float)

    def register_path_field(self, name):
        self._path_fields.add(name)
        return self

    def build_class(self):
        plugin_models_dir = self._plugin_models_dir
        fields = dict(self._fields)
        path_fields = set(self._path_fields)

        class ModelSettings(object):
            def __init__(self, model_name, common_models_dir):
                config = ConfigParser.RawConfigParser()
                models_ini_full_path = _get_full_path('models.ini', plugin_models_dir, common_models_dir)
                config.read(models_ini_full_path)

                try:
                    for field_name, field_type in fields.iteritems():
                        raw_field_value = config.get(model_name, field_name)
                        setattr(self, field_name, field_type(raw_field_value))

                    for field_name in path_fields:
                        raw_field_value = config.get(model_name, field_name)
                        setattr(self, field_name, _get_full_path(raw_field_value, plugin_models_dir, common_models_dir))
                except ConfigParser.NoSectionError:
                    raise ModelNotFoundError(models_ini_full_path, model_name, config.sections())

        return ModelSettings


class ModelNotFoundError(Exception):
    def __init__(self, models_ini_full_path, requested_model, available_models):
        args = (requested_model, models_ini_full_path, available_models)
        super(ModelNotFoundError, self).__init__(
            'Failed to load the requested model named "%s", because it was not one of the models listed in the model '
            'configuration file located at "%s". The available models are %s'
            % args, args)
        self.models_ini_full_path = models_ini_full_path
        self.requested_model = requested_model
        self.available_models = available_models


def _get_full_path(file_name, plugin_models_dir, common_models_dir):
    file_name = _expand_path(file_name)
    if file_name[0] == '/':
        possible_locations = (file_name,)
    else:
        possible_locations = (_expand_path(common_models_dir, file_name), _expand_path(plugin_models_dir, file_name))

    for possible_location in possible_locations:
        if os.path.exists(possible_location):
            return possible_location

    error_msg = 'Failed to load model because a required file was not present. Expected a file to exist at '
    if file_name[0] == '/':
        error_msg += '"%s".' % file_name
    else:
        error_msg += 'either "%s" or "%s".' % (possible_locations[0], possible_locations[1])
    raise IOError(error_msg)


def _expand_path(path, *paths):
    return os.path.expandvars(os.path.expanduser(os.path.join(path, *paths)))
