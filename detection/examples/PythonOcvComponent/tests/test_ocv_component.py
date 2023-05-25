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

from pathlib import Path
import unittest

import mpf_component_api as mpf

from ocv_component import OcvComponent

TEST_DATA = Path(__file__).parent / 'data'


class TestOcvComponent(unittest.TestCase):

    def test_image(self):
        job = mpf.ImageJob('test', str(TEST_DATA / 'test.png'), {}, {})
        component = OcvComponent()
        results = list(component.get_detections_from_image(job))
        self.assertEqual(2, len(results))

        self.assertEqual(300, results[0].x_left_upper)
        self.assertEqual(0, results[0].y_left_upper)



if __name__ == '__main__':
    unittest.main(verbosity=2)
