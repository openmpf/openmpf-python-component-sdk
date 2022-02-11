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
