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


def print_chat(chat: Chat, colorize=False) -> None:
    print()

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
            print(f'{colored(label, color)}:', message['content'])
        else:
            print(f'{label}: {message["content"]}')
        print()


def summarize(chat: Chat, system: str):
    summary = prompt(str(chat), system=system)
    print(f'{colored("Summary", "blue")}:\n{summary}')


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

    rounds = int(input("Enter number of rounds: ").strip())

    debate(affirmative_chat, negative_chat, rounds)
    print_chat(affirmative_chat, colorize=True)
    summarize(affirmative_chat, messages['summary'])

    return 0


if __name__ == '__main__':
    sys.exit(main())
