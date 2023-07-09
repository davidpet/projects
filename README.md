## Requirements for using this repo

1. Python 3.11 environment (eg. via conda)
1. All appropriate conda/pip packages installed in current environment
   - tensorflow (GPU) (documentation TBD)
   - matplotlib
   - scikit-learn
   - pandas
   - jupyter (documentation TBD)
   - tensorflow_datasets
   - yapf
   - pylint
   - pytype (on hold until supports python 3.11)
   - termcolor
   - python_dotenv
   - openai
1. a conda environment called `bazel-protoc` that has Python 3.11 and nothing installed but `conda install grpcio-tools`.
   - This is a hack that is needed due to dependency hell between grpcio-tools and tensorflow.
   - NOTE: You do not need to activate that environment yourself for any commands - the bazel rules will handle themselves.
1. _PYTHONPATH_ set to the location of this repo so that you can import modules relative to it.
1. _PYLINTRC_ set to the .pylintrc file in this repo (TODO: revisit this procedure later).

## VSCode Setup

You probably want to set up setting sync and make a workspace for this repo (at least).

Recommended Extensions:

1.  Python (set the interpreter to the one for your environment)
1.  PyLint
1.  autoDocstring (google style)
1.  TensorFlow 2.0 Snippets
1.  Pandas Basic Snippets
1.  WSL (if on Windows using WSL)

Other Settings:

1.  Set yapf as formatting provider and add the args '--style' and 'google' for yapf

## Running Tests

For Python, testing is done via _test.py_ at the top of the repo. TODO: other languages (bazel to encapsulate?)

See the docstring at the top of that file for all the options.

Examples:

1. `python3 -m test`
   - whole repo
1. `python3 -m test ~/repos/projects/machine_learning.common`
   - some subfolder of the repo
1. `python3 -m test ~/repos/projects/machine_learning.common.checks_tests.py`
   - single file
1. `python3 -m test ~/repos/projects/machine_learning.common.checks_tests.py/ChecksTests.test_check_condition_false`
   - single method

## Before Commiting (TODO: make a hook)

1. `yapf --style google --recursive --in-place [repoPath]`
   - TODO: other languages too (for now manually Format Document in VSCode when change)
1. `pylint [repoPath]`
   - TODO: other languages too
   - NOTE: this will catch more things than pylint in VSCode will catch
1. TODO: type checking step when pytype is ready for 3.11
1. Manually run formatting in jupyter notebooks changed
1. `python3 -m test`
   - TODO: other languages (probably use Bazel or similar to handle dependencies and such)
