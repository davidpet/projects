"""Tests for utilities.py."""

import unittest
import os

# Loading indirectly so we can easily test the difference between provided dir
# and not provided.  Otherwise, it would be ambiguous if the path to the file
# was the same in both cases.
from machine_learning.common.utilities_test_data import subfolder_module as indirect


class UtilitiesTests(unittest.TestCase):
    """Tests for utilities.py"""

    FILE_TXT_CONTENT = 'Hello!\nHow are you?'
    FILE_TXT_NAME = 'file.txt'
    FILE_TXT_PATH = 'utilities_test_data/file.txt'

    FILE_JSON_NAME = 'file.json'
    FILE_JSON_PATH = 'utilities_test_data/file.json'
    FILE_JSON_CONTENT = {
        "field1": "value1",
        "field2": 100,
        "field3": {
            "subfield1": 200
        }
    }

    FILES_INPUT = {
        'bla1': 'file.txt',
        'bla2': 'otherfile.txt',
    }
    FILES_INPUT_WITH_PATHS = {
        'bla1': 'utilities_test_data/file.txt',
        'bla2': 'utilities_test_data/otherfile.txt',
    }
    FILES_OUTPUT = {
        'bla1': FILE_TXT_CONTENT,
        'bla2': 'yo!',
    }

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.printed = ''

    def test_load_data_file_with_dir(self):
        text = indirect.load_data_file(UtilitiesTests.FILE_TXT_PATH,
                                       dir=os.path.dirname(__file__))

        self.assertEqual(text, UtilitiesTests.FILE_TXT_CONTENT)

    def test_load_data_file_with_no_dir(self):
        text = indirect.load_data_file(UtilitiesTests.FILE_TXT_NAME)

        self.assertEqual(text, UtilitiesTests.FILE_TXT_CONTENT)

    def test_load_json_data_file_with_dir(self):
        text = indirect.load_json_data_file(UtilitiesTests.FILE_JSON_PATH,
                                            dir=os.path.dirname(__file__))

        self.assertEqual(text, UtilitiesTests.FILE_JSON_CONTENT)

    def test_load_json_data_file_with_no_dir(self):
        text = indirect.load_json_data_file(UtilitiesTests.FILE_JSON_NAME)

        self.assertEqual(text, UtilitiesTests.FILE_JSON_CONTENT)

    def test_load_data_files_with_dir(self):
        data = indirect.load_data_files(UtilitiesTests.FILES_INPUT_WITH_PATHS,
                                        dir=os.path.dirname(__file__))

        self.assertEqual(data, UtilitiesTests.FILES_OUTPUT)

    def test_load_data_files_with_no_dir(self):
        data = indirect.load_data_files(UtilitiesTests.FILES_INPUT)

        self.assertEqual(data, UtilitiesTests.FILES_OUTPUT)


if __name__ == '__main__':
    unittest.main()
