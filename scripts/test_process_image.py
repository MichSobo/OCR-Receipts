"""
Code for process_image.py unit testing.
"""
import unittest

import process_image


class TestReadImage(unittest.TestCase):
    """Test case for read_image()"""

    def test_case01(self):
        """tests with not existing file"""
        self.assertRaises(FileNotFoundError, process_image.read_image, 'not_existing_file.jpg')


if __name__ == '__main__':
    unittest.main(verbosity=2)
