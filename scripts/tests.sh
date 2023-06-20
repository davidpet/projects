#!/bin/bash

#TODO: continue working on this as it is not working yet
# it seems to be able to find tests for files that have dependencies in the top-level BUILD
# now, but not in lower-level BUILD files.

# Dependencies: python, git, bazel

# Get the git and workspace roots
git_root=$(git rev-parse --show-toplevel)
workspace_root=$(bazel info workspace)

# Function to calculate relative path
relative_path() {
  local src=$1
  local dst=$2
  python3 -c "import os.path; print(os.path.relpath('$src', '$dst'))"
}

# Get the list of modified/added files in the staging area or working copy from Git
unstaged_files=$(git diff --name-only --diff-filter=d)
staged_files=$(git diff --name-only --cached)

# Deduplicate the list of files and convert them to paths relative to the workspace root
all_files=$(echo -e "${unstaged_files}\n${staged_files}" | grep -v '^$' | sort -u | \
             while IFS= read -r file; do
               relative_path "$git_root/$file" "$workspace_root"
             done)

if [[ -z "$all_files" ]]; then
    echo "No files have changed. Nothing to do."
    exit 0
fi

echo "Changed files (relative to workspace root): ${all_files}"

prefixed_files=()
valid_targets=()

for file in $all_files; do
  IFS="/" read -ra path_parts <<< "$file"
  num_parts=${#path_parts[@]}

  variations=("//:$file")  # Add //: prefix version

  for ((i = 1; i < num_parts; i++)); do
    path_prefix=""
    for ((j = 0; j < i; j++)); do
      path_prefix+="${path_parts[j]}/"
    done

    path_suffix=""
    for ((k = i; k < num_parts; k++)); do
      path_suffix+="${path_parts[k]}/"
    done

    prefixed_file="//${path_prefix}:${path_suffix}"
    variations+=("$(echo "$prefixed_file" | sed 's:/*$::')")
  done

  prefixed_files+=("${variations[@]}")
done

echo "Valid Bazel targets:"
for target in "${prefixed_files[@]}"; do
  echo $target
  if bazel query --output=label "kind(rule, ${target})" >/dev/null 2>&1; then
    valid_targets+=" ${target}"
  fi
done
echo "${valid_targets[@]}"

bazel query --output=label "kind(test, rdeps(//..., set($valid_targets)))" | xargs bazel test
