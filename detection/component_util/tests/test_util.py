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

import os
import sys


def add_local_component_libs_to_sys_path():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../api'))


def get_data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)


def is_all_same_color(image, color_tuple):
    return (image == color_tuple).all()


def is_all_black(image):
    return is_all_same_color(image, (0, 0, 0))


def is_all_white(image):
    return is_all_same_color(image, (255, 255, 255))