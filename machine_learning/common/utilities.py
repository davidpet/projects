import os
import inspect
import json


def _get_folder(dir=None):
    if dir is None:
        dir = os.path.dirname(inspect.stack()[2].filename)
    return dir


def load_data_file(file: str, dir=None) -> str:
    dir = _get_folder(dir)

    filepath = os.path.join(dir, file)
    with open(filepath, 'r') as f:
        return f.read().strip()


def load_json_data_file(file: str, dir=None) -> dict[str, str]:
    dir = _get_folder(dir)

    text = load_data_file(file, dir)
    return json.loads(text)


def load_data_files(files: dict[str, str], dir=None) -> dict[str, str]:
    mappings = {}
    dir = _get_folder(dir)

    for key, file in files.items():
        text = load_data_file(file=file, dir=dir)
        mappings[key] = text

    return mappings
