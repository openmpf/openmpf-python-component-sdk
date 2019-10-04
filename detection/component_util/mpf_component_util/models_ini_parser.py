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

from __future__ import division, print_function

import ConfigParser
import os


class ModelsIniParser(object):
    def __init__(self, plugin_models_dir):
        self._plugin_models_dir = plugin_models_dir
        self._fields = []

    def register_field(self, name, field_type=str):
        self._fields.append(_FieldInfo(name, field_type, False))
        return self

    def register_optional_field(self, name, default_value=None, field_type=str):
        self._fields.append(_FieldInfo(name, field_type, True, default_value))
        return self


    def register_int_field(self, name):
        return self.register_field(name, int)

    def register_optional_int_field(self, name, default_value=None):
        return self.register_optional_field(name, default_value, int)


    def register_float_field(self, name):
        return self.register_field(name, float)

    def register_optional_float_field(self, name, default_value=None):
        return self.register_optional_field(name, default_value, float)

    def register_path_field(self, name):
        self._fields.append(_PathFieldInfo(name, None, False))
        return self

    def register_optional_path_field(self, name, default_value=None):
        self._fields.append(_PathFieldInfo(name, None, True, default_value))
        return self

    def build_class(self):
        plugin_models_dir = self._plugin_models_dir
        fields = list(self._fields)

        class ModelSettings(object):
            def __init__(self, model_name, common_models_dir):
                config = ConfigParser.RawConfigParser()
                models_ini_full_path = _get_full_path('models.ini', plugin_models_dir, common_models_dir)
                config.read(models_ini_full_path)

                for field_info in fields:
                    try:
                        field_info.set_field(config, model_name, self, plugin_models_dir, common_models_dir)
                    except ConfigParser.NoSectionError:
                        raise ModelNotFoundError(models_ini_full_path, model_name, config.sections())
                    except ConfigParser.NoOptionError:
                        raise ModelMissingRequiredFieldError(models_ini_full_path, model_name, field_info.name)
                    except _PathEmptyError:
                        raise ModelEmptyPathError(models_ini_full_path, model_name, field_info.name)
                    except _TypeConversionError as e:
                        raise ModelTypeConversionFailed(models_ini_full_path, model_name, field_info.name, e.message)
        return ModelSettings


def _get_full_path(file_name, plugin_models_dir, common_models_dir):
    file_name = _expand_path(file_name)
    if file_name[0] == '/':
        possible_locations = (file_name,)
    else:
        possible_locations = (_expand_path(common_models_dir, file_name), _expand_path(plugin_models_dir, file_name))

    for possible_location in possible_locations:
        if os.path.exists(possible_location):
            return possible_location

    raise ModelFileNotFoundError(possible_locations)


def _expand_path(path, *paths):
    return os.path.expandvars(os.path.expanduser(os.path.join(path, *paths)))


class _FieldInfo(object):
    def __init__(self, name, field_type, is_optional, default_value=None):
        self.name = name
        self._field_type = field_type
        self._is_optional = is_optional
        self._default_value = default_value


    def set_field(self, config, model_name, model_settings, plugin_models_dir, common_models_dir):
        if not self._is_optional or config.has_option(model_name, self.name):
            try:
                string_value = config.get(model_name, self.name)
                converted_value = self.convert_value(string_value, plugin_models_dir, common_models_dir)
            except ValueError as e:
                raise _TypeConversionError(e.message)
        else:
            converted_value = self.convert_default_value(self._default_value, plugin_models_dir, common_models_dir)

        setattr(model_settings, self.name, converted_value)


    def convert_value(self, string_value, plugin_models_dir, common_models_dir):
        return self._field_type(string_value)

    @staticmethod
    def convert_default_value(value, plugin_models_dir, common_models_dir):
        return value


class _PathFieldInfo(_FieldInfo):
    def convert_value(self, string_value, plugin_models_dir, common_models_dir):
        if len(string_value) == 0:
            raise _PathEmptyError()
        return _get_full_path(string_value, plugin_models_dir, common_models_dir)

    @staticmethod
    def convert_default_value(value, plugin_models_dir, common_models_dir):
        return _get_full_path(value, plugin_models_dir, common_models_dir) if value else value


class _PathEmptyError(Exception):
    pass

class _TypeConversionError(Exception):
    pass



class ModelsIniError(Exception):
    pass


class ModelNotFoundError(ModelsIniError):
    def __init__(self, models_ini_path, requested_model, available_models):
        super(ModelNotFoundError, self).__init__(
            'Failed to load the requested model named "%s", because it was not one of the models listed in the model '
            'configuration file located at "%s". The available models are %s'
            % (requested_model, models_ini_path, available_models))
        self.models_ini_path = models_ini_path
        self.requested_model = requested_model
        self.available_models = available_models



class ModelEmptyPathError(ModelsIniError):
    def __init__(self, models_ini_path, model_name, field_name):
        super(ModelEmptyPathError, self).__init__(
            'Failed to the load the requested model named "%s", '
            'because the "%s" field was empty in the [%s] section of the configuration file located at "%s"'
            % (model_name, field_name, model_name, models_ini_path))
        self.models_ini_path = models_ini_path
        self.model_name = model_name
        self.field_name = field_name


class ModelMissingRequiredFieldError(ModelsIniError):
    def __init__(self, models_ini_path, model_name, field_name):
        super(ModelMissingRequiredFieldError, self).__init__(
            'Failed to the load the requested model named "%s", '
            'because the "%s" field was not present in the [%s] section of the configuration file located at "%s"'
            % (model_name, field_name, model_name, models_ini_path))
        self.models_ini_path = models_ini_path
        self.model_name = model_name
        self.field_name = field_name


class ModelFileNotFoundError(IOError, ModelsIniError):
    def __init__(self, possible_locations):
        super(ModelFileNotFoundError, self).__init__(
            'Failed to load model because a required file was not present. '
            'Expected a file to exist at one of the following locations: %s' % (possible_locations,))
        self.possible_locations = possible_locations


class ModelTypeConversionFailed(ModelsIniError):
    def __init__(self, models_ini_path, model_name, field_name, reason):
        super(ModelTypeConversionFailed, self).__init__(
            'Failed to the load the requested model named "%s", '
            'because the "%s" field in the [%s] section of the configuration file located at "%s" was not able to '
            'be converted to the specified type due to: %s'
            % (model_name, field_name, model_name, models_ini_path, reason))
        self.models_ini_path = models_ini_path
        self.model_name = model_name
        self.field_name = field_name
