import sys
import os

from machine_learning.common.openai_api import prompt, fetch_api_key
from machine_learning.common.utilities import load_data_files

SECTION_DELIM = '*' * 50

INPUTS = {
    'system': 'prompts/system.txt',
    'outline': 'prompts/outline.txt',
    'subtopics': 'prompts/subtopics.txt',
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
    """
    Create an outline using LLM and write it to a file.

    Args:
        topic (str): the programming language

    Returns:
        str: the outline
    """

    outline = prompt(system=data['system'].format(topic),
                     prompt=data['subtopics'].format(topic, data['outline']))
    outline = outline.replace('###', '').strip()
    outline = data['outline'] + '\n\n' + outline

    write_file('outline.txt', outline)

    return outline


def prompt_outline(topic: str) -> str:
    """
    Prompt user whether to create an outline and then either create or load it.

    Args:
        topic (str): the programming language

    Returns:
        str: the new or existing outline text
    """

    response = input(
        'Would you like to generate an outline? (Y or N): ').strip().lower()
    if 'y' in response:
        outline = create_outline(topic)
    else:
        outline_path = input(
            'Where is your existing outline located (full path)?: ')
        with open(outline_path, 'r') as f:
            outline = f.read()
    print_section('Outline')
    print(outline)


def main() -> int:
    topic = input('Please enter a topic: ').capitalize()

    if not fetch_api_key():
        print("ERROR: Could not get OpenAI API Key!")
        return 1

    global data
    data = load_data_files(INPUTS)

    outline = prompt_outline(topic)

    return 0


if __name__ == '__main__':
    sys.exit(main())
