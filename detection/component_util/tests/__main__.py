#! /usr/bin/env python

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

import os
import sys
import unittest

if __name__ == '__main__':
    print('Running unit tests for Python component utilities ...', file=sys.stderr)
    print('----------------------------------------------------------------------', file=sys.stderr)

    test_argv = list(sys.argv)
    if len(test_argv) == 1:
        test_argv.extend((
            'discover',
            '--start-directory', os.path.dirname(__file__),
            '--buffer',  # Only show test stdout and stderr when the test fails
            '--verbose'
        ))

    unittest.main(argv=test_argv)
