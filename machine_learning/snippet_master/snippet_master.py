import sys
import os

from machine_learning.common.openai_api import prompt, fetch_api_key
from machine_learning.common.utilities import load_data_files

SECTION_DELIM = '*' * 50

INPUTS = {
    'system': 'prompts/system.txt',
    'outline': 'prompts/outline.txt',
}

OUTPUTS = {
    'outline': 'outline.txt',
}

data = None


def write_file(path: str, text: str) -> None:
    with open(path, 'w') as f:
        f.write(text)


def print_section(section: str) -> None:
    print(SECTION_DELIM)
    print(section)
    print(SECTION_DELIM)


def create_outline(topic: str) -> str:
    outline = prompt(system=data['system'].format(topic),
                     prompt=data['outline'].format(topic))
    print_section('Outline')
    print(outline)
    write_file('outline.txt', outline)

    return outline


def main() -> int:
    topic = input('Please enter a topic: ').capitalize()

    if not fetch_api_key():
        print("ERROR: Could not get OpenAI API Key!")
        return 1

    global data
    data = load_data_files(INPUTS)

    outline = create_outline(topic)

    return 0


if __name__ == '__main__':
    sys.exit(main())
