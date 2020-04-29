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

import collections
import inspect
import os
from typing import ClassVar, Type


def type_converter(obj, class_or_factory):
    if inspect.isclass(class_or_factory) and isinstance(obj, class_or_factory):
        return obj
    return class_or_factory(obj)


class FieldTypes(object):
    """
    Class decorator that adds properties that check the argument type before assigning to the underlying field.
    """
    def __init__(self, **kwargs):
        """
        :param kwargs: The key is the name of the field and the value is either a class
                        or a function that converts a value to that class.
        """
        self.types_dict = kwargs


    def __call__(self, clazz):
        for field, field_type in self.types_dict.items():
            prop = FieldTypes.create_property('_' + field, field_type)
            # Add the new property to the decorated class
            setattr(clazz, field, prop)

        ctor_args = [a for a in inspect.getfullargspec(clazz.__init__).args if a in self.types_dict]

        FieldTypes.add_equals_methods(clazz, ctor_args)
        FieldTypes.add_to_string_method(clazz, ctor_args)
        return clazz


    # Creates a property descriptor. The getter just returns the underlying field.
    # The setter makes sure the RHS of the assignment is of the correct type.
    @staticmethod
    def create_property(member_var_name, field_type):
        def getter(instance):
            # Just return the backing field
            return getattr(instance, member_var_name, None)

        def setter(instance, val):
            # Make sure val is instance of field_type when trying to assign
            setattr(instance, member_var_name, type_converter(val, field_type))

        return property(getter, setter)

    @staticmethod
    def add_to_string_method(clazz, ctor_args):
        str_is_overridden = hasattr(clazz, '__repr__') and clazz.__repr__ != object.__repr__
        if not str_is_overridden:
            clazz.__repr__ = FieldTypes.create_string_fn(ctor_args)


    @staticmethod
    def create_string_fn(fields):
        def to_string(instance):
            fields_string = ', '.join('%s = %s' % (f, getattr(instance, f)) for f in fields)
            return '%s { %s }' % (type(instance).__name__, fields_string)
        return to_string


    @staticmethod
    def add_equals_methods(clazz, ctor_args):
        if '__eq__' not in clazz.__dict__:
            clazz.__eq__ = lambda s, o: all(getattr(s, f) == getattr(o, f) for f in ctor_args)
            clazz.__ne__ = lambda s, o: not s.__eq__(o)
            clazz.__hash__ = None


class TypedDict(collections.MutableMapping):
    """
    Behaves identically to a regular dict, except when inserting new items.
    When inserting new items the types of the key and value are checked.
    """
    key_type: ClassVar[Type] = object
    value_type: ClassVar[Type] = object

    def __init__(self, *args, **kwargs):
        super(TypedDict, self).__init__()
        self._dict = dict()
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        typed_key = type_converter(key, self.key_type)
        typed_value = type_converter(value, self.value_type)
        return self._dict.__setitem__(typed_key, typed_value)

    # Everything else just calls through to the underlying dict

    def __delitem__(self, key):
        return self._dict.__delitem__(key)

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._dict.__iter__()

    def __str__(self):
        return self._dict.__str__()


def create_if_none(val, func):
    if val is None:
        return func()
    else:
        return val


def get_full_log_path(filename):
    log_dir = os.path.expandvars('$MPF_LOG_PATH/$THIS_MPF_NODE/log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, filename)
    return os.path.expandvars(log_path)


def get_log_name(filename):
    log_name, _ = os.path.splitext(os.path.basename(filename if filename else ''))
    return log_name if log_name else 'component_logger'
