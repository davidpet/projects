import unittest
from unittest.mock import patch

import machine_learning.common.checks as checks


class ChecksTests(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.printed = ''

    def make_fake_print(self):

        def fake_print(*args, **kwargs):
            self.printed = str(args) + str(kwargs)

        return fake_print

    def test_check_condition_false(self):
        with patch('builtins.print', new=self.make_fake_print()):
            checks.check_condition(False, 'THE PREFIX')

        self.assertEqual(
            r"('\x1b[2m\x1b[34mTHE PREFIX\x1b[0m: \x1b[31mFail\x1b[0m',){}",
            self.printed)

    def test_check_condition_true(self):
        with patch('builtins.print', new=self.make_fake_print()):
            checks.check_condition(True, 'THE PREFIX')

        self.assertEqual(
            r"('\x1b[2m\x1b[34mTHE PREFIX\x1b[0m: \x1b[32mPass\x1b[0m',){}",
            self.printed)
