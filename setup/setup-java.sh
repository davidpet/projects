#!/bin/bash

# Dependencies: curl

# Get the directory of the script itself
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Specify the text file that contains the tool names and URLs
TOOL_URL_FILE="${SCRIPT_DIR}/java-tools.txt"

# Define the directory to store the tools
TOOL_DIR="${HOME}/java-tools"

# Create the directory if it doesn't exist
mkdir -p ${TOOL_DIR}

# Read the tool names and URLs from the text file
while read -r tool_name tool_url
do
  # Skip empty lines
  if [[ -z "${tool_name}" && -z "${tool_url}" ]]; then
    continue
  fi

  # Get the tool filename from the URL
  tool_filename=$(basename ${tool_url})

  # Check if the tool already exists in the directory
  if [[ -f "${TOOL_DIR}/${tool_filename}" ]]; then
    echo "${tool_filename} already downloaded."
  else
    # Download the tool
    echo "Downloading ${tool_name}..."
    curl -L ${tool_url} -o "${TOOL_DIR}/${tool_filename}"
    # Check if the download was successful
    if [[ $? -ne 0 ]]; then
        echo "Failed to download ${tool_filename}"
        # Remove the symlink if download failed
        rm -f "${TOOL_DIR}/${tool_name}"
        continue
    fi
  fi

  # Check if the final filename is different from the downloaded filename
  if [[ "${tool_filename}" != "${tool_name}" ]]; then
    # Check if the file is a zip file
    if [[ "${tool_filename}" == *.zip ]]; then
        # Create a directory with the same name as the zip file
        unzip_dir="${TOOL_DIR}/${tool_filename%.*}"
        mkdir -p "${unzip_dir}"
        # Unzip the file into the new directory
        echo "Unzipping ${tool_filename} into ${unzip_dir}..."
        unzip -q "${TOOL_DIR}/${tool_filename}" -d "${unzip_dir}"
        # Search for the tool_name in the unzipped files and create a symlink
        found_tool_path=$(find "${unzip_dir}" -type f -name "${tool_name}" -print -quit)
        if [[ -n "${found_tool_path}" ]]; then
        echo "Creating symlink ${tool_name}"
        ln -sf "${found_tool_path}" "${TOOL_DIR}/${tool_name}"
        else
        echo "Could not find ${tool_name} in unzipped files."
        fi
    else
        # Create the symlink
        echo "Creating symlink ${tool_name}"
        ln -sf "${TOOL_DIR}/${tool_filename}" "${TOOL_DIR}/${tool_name}"
    fi
  fi
done < ${TOOL_URL_FILE}
