"""This file is here to call utilities functions from within this folder."""

from machine_learning.common import utilities

def load_data_file(file: str, dir: str | None = None) -> str:
    return utilities.load_data_file(file, dir)


def load_json_data_file(file: str, dir: str | None = None) -> dict[str, str]:
   return utilities.load_json_data_file(file, dir)


def load_data_files(files: dict[str, str],
                    dir: str | None = None) -> dict[str, str]:
    return utilities.load_data_files(files, dir)
