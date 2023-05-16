"""
Discovers and runs tests (files ending with _test.py) relative to a folder.

Because discovery in unittest is picky about how things are laid out,
I'll use my own discovery so I can have the layout that is best for my projects.

This depends on having PYTHONPATH set up as per the repo's README.

Usage: python3 -m test '~/repos/projects/common'
    This will run all tests found recursively in the common folder of projects.
Usage: python3 -m test
    This will run all tests found recursively in the whole repo.
Usage: python3 -m test '~/repos/projects/common/checks_test.py'
    This will run a specific python test file.
Usage: python3 -m test '~/repos/projects/common/checks'
    This will run checks_test.py because there's no 'checks' folder.
Usage: python3 -m test '~/repos/projects/common/checks_test.py/MyTestClass'
    This will run a specific class in a specific python file.
Usage: python3 -m test '~/repos/projects/common/checks_test.py/MyTestClass.test_method1'
    This will run a specific method in a specific python file.
"""

import sys
import os
import unittest
from typing import List

TEST_SUFFIX = '_test.py'

# The folder containing this module should be in PYTHONPATH per repo setup instructions.
module_root = os.path.dirname(__file__)

def make_module_name(path: str) -> str:
    rel_path = os.path.relpath(path, module_root)
    return rel_path.replace('/', '.')
    
def find_tests(root: str) -> List[str]:
    root = os.path.expanduser(root)

    tests = []

    # Recursive search
    if os.path.isdir(root):
        for folder, _, files in os.walk(root):
            for file in files:
                if file.endswith(TEST_SUFFIX):
                    file_path = os.path.join(folder, file[:-3])
                    tests.append(make_module_name(file_path))
    # Single .py file
    elif os.path.isfile(root):
        tests.append(make_module_name(root[:-3]))
    # Portion of .py file without the _test.py
    elif os.path.exists(root + TEST_SUFFIX):
        tests.append(make_module_name((root + TEST_SUFFIX)[:-3]))
    # Class.method specified after the .py file
    elif os.path.isfile('/'.join(root.split('/')[:-1])):
        root_components = root.split('/')
        file = '/'.join(root_components[:-1])
        method = root_components[-1]

        tests.append(make_module_name(file[:-3]) + '.' + method)

    return tests

def display_tests(tests: str) -> None:
    print(f'Test Files Found ({len(tests)}):')
    for test in tests:
        print(test)
    print()
    
if __name__=='__main__':
    if len(sys.argv) > 2:
        print('Usage: python3 -m test [root_or_file_path]/[method_name]')
        exit(1)
    
    search_path = module_root
    if len(sys.argv) > 1:
        search_path = sys.argv[1]
    
    tests = find_tests(search_path)
    display_tests(tests)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(tests)
    runner = unittest.TextTestRunner()
    
    runner.run(suite)
