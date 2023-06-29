from typing import Callable, Protocol, Any
from dotenv import load_dotenv
import os

from machine_learning.common import utilities

import openai

StringDictionary = dict[str, str]
Examples = dict[str, list[StringDictionary]]

# depends on ~/openai.env existing that sets OPENAI_API_KEY variable


def fetch_api_key() -> bool:
    load_dotenv(os.path.expanduser('~/openai.env'))
    openai.api_key = os.getenv('OPENAI_API_KEY')
    return openai.api_key is not None


def load_prompt_injection_instructions() -> str:
    return utilities.load_data_file('openai_api/prompt_injections.txt')


def load_prompt_injection_declination_instructions() -> str:
    return utilities.load_data_file('openai_api/prompt_injection_decline.txt')


def delimit_text(original_text: str, delimitter: str | None) -> str:
    return (delimitter or '') + original_text + (delimitter or '')


def extract_delimitted_text(full_text: str, delimitter: str) -> str:
    stop = full_text.rfind(delimitter)
    if stop == -1:
        return ''
    delim_start = full_text.rfind(delimitter, 0, stop)
    if delim_start == -1:
        delim_start = stop
        stop = None
    start = delim_start + len(delimitter)

    return full_text[start:stop]


def prompt(prompt: str,
           temperature: float = 0.0,
           model: str = 'gpt-3.5-turbo',
           system: str = None,
           input_delim: str | None = None,
           output_delim: str | None = None) -> str:
    messages = []
    if system is not None:
        messages.append({
            'role': 'system',
            'content': system,
        })
    messages.append({
        'role': 'user',
        'content': delimit_text(prompt, input_delim),
    })
    response = openai.ChatCompletion.create(model=model,
                                            messages=messages,
                                            temperature=temperature)
    response_text = response.choices[0].message['content']
    if output_delim:
        response_text = extract_delimitted_text(response_text, output_delim)

    return response_text


class ModerationResponse(Protocol):
    flagged: bool
    categories: dict[str, bool]
    category_scores: dict[str, float]


moderation_flagged = lambda m: m['flagged']
moderation_scores = lambda m: m['category_scores']
moderation_categories = lambda m: m['categories']


def moderation(input: str,
               fn: Callable[[ModerationResponse], Any] = None) -> Any:
    response = openai.Moderation.create(input=input)
    output = response['results'][0]

    if fn is None:
        return output
    else:
        return fn(output)


meta_prompt_y = lambda s: s.strip().lower() == 'y'


def meta_prompt(user_msg: str,
                meta_msg: str,
                system_msg: str,
                examples: Examples,
                input_delim='###',
                output_delim: str = '***',
                fn: Callable[[str], Any] = None) -> Any:
    chat = Chat()
    chat.add_system_msg(meta_msg.format(system=system_msg))
    chat.add_msges(examples['messages'])
    chat.add_user_msg(user_msg=user_msg, input_delim=input_delim)

    result = chat.predict_assistant_msg(output_delim=output_delim)
    #print(chat)
    #print(result)

    if fn:
        return fn(result)
    else:
        return result


class Chat:

    def __init__(self, model: str = 'gpt-3.5-turbo', temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        self.messages = []

    def remove_msg(self) -> None:
        self.messages.pop()

    def add_msg(self,
                role: str,
                msg: str,
                input_delim: str | None = None) -> None:
        self.messages.append({
            'role': role,
            'content': delimit_text(msg, input_delim),
        })

    def add_msges(self, msges: list[dict[str, str]]):
        for msg in msges:
            self.add_msg(role=msg['role'], msg=msg['content'])

    def add_system_msg(self,
                       system_msg: str,
                       input_delim: str | None = None) -> None:
        self.add_msg('system', system_msg, input_delim)

    def add_user_msg(self,
                     user_msg: str,
                     input_delim: str | None = None) -> None:
        self.add_msg('user', user_msg, input_delim)

    def add_assistant_msg(self,
                          agent_msg: str,
                          input_delim: str | None = None) -> None:
        self.add_msg('assistant', agent_msg, input_delim)

    def predict_assistant_msg(self, output_delim: str | None = None) -> str:
        response = openai.ChatCompletion.create(model=self.model,
                                                temperature=self.temperature,
                                                messages=self.messages)
        best_response = response.choices[0]
        next_msg = best_response.message['content']
        self.add_assistant_msg(next_msg)

        if output_delim:
            return extract_delimitted_text(next_msg, output_delim)
        else:
            return next_msg

    def __str__(self):
        formatted_messages = [
            f'{message["role"]}: {message["content"]}'
            for message in self.messages
        ]
        return '\n'.join(formatted_messages)
