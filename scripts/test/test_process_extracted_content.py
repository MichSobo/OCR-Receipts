"""
Code for process_extracted_content.py unit tests.
"""
import json
import os
import shutil
import unittest

from scripts.content_detector import process_extracted_content


ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))


class TestGetExtractedContent(unittest.TestCase):
    """Test case for get_extracted_content()"""

    @classmethod
    def setUpClass(cls):
        # Create a sample text file, get path to it
        filename = 'sample_file.txt'
        with open(filename, 'w') as f:
            f.write('Sample content')
        cls.sample_txt_filepath = os.path.join(os.getcwd(), filename)

        # Create a sample json file, get path to it
        filename = 'sample_file.json'
        with open(filename, 'w') as f:
            json.dump({'sample_key': 'sample_value'}, f)
        cls.sample_json_filepath = os.path.join(os.getcwd(), filename)

    def test_case01(self):
        """test with not existing file"""
        self.assertRaises(FileNotFoundError,
                          process_extracted_content.get_content,
                          'not_existing_file.xxx')

    def test_case02(self):
        """test with a file with wrong format"""
        from json.decoder import JSONDecodeError
        self.assertRaises(JSONDecodeError,
                          process_extracted_content.get_content,
                          self.sample_txt_filepath)

    def test_case03(self):
        """test with a file with correct format"""
        data = process_extracted_content.get_content(self.sample_json_filepath)
        self.assertTrue(isinstance(data, dict))

    @classmethod
    def tearDownClass(cls):
        # Delete sample files
        os.remove(cls.sample_txt_filepath)
        os.remove(cls.sample_json_filepath)


if __name__ == '__main__':
    unittest.main()