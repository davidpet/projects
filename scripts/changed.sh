#!/bin/bash

# Format or lint modified files relative to latest commit
# using appropriate formatters/linters for file types.

# Example: changed format
# Example: changed lint

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
FILETYPES_DIR="${SCRIPT_DIR}/filetypes"

# Step 1: Get the list of modified/added files in the staging area or working copy from Git
repo_root=$(git rev-parse --show-toplevel)
# Get the list of files that have been changed in the working directory but not yet staged
unstaged_files=$(git diff --name-only --diff-filter=d | sed "s|^|${repo_root}/|")
# Get the list of files that have been staged for the next commit
staged_files=$(git diff --name-only --cached | sed "s|^|${repo_root}/|")
# Get the list of untracked files in the working directory
untracked_files=$(git ls-files --others --exclude-standard | sed "s|^|${repo_root}/|")

# Step 2: Deduplicate the list of files
# Combine the lists, remove empty lines, and deduplicate
all_files=$(echo -e "${unstaged_files}\n${staged_files}\n${untracked_files}" | grep -v '^$' | sort -u)
if [[ -z "$all_files" ]]; then
    echo "No files have changed. Nothing to do."
    exit 0
fi
echo "Changed files: ${all_files}"

# Step 3: Separate the list into separate lists based on file types
python_files=()
typescript_files=()
java_files=()
other_files=()

# File type specific 'lint' scripts
python_lint_script="${FILETYPES_DIR}/lint_python.sh"
typescript_lint_script="${FILETYPES_DIR}/lint_typescript.sh"
java_lint_script="${FILETYPES_DIR}/lint_java.sh"

# File type specific 'format' scripts
python_format_script="${FILETYPES_DIR}/format_python.sh"
typescript_format_script="${FILETYPES_DIR}/format_typescript.sh"
java_format_script="${FILETYPES_DIR}/format_java.sh"

# File types to exclude from the warning
excluded_file_types=("txt sh proto")  # Add any file types you want to exclude from the warning

# Aggregate errors
errors=""

# Loop through each file
while IFS= read -r file; do
    echo "File: ${file}"
    extension="${file##*.}"
    echo "Extension: ${extension}"

    case $extension in
        py)
            python_files+=("$file")
            ;;
        ts)
            typescript_files+=("$file")
            ;;
        json)
            typescript_files+=("$file")
            ;;
        js)
            typescript_files+=("$file")
            ;;
        java)
            java_files+=("$file")
            ;;
        *)
            if [[ ! " ${excluded_file_types[@]} " =~ " $extension " ]]; then
                other_files+=("$file")
            fi
            ;;
    esac
done <<< "$all_files"

# Step 4: Call the file type specific 'lint' and 'format' scripts
run_script() {
    local script="$1"
    shift
    local files=("$@")
    
     # If there are no files to process, do nothing
    if [ "${#files[@]}" -eq 0 ]; then
        return
    fi

    if [ -x "$script" ]; then
        "$script" "${files[@]}"
        if [ $? -ne 0 ]; then
            errors+="Error: Failed to run script '$script'\n"
        fi
    else
        errors+="Error: Script '$script' not found or not executable\n"
    fi
}

# Step 4a: Run 'lint' scripts for each file type
run_lint_scripts() {
    local filetype=$1
    shift 1
    local files=("$@")
    
    if [ ${#files[@]} -gt 0 ]; then
        case $filetype in
            py)
                run_script "$python_lint_script" "${files[@]}"
                ;;
            ts)
                run_script "$typescript_lint_script" "${files[@]}"
                ;;
            java)
                run_script "$java_lint_script" "${files[@]}"
                ;;
        esac
    fi
}

# Step 4b: Run 'format' scripts for each file type
run_format_scripts() {
    local filetype=$1
    shift 1
    local files=("$@")
    
    if [ ${#files[@]} -gt 0 ]; then
        case $filetype in
            py)
                run_script "$python_format_script" "${files[@]}"
                ;;
            ts)
                run_script "$typescript_format_script" "${files[@]}"
                ;;
            java)
                run_script "$java_format_script" "${files[@]}"
                ;;
        esac
    fi
}

# Step 4: Call the file type specific 'lint' or 'format' scripts
if [ "$1" == "lint" ]; then
    run_lint_scripts "py" "${python_files[@]}"
    run_lint_scripts "ts" "${typescript_files[@]}"
    run_lint_scripts "java" "${java_files[@]}"
else
    run_format_scripts "py" "${python_files[@]}"
    run_format_scripts "ts" "${typescript_files[@]}"
    run_format_scripts "java" "${java_files[@]}"
fi

# Step 5: Print warning for other files if not empty
if [ ${#other_files[@]} -gt 0 ]; then
    echo "Warning: The following files were not processed:"
    for file in "${other_files[@]}"; do
        echo "- $file"
    done
fi

# Step 6: Aggregate errors
if [ -n "$errors" ]; then
    echo "Lint errors were found!"
fi
