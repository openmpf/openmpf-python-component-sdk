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

import configparser
import os
from typing import Any, Collection, Callable, List, Optional

import mpf_component_api as mpf


class ModelsIniParser(object):
    def __init__(self, plugin_models_dir: str):
        self._plugin_models_dir = plugin_models_dir
        self._fields: List[_FieldInfo] = []

    def register_field(self, name: str, field_type: Callable[[str], Any] = str) -> 'ModelsIniParser':
        self._fields.append(_FieldInfo(name, field_type, False))
        return self

    def register_optional_field(self, name: str, default_value=None, field_type: Callable[[str], Any] = str) \
            -> 'ModelsIniParser':
        self._fields.append(_FieldInfo(name, field_type, True, default_value))
        return self


    def register_int_field(self, name: str) -> 'ModelsIniParser':
        return self.register_field(name, int)

    def register_optional_int_field(self, name: str, default_value: Optional[int] = None):
        return self.register_optional_field(name, default_value, int)


    def register_float_field(self, name: str) -> 'ModelsIniParser':
        return self.register_field(name, float)

    def register_optional_float_field(self, name: str, default_value: Optional[float] = None):
        return self.register_optional_field(name, default_value, float)


    def register_path_field(self, name: str) -> 'ModelsIniParser':
        self._fields.append(_PathFieldInfo(name, None, False))
        return self

    def register_optional_path_field(self, name: str, default_value: Optional[str] = None) -> 'ModelsIniParser':
        self._fields.append(_PathFieldInfo(name, None, True, default_value))
        return self

    def build_class(self):
        plugin_models_dir = self._plugin_models_dir
        fields = list(self._fields)

        class ModelSettings(object):
            def __init__(self, model_name, common_models_dir):
                config = configparser.RawConfigParser()
                models_ini_full_path = _get_full_path('models.ini', plugin_models_dir, common_models_dir)
                config.read(models_ini_full_path)

                for field_info in fields:
                    try:
                        field_info.set_field(config, model_name, self, plugin_models_dir,
                                             common_models_dir)
                    except configparser.NoSectionError as e:
                        raise ModelNotFoundError(models_ini_full_path, model_name,
                                                 config.sections()) from e
                    except configparser.NoOptionError as e:
                        raise ModelMissingRequiredFieldError(models_ini_full_path, model_name,
                                                             field_info.name) from e
                    except _PathEmptyError as e:
                        raise ModelEmptyPathError(models_ini_full_path, model_name,
                                                  field_info.name) from e
                    except _TypeConversionError as e:
                        raise ModelTypeConversionError(models_ini_full_path, model_name,
                                                       field_info.name, str(e)) from e
        return ModelSettings


def _get_full_path(file_name, plugin_models_dir, common_models_dir):
    file_name = _expand_path(file_name)
    if file_name[0] == '/':
        possible_locations: Collection[str] = (file_name,)
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
                raise _TypeConversionError(str(e)) from e
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



class ModelsIniError(mpf.DetectionException):
    pass


class ModelNotFoundError(ModelsIniError):
    models_ini_path: str
    requested_model: str
    available_models: Collection[str]

    def __init__(self, models_ini_path: str, requested_model: str,
                 available_models: Collection[str]):
        super().__init__(
            f'Failed to load the requested model named "{requested_model}", '
            f'because it was not one of the models listed in the model configuration file located '
            f'at "{models_ini_path}". The available models are {available_models}',
            mpf.DetectionError.COULD_NOT_OPEN_DATAFILE)
        self.models_ini_path = models_ini_path
        self.requested_model = requested_model
        self.available_models = available_models



class ModelEmptyPathError(ModelsIniError):
    models_ini_path: str
    model_name: str
    field_name: str

    def __init__(self, models_ini_path: str, model_name: str, field_name: str):
        super().__init__(
            f'Failed to the load the requested model named "{model_name}", '
            f'because the "{field_name}" field was empty in the [{model_name}] section of the '
            f'configuration file located at "{models_ini_path}"',
            mpf.DetectionError.COULD_NOT_READ_DATAFILE)
        self.models_ini_path = models_ini_path
        self.model_name = model_name
        self.field_name = field_name


class ModelMissingRequiredFieldError(ModelsIniError):
    models_ini_path: str
    model_name: str
    field_name: str

    def __init__(self, models_ini_path: str, model_name: str, field_name: str):
        super().__init__(
            f'Failed to the load the requested model named "{model_name}", '
            f'because the "{field_name}" field was not present in the [{model_name}] section of '
            f'the configuration file located at "{models_ini_path}"',
            mpf.DetectionError.COULD_NOT_READ_DATAFILE)
        self.models_ini_path = models_ini_path
        self.model_name = model_name
        self.field_name = field_name


class ModelFileNotFoundError(ModelsIniError, IOError):
    possible_locations: Collection[str]

    def __init__(self, possible_locations: Collection[str]):
        super(ModelsIniError, self).__init__(
            'Failed to load model because a required file was not present. '
            f'Expected a file to exist at one of the following locations: {possible_locations}',
            mpf.DetectionError.COULD_NOT_OPEN_DATAFILE)
        self.possible_locations = possible_locations


class ModelTypeConversionError(ModelsIniError):
    models_ini_path: str
    model_name: str
    field_name: str
    reason: str

    def __init__(self, models_ini_path: str, model_name: str, field_name: str, reason: str):
        super().__init__(
            f'Failed to the load the requested model named "{model_name}", '
            f'because the "{field_name}" field in the [{model_name}] section of the configuration '
            f'file located at "{models_ini_path}" was not able to be converted to the specified '
            f'type due to: {reason}',
            mpf.DetectionError.COULD_NOT_READ_DATAFILE)
        self.models_ini_path = models_ini_path
        self.model_name = model_name
        self.field_name = field_name
        self.reason = reason
