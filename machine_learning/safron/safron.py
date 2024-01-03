"""SAFRON - Self Argumentation for Refinement of Notions"""

import sys

from machine_learning.common import utilities
from machine_learning.common.openai_api import fetch_api_key

TEMPERATURE = 1.0


def main():
    messages = utilities.load_data_files(
        files={
            'affirmative': 'messages/system_affirmative.txt',
            'negative': 'messages/system_negative.txt',
        })

    if not fetch_api_key():
        print('Uh oh!')
        sys.exit(1)

    print(messages)


if __name__ == '__main__':
    main()
