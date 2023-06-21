"""Tests for checks.py."""

import unittest

from machine_learning.common import checks


class ChecksTests(unittest.TestCase):
    """Tests for checks.py"""

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.printed = ''

    def make_fake_print(self):

        def fake_print(*args, **kwargs):
            self.printed = str(args) + str(kwargs)

        return fake_print

    def test_check_condition_false(self):
        checks.check_condition(False, 'THE PREFIX', self.make_fake_print())

        # TODO: find out why color codes get stripped in bazel context
        # and put them back here.
        # It doesn't just happen on print but also on any creation using
        # termcolor or colored packages.
        self.assertEqual(r"('THE PREFIX: Fail',){}", self.printed)

    def test_check_condition_true(self):
        checks.check_condition(True, 'THE PREFIX', self.make_fake_print())

        self.assertEqual(r"('THE PREFIX: Pass',){}", self.printed)


if __name__ == '__main__':
    unittest.main()
