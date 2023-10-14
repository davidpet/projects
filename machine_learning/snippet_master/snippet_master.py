import sys
import re
import os
import shutil
import nbformat as nbf
import nbformat.v4 as nbf4

from machine_learning.common.openai_api import prompt, fetch_api_key
from machine_learning.common.utilities import load_data_files

SECTION_DELIM = '*' * 50

INPUTS = {
    'system': 'prompts/system.txt',
    'outline_oop': 'prompts/outline_oop.txt',
    'outline_query': 'prompts/outline_query.txt',
    'subtopics': 'prompts/subtopics.txt',
    'snippet': 'prompts/snippet.txt',
}

OUTPUTS = {
    'outline': 'outline.txt',
}

OUTLINE_MENU = '''Which outline would you like to use?
1. OOP (eg. Java, C++, TypeScript, etc.)
2. Query (eg. SQL)

Enter number (default 1): '''

OUTLINE_MENU_CHOICES = [
    'outline_oop',
    'outline_query',
]

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


class VirtualNotebookFactory:
    """Interface for notebook creation."""

    def create(self):
        pass

    def set_kernel_info(self, name: str, display_name: str,
                        language: str) -> None:
        pass

    def create_subtopic(self, subtopic: str) -> None:
        pass

    def add_markdown(self, content: str) -> None:
        pass

    def add_code_snippet(self, code: str) -> None:
        pass

    def save(self, name: str):
        pass


class JupyterNotebookFactory(VirtualNotebookFactory):
    """Jupyter notebook creation."""

    def __init__(self):
        self.notebook = None

    def create(self):
        self.notebook = nbf4.new_notebook()

    def set_kernel_info(self, name: str, display_name: str,
                        language: str) -> None:
        self.notebook.metadata.kernelspec = {
            "name": name,
            "display_name": display_name,
            "language": language,
        }

    def create_subtopic(self, subtopic: str) -> None:
        pass

    def add_markdown(self, content: str) -> None:
        markdown = nbf4.new_markdown_cell(content)
        self.notebook.cells.append(markdown)

    def add_code_snippet(self, code: str) -> None:
        code_cell = nbf4.new_code_cell(code)
        self.notebook.cells.append(code_cell)

    def save(self, name: str):
        with open(name + '.ipynb', 'w') as f:
            nbf.write(self.notebook, f)


class CodeFileFactory(VirtualNotebookFactory):
    """Creation of direct code files when Jupyter won't work."""

    TEMP_FOLDER = 'CodeFileFactory_temp'

    def __init__(self, extension: str):
        self.extension = extension
        self.count = 0
        self.subtopic = ''

        self.code_files = []

    def __next_name(self) -> str:
        return '{:03}'.format(self.count)

    def create(self):
        if os.path.exists(self.TEMP_FOLDER):
            shutil.rmtree(self.TEMP_FOLDER)
        os.mkdir(self.TEMP_FOLDER)

        self.count = 0
        self.code_files = []

    def set_kernel_info(self, name: str, display_name: str,
                        language: str) -> None:
        pass

    def create_subtopic(self, subtopic: str) -> None:
        self.subtopic = subtopic

    def add_markdown(self, content: str) -> None:
        with open(
                os.path.join(
                    self.TEMP_FOLDER,
                    self.__next_name() + ' - ' + self.subtopic +
                    ' - explanation.md'), 'w') as f:
            f.write(content)

    def add_code_snippet(self, code: str) -> None:
        filename = self.__next_name(
        ) + ' - ' + self.subtopic + ' - snippet.' + self.extension

        with open(os.path.join(self.TEMP_FOLDER, filename), 'w') as f:
            f.write(code)
        self.count += 1
        self.code_files.append(filename)

    def save(self, name: str):
        with open(os.path.join(self.TEMP_FOLDER, 'BUILD'), 'w') as f:
            for code_file in self.code_files:
                f.write(self.extension + "_binary (\n")
                f.write('  name = "' + os.path.splitext(code_file)[0].replace(
                    '/', '_').replace(' ', '_') + '",\n')
                f.write('  srcs = ["' + code_file + '"],\n')
                f.write(')\n')
                f.write('\n')

        if os.path.exists(name):
            shutil.rmtree(name)
        os.rename(self.TEMP_FOLDER, name)


def write_file(path: str, text: str) -> None:
    with open(path, 'w') as f:
        f.write(text)


def print_section(section: str) -> None:
    print(SECTION_DELIM)
    print(section)
    print(SECTION_DELIM)


def create_outline(topic: str, outline_template: str) -> str:
    """
    Create an outline using LLM and write it to a file.

    Args:
        topic (str): the programming language
        outline_template (str): the outline to use

    Returns:
        str: the outline
    """

    outline = prompt(system=data['system'].format(topic),
                     prompt=data['subtopics'].format(topic, outline_template))
    outline = outline.replace('###', '').strip()
    outline = outline_template + '\n\n' + outline

    write_file(OUTPUTS['outline'], outline)

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
        which_template = int(input(OUTLINE_MENU).strip() or 1) - 1
        if which_template < 0 or which_template >= len(OUTLINE_MENU_CHOICES):
            raise 'Invalid outline template choice!'
        outline_template = data[OUTLINE_MENU_CHOICES[which_template]]
        outline = create_outline(topic, outline_template)
    else:
        outline_path = input(
            'Where is your existing outline located (full path)?: ')
        with open(outline_path, 'r') as f:
            outline = f.read()
    print_section('Outline')
    print(outline)

    return outline


def create_snippets(
    topic: str,
    kernel: str,
    outline: Outline,
    count: int,
    use_python=False,
    notebook_factory: VirtualNotebookFactory = JupyterNotebookFactory()
) -> None:
    """
    Create snippets.

    Args:
        topic (str): programming language
        kernel (str): the Jupyter notebook kernel to use
        outline (Outline): the outline of topics and subtopics for snippets
        count (int): number of topics from beginning of outline to create.
                     This allows for testing without the system going crazy.
        use_python (bool): to override kernel and language info.
                     This allows for extensions that use Python cells instead
                     of their own kernels.
        notebook_factory (VirtualNotebookFactory): Factory for creating
                     notebooks.  Defaults to Jupyter notebooks, which is
                     usually what we want, but some languages don't have
                     fully functional kernels available, so we have to
                     have a workaround.
    """

    if not use_python:
        print(f'Using kernel {kernel}')
    else:
        print(f'Using python cells!')

    for i in range(count):
        section = outline.sections[i]
        print(f'Generating notebook for {section.title}.')

        # Create a new notebook w/ appropriate kernel info
        notebook_factory.create()
        if use_python:
            notebook_factory.set_kernel_info('python3', 'Python 3 (ipykernel)',
                                             'python')
        else:
            notebook_factory.set_kernel_info(kernel, topic, topic.lower())

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

            notebook_factory.create_subtopic(subtopic.replace('/', ', '))

            # Add a title+summary markdown cell for each subtopic
            notebook_factory.add_markdown(f'# {subtopic}\n{markdown_content}')

            # Add a code snippet cell for each subtopic
            notebook_factory.add_code_snippet(code_content)

        # Write to disk (ends up in bazel-bin)
        notebook_factory.save(section.title.replace('/', ', '))


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
        override_jupyter = (input(
            'Do you need to override Jupyter notebook creation, and if so, ' +
            'what extension should we use? (Default no override): ').strip().
                            lower())
        if override_jupyter:
            kernel = None
            unique_kernel = True  # just stop it from using Python
        if not override_jupyter:
            unique_kernel = (input(
                'Does this language have its own kernel? (Y or N - default Y): '
            ).strip().lower() or 'y') == 'y'
            kernel = None
            if unique_kernel:
                kernel = input(
                    'What is the kernel to use for notebooks? (Default to i + language lowercased): '
                ).strip()
                if not kernel:
                    kernel = 'i' + topic.lower()

        print_section('Snippets')
        create_snippets(topic,
                        kernel,
                        outline,
                        count,
                        use_python=not unique_kernel,
                        notebook_factory=CodeFileFactory(override_jupyter)
                        if override_jupyter else JupyterNotebookFactory())


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
