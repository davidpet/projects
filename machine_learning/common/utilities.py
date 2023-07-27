"""Generic utilities for things like loading files."""

import os
import inspect
import json


def _get_folder(dir=None) -> str:
    """
    Get the folder containing the script calling this utility file, or
    the passed in one if provided.

    Args:
        dir (dir, optional): The dir to return instead if provided. Defaults to None.

    Returns:
        str: The folder path.
    """

    if dir is None:
        dir = os.path.dirname(inspect.stack()[2].filename)
    return dir


def load_data_file(file: str, dir: str | None = None) -> str:
    """
    Load a data file relative to either the folder of the calling
    script or the given directory.

    Args:
        file (str): Path of the file relative to calling script directory or dir.
        dir (str, optional): Optional override path. Defaults to None.

    Returns:
        str: Contents of the file as a string (beginning and end striped).
    """

    dir = _get_folder(dir)

    filepath = os.path.join(dir, file)
    with open(filepath, 'r') as f:
        return f.read().strip()


def load_json_data_file(file: str, dir: str | None = None) -> dict[str, str]:
    """
    Load a json data file relative to either the folder of the calling
    script or the given directory.

    Args:
        file (str): Path of the file relative to calling script directory or dir.
        dir (str, optional): Optional override path. Defaults to None.

    Returns:
        dict[str, str]: Contents of the file as a dictionary, which is
                        potentially multi-level.
    """

    dir = _get_folder(dir)

    text = load_data_file(file, dir)
    return json.loads(text)


def load_data_files(files: dict[str, str],
                    dir: str | None = None) -> dict[str, str]:
    """
    Load a collection of data files as strings relative to either the folder
    of the calling script or the given directory.

    Args:
        files (dict[str, str]): mapping of names to paths.
        dir (str, optional): Optional override path. Defaults to None.

    Returns:
        dict[str, str]: mapping of names to content.  Names are same as input.
    """

    mappings = {}
    dir = _get_folder(dir)

    for key, file in files.items():
        text = load_data_file(file=file, dir=dir)
        mappings[key] = text

    return mappings
