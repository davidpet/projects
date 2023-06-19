#!/bin/bash

# TODO: maybe add spotbugs (but probably on the bazel side)

# Dependencies:
#   JDK (with JAVA_HOME) setup locally
#   setup-java.sh has been run
#   buildifier target has been set up in bazel workspace

TOOL_DIR="${HOME}/java-tools"
SETUP_FOLDER="$(dirname "${BASH_SOURCE[0]}")"

# runs on workspace
function buildifier() {
    bazel run //:buildifier
}

# runs on list of files
function google-java-format() {
    java -jar ${TOOL_DIR}/google-java-format.jar --replace "$@"
}

# runs on list of files
function checkstyle() {
    java -cp ${TOOL_DIR}/checkstyle.jar com.puppycrawl.tools.checkstyle.Main -c /google_checks.xml "$@"
}

# runs on folder or single file (not list)
# rules configured via pmd-rules.xml
function pmd() {
    ${TOOL_DIR}/pmd check -d "$1" -f text -R ${SETUP_FOLDER}/pmd-rules.xml
}

# Wrap a tool that runs on a list of files to run on a folder.
function run_tool_recursive() {
    local tool=$1
    local dir=$2

    local files=( $(find "${dir}" -name "*.java") )
    ${tool} ${files[@]}
}

# runs on a folder
function google-java-format-all() {
    run_tool_recursive google-java-format "$1" 
}

# runs on a folder
function checkstyle-all() {
    run_tool_recursive checkstyle "$1"
}

# Wrap a tool that runs on a single file to run on a list.
function run_tool_on_each_file() {
    local tool=$1
    shift 1
    local files="$@"

    for file in ${files[@]}; do
        ${tool} "${file}"
    done
}

# runs on a list of files
function pmd-list() {
    run_tool_on_each_file pmd "$@"
}

# generic convenience functions
function format-java() {
    google-java-format "$@"
}

function lint-java() {
    checkstyle "$@"
    pmd-list "$@"
}

function format-java-all() {
    google-java-format-all "$1"
}

function lint-java-all() {
    checkstyle-all "$1"
    pmd "$1"
}
