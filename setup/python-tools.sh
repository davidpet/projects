SETUP_FOLDER="$(dirname "${BASH_SOURCE[0]}")"
PROJECTS_FOLDER="$(dirname "$SETUP_FOLDER")"

# Make my shared python libraries available to scripts and notebooks.
# TODO: make this less system dependent
export PYTHONPATH=${PROJECTS_FOLDER}:$PYTHONPATH

# Use my copy of the pylintrc file for pylint rc configuration.
export PYLINTRC=${PROJECTS_FOLDER}/.pylintrc

# Format given .py files.
function format-python() {
    yapf --style google --in-place "$@"
}
# Format all .py files recursively in a folder.
function format-python-all() {
    yapf --style google --in-place --recursive "$@"
}

# Lint a list of .py files.
# TODO: figure out why PYLINTRC variable doesn't work on mac.
function lint-python() {
  pylint --rcfile "$PYLINTRC" "$@"
}
# Recursively lint all .py files in a folder
# Wrap a tool that runs on a list of files to run on a folder.
function run_tool_recursive() {
    local tool=$1
    local dir=$2

    local files=( $(find "${dir}" -name "*.py") )
    ${tool} ${files[@]}
}
function lint-python-all() {
  run_tool_recursive lint-python "$1"
}
