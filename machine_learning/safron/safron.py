"""SAFRON - Self Argumentation for Refinement of Notions"""

import sys
from collections import namedtuple
from io import StringIO

from termcolor import colored

from machine_learning.common import utilities
from machine_learning.common.openai_api import fetch_api_key, Chat, prompt, StringDictionary, GPT4_MODEL, GPT3_5_MODEL

# TODO: fix GPT 3.5 reversing polarity of arguments (reword system messages)
# TODO: fix GPT 3.5 not separating the arguments in summary like GPT 4 does
# TODO: consider open-ended rounds (w/ iterative summaries) where user decides
#       when to terminate (instead of pre-choosing # rounds)
# TODO: append and prepend some stuff to filename (eg. ~ and .txt)

# TODO: break this file apart (maybe) and unit test it (definitely)
# TODO: finish type annotations and docstrings

AFFIRMATIVE_LABEL = 'Affirmative'
NEGATIVE_LABEL = 'Negative'
SUMMARY_LABEL = 'Summary'

AFFIRMATIVE_COLOR = 'green'
NEGATIVE_COLOR = 'red'
SUMMARY_COLOR = 'blue'

SafronOptions = namedtuple(
    'SafronOptions', ['topic', 'rounds', 'filename', 'model', 'temperature'])


def debate(chat1: Chat, chat2: Chat, rounds: int, file) -> None:
    for i in range(rounds):
        print(f'\n***ROUND {i+1} OF {rounds}***\n')

        pos_msg = chat1.predict_assistant_msg()
        chat2.add_user_msg(pos_msg)
        output_debate_msg(msg=pos_msg,
                          label=AFFIRMATIVE_LABEL,
                          color=AFFIRMATIVE_COLOR,
                          file=file)

        neg_msg = chat2.predict_assistant_msg()
        chat1.add_user_msg(neg_msg)
        output_debate_msg(msg=neg_msg,
                          label=NEGATIVE_LABEL,
                          color=NEGATIVE_COLOR,
                          file=file)


def output_debate_msg(msg: str, label: str, color: str, file) -> None:
    print(f'{colored(label, color)}:', msg)
    print()

    print(f'[{label}]\n{msg}', file=file)
    print(file=file)
    print(file=file)


def output_summary_msg(summary: str, file) -> None:
    print(f'{colored("Summary", "blue")}:\n{summary}')
    print()

    print('[Summary]\n', summary, file=file)
    print(file=file)


def summarize_debate(chat: Chat, system: str, model: str, temperature: float,
                     disk_file):
    messages = [
        f'{msg["role"]}: {msg["content"]}' for msg in chat.messages
        if msg['role'] != 'system'
    ]
    summary = prompt(prompt='\n\n'.join(messages),
                     system=system,
                     model=model,
                     temperature=temperature)
    output_summary_msg(summary, disk_file)


def setup_environment() -> StringDictionary | None:
    if not fetch_api_key():
        print('ERROR: API key not found!')
        return None

    return utilities.load_data_files(
        files={
            'affirmative': 'messages/system_affirmative.txt',
            'negative': 'messages/system_negative.txt',
            'summary': 'messages/system_summary.txt',
        })


def gather_options_from_user() -> SafronOptions:
    topic = input('Please enter debate topic: ').strip()
    rounds = int(input('Enter number of rounds: ').strip())
    filename = input('Enter a filename: ').strip()
    if input('Use GPT 4 instead of 3.5? (Default N): ').strip().lower() == 'y':
        model = GPT4_MODEL
    else:
        model = GPT3_5_MODEL
    temperature = float(
        input('Please enter a temperature (Default 0.0): ').strip() or 0.0)

    return SafronOptions(topic=topic,
                         rounds=rounds,
                         filename=filename,
                         model=model,
                         temperature=temperature)


def setup_chats(system1: str, system2: str, topic: str, model: str,
                temperature: float) -> tuple[Chat, Chat]:
    affirmative_chat = Chat(model=model, temperature=temperature)
    affirmative_chat.add_system_msg(system1.format(topic))
    negative_chat = Chat(model=model, temperature=temperature)
    negative_chat.add_system_msg(system2.format(topic))

    return affirmative_chat, negative_chat


def setup_output_file(filename: str | None):
    if filename:
        return open(filename, 'w')
    else:
        return StringIO()


def main() -> int:
    messages = setup_environment()
    if not messages:
        return 1
    topic, rounds, filename, model, temperature = gather_options_from_user()
    affirmative_chat, negative_chat = setup_chats(messages['affirmative'],
                                                  messages['negative'],
                                                  topic,
                                                  model=model,
                                                  temperature=temperature)

    with setup_output_file(filename) as file:
        debate(affirmative_chat, negative_chat, rounds, file)
        summarize_debate(affirmative_chat,
                         messages['summary'],
                         model=model,
                         temperature=temperature,
                         disk_file=file)

    return 0


if __name__ == '__main__':
    sys.exit(main())
