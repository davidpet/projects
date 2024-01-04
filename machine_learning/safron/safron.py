"""SAFRON - Self Argumentation for Refinement of Notions"""

import sys

from termcolor import colored

from machine_learning.common import utilities
from machine_learning.common.openai_api import fetch_api_key, Chat, prompt


def debate(chat1: Chat, chat2: Chat, rounds: int) -> None:
    for _ in range(rounds):
        pos_msg = chat1.predict_assistant_msg()
        chat2.add_user_msg(pos_msg)
        neg_msg = chat2.predict_assistant_msg()
        chat1.add_user_msg(neg_msg)


def print_chat(chat: Chat, colorize=False, file=sys.stdout) -> None:
    print(file=file)

    for message in chat.messages:
        if message['role'] == 'assistant':
            label = 'Affirmative'
            color = 'green'
        elif message['role'] == 'user':
            label = 'Negative'
            color = 'red'
        else:
            continue

        if colorize:
            print(f'{colored(label, color)}:', message['content'], file=file)
        else:
            print(f'[{label}]\n{message["content"]}\n', file=file)
        print(file=file)


def summarize(chat: Chat, system: str, disk_file=None):
    summary = prompt(str(chat), system=system)
    print(f'{colored("Summary", "blue")}:\n{summary}')
    print()

    if disk_file:
        print('\n[Summary]\n', summary, file=disk_file)
        print(file=disk_file)


def main() -> int:
    messages = utilities.load_data_files(
        files={
            'affirmative': 'messages/system_affirmative.txt',
            'negative': 'messages/system_negative.txt',
            'summary': 'messages/system_summary.txt',
        })

    if not fetch_api_key():
        print('ERROR: API key not found!')
        return 1

    topic = input('Please enter debate topic: ').strip()

    affirmative_chat = Chat()
    affirmative_chat.add_system_msg(messages['affirmative'].format(topic))
    negative_chat = Chat()
    negative_chat.add_system_msg(messages['negative'].format(topic))

    rounds = int(input('Enter number of rounds: ').strip())
    filename = input('Enter a filename: ').strip()
    file = None
    if filename:
        file = open(filename, 'w')  # TODO: use 'with' properly here

    # TODO: refactor this to be less taped together
    # TODO: don't pass affirmative system message into the summary phase
    # TODO: give feedback in between rounds (and maybe iterative summaries)
    # TODO: consider open-ended rounds where user decides when to terminate
    # TODO: append and prepend some stuff to filename (eg. ~ and .html)
    # TODO: factor the printing stuff into common area and test it
    # TODO: tests, docstrings, etc. after stable-ish

    debate(affirmative_chat, negative_chat, rounds)
    print_chat(affirmative_chat, colorize=True)
    if file:
        print_chat(affirmative_chat, colorize=False, file=file)
    summarize(affirmative_chat, messages['summary'], disk_file=file)

    if file:
        file.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
