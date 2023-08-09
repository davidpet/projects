import sys
import re
import nbformat as nbf
import nbformat.v4 as nbf4

from machine_learning.common.openai_api import prompt, fetch_api_key
from machine_learning.common.utilities import load_data_files

SECTION_DELIM = '*' * 50

INPUTS = {
    'system': 'prompts/system.txt',
    'outline': 'prompts/outline.txt',
    'subtopics': 'prompts/subtopics.txt',
    'snippet': 'prompts/snippet.txt',
}

OUTPUTS = {
    'outline': 'outline.txt',
}

data = None


class Section:
    """
    A section within the outline for a programming language.

    Main title and subtopic titles do not contain the leading numbering here.
    """

    title: str
    subtopics: list[str]

    def __init__(self, title: str, subtopics: list[str]):
        """
        Create a new instance.

        Args:
            title (str): the section title (with numbering to strip)
            subtopics (list[str]): subtopic titles (with numbering to strip)
        """

        self.title = self._remove_annotation(title)
        self.subtopics = [
            self._remove_annotation(subtopic) for subtopic in subtopics
        ]

    def _remove_annotation(self, title: str) -> str:
        """Strip initial numbering from a title string."""

        return re.sub(r'^\s*\S+\s*', '', title, count=1)


class Outline():
    """Parses outline text into list of Section objects."""

    sections: list[Section]

    def __init__(self, text):
        lines = text.split('\n')
        section_lines = []

        section_start = 0
        for i in range(len(lines) + 1):
            if i == len(lines) or not lines[i].strip():
                section_end = i
                if section_start != section_end:
                    section_lines.append(lines[section_start:section_end])
                section_start = i + 1

        self.sections = [
            Section(section[0], section[1:]) for section in section_lines
        ]


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

    return outline


def create_snippets(topic: str, kernel: str, outline: Outline,
                    count: int) -> None:
    """
    Create snippets.

    Args:
        topic (str): programming language
        kernel (str): the Jupyter notebook kernel to use
        outline (Outline): the outline of topics and subtopics for snippets
        count (int): number of topics from beginning of outline to create.
                     This allows for testing without the system going crazy.
    """

    print(f'Using kernel {kernel}')

    for i in range(count):
        section = outline.sections[i]
        print(f'Generating notebook for {section.title}.')

        # Create a new notebook w/ appropriate kernel info
        notebook = nbf4.new_notebook()
        notebook.metadata.kernelspec = {
            "name": kernel,
            "display_name": topic,
            "language": topic.lower(),
        }

        for subtopic in section.subtopics:
            print(f'\tGenerating snippet for {subtopic}')

            # Get the AI summary and code cell content for each subtopic
            llm_response = prompt(prompt=data['snippet'].format(
                topic, section.title, subtopic),
                                  system=data['system']).strip()
            split_index = llm_response.find('#####')
            if split_index == -1:
                markdown_content = ''
                code_content = llm_response
            else:
                markdown_content = llm_response[6 + split_index:].strip()
                code_content = llm_response[:split_index].strip()

            # The AI wants to wrap the code in markdown so let's play along
            # (Trying to fix it via prompt may cause context confusion)
            code_content = re.sub(r'^\s*```\S*\s*$',
                                  '',
                                  code_content,
                                  flags=re.MULTILINE).strip()

            # Diagnostics
            #print('-code-')
            #print(code_content)
            #print('-markdown-')
            #print(markdown_content)

            # Add a title+summary markdown cell for each subtopic
            markdown = nbf4.new_markdown_cell(
                f'# {subtopic}\n{markdown_content}')
            notebook.cells.append(markdown)

            # Add a code snippet cell for each subtopic
            code = nbf4.new_code_cell(code_content)
            notebook.cells.append(code)

        # Write to disk (ends up in bazel-bin)
        with open(section.title.replace('/', ', ') + '.ipynb', 'w') as f:
            nbf.write(notebook, f)


def prompt_snippets(topic: str, outline: Outline) -> None:
    """
    Ask user how many snippets to create and then create them.

    User can just hit enter to generate all for outline.
    Invalid input will just show error.
    0 will pass through silently and do nothing.

    Args:
        topic (str): programming language
        outline (Outline): outline to use for snippet generation
    """

    print(SECTION_DELIM)
    response = input(
        'How many notebooks would you like to generate? (just hit Enter for max): '
    ).strip()

    if not response:
        # Empty = all
        count = len(outline.sections)
    else:
        try:
            # Non-empty = expect integer
            count = int(response)
            # Clip to max of range
            if count > len(outline.sections):
                count = len(outline.sections)
        except:
            # Invalid input = generate nothing
            count = 0
            print('ERROR: Invalid count!')
        if count < 0:
            # Clip to min of range
            count = 0

    if count:
        kernel = input(
            'What is the kernel to use for notebooks? (Default to i + language lowercased): '
        ).strip()
        if not kernel:
            kernel = 'i' + topic.lower()

        print_section('Snippets')
        create_snippets(topic, kernel, outline, count)


def main() -> int:
    topic = input('Please enter a topic: ').capitalize()

    if not fetch_api_key():
        print("ERROR: Could not get OpenAI API Key!")
        return 1

    global data
    data = load_data_files(INPUTS)

    outline = prompt_outline(topic)
    prompt_snippets(topic, Outline(outline))

    return 0


if __name__ == '__main__':
    sys.exit(main())
