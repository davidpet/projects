"""Functionality for using the OpenAI API."""

from typing import Callable, Protocol, Any
import os

from dotenv import load_dotenv
import openai

from machine_learning.common import utilities

StringDictionary = dict[str, str]

# Few-shot learning examples for the LLM.
Examples = dict[str, list[StringDictionary]]


def fetch_api_key() -> bool:
    """
    Internally load the OpenAI Api key so that future operations will work.

    Depends on ~/openai.env existing and settings OPENAI_API_KEY.

    Returns:
        bool: true if succeeds.
    """

    load_dotenv(os.path.expanduser('~/openai.env'))
    openai.api_key = os.getenv('OPENAI_API_KEY')
    return openai.api_key is not None


def load_prompt_injection_instructions() -> str:
    """
    Load the generic prompt injection detection instructions for LLMs.

    These are instructions to the LLM asking it to decide if a prompt is
    a prompt injection or not.

    Returns:
        str: the text of the instructions
    """

    return utilities.load_data_file('openai_api/prompt_injections.txt')


def load_prompt_injection_declination_instructions() -> str:
    """
    Load the generic prompt injection decline instructions for LLMs.

    These are instructions to the LLM telling it that we already know the
    prompt is an injection, so politely decline to honor it.

    Returns:
        str: the text of the instructions
    """

    return utilities.load_data_file('openai_api/prompt_injection_decline.txt')


def delimit_text(original_text: str, delimitter: str | None) -> str:
    """
    Place an optional delimiter before and after given string.

    Args:
        original_text (str): the text to decorate
        delimitter (str | None): optional text to use as delim

    Returns:
        str: delimitted (or original if None delimitter) text
    """

    return (delimitter or '') + original_text + (delimitter or '')


def extract_delimitted_text(full_text: str, delimitter: str) -> str:
    """
    Find the last occurence of a string surrounded by given delimitter.

    Args:
        full_text (str): the text to search in
        delimitter (str): the delimitter surrounding text to find

    Returns:
        str: the text within the delimitters (last occurence) or
             '' if not found. If only 1 delim present, then the
             trailing portion of the text will be returned.
    """

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
           system: str | None = None,
           input_delim: str | None = None,
           output_delim: str | None = None) -> str:
    """
    Issue a prompt to the OpenAI ChatCompletion endpoint.

    Args:
        prompt (str): the text prompt to send
        temperature (float, optional): randomness/creativity of the response.
                                       Defaults to 0.0 for predictability.
        model (str, optional): the LLM to use. Defaults to 'gpt-3.5-turbo'.
        system (str, optional): system role message. Defaults to None.
        input_delim (str | None, optional): Delimiter to put around prompt.
                                            Defaults to None.
        output_delim (str | None, optional): Delimiter to extract from in
                                             response. Defaults to None.

    TODO: possibly deal with multiple choices in response.

    Returns:
        str: either the full response from the LLM or the text surrounded by
        delims (or marked with 1 delim).
    """

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
    """
    Response from OpenAI Moderation API.

    This is actually not used directly but is for the purpose of
    type annotations.

    Attributes:
        flagged (bool): whether the Moderation API flagged the text
        categories (dict[str, bool]): individual flagged state of each category
        category_scores (dict[str, float]): individual offensiveness scores
    """

    flagged: bool
    categories: dict[str, bool]
    category_scores: dict[str, float]


# fn to extract the 'flagged' field from a moderation response from the server.
# TODO: find out why I treated it as a dictionary instead of an object
#       (I don't remember and it looks weird).
moderation_flagged = lambda m: m['flagged']
# fn to extract the 'category_scores' field from a moderation response from
# the server.
moderation_scores = lambda m: m['category_scores']
# fn to extract the 'categories' field from a moderation response from the
# server.
moderation_categories = lambda m: m['categories']


def moderation(input: str,
               fn: Callable[[ModerationResponse], Any] = None) -> Any:
    """
    Call OpenAI Moderation API with input text and optionally extract a portion
    of the output using a given fn.

    Extraction fn would typically be one of the global variables from this
    module such as `moderation_flagged`, etc.

    Args:
        input (str): the text to send to the Moderation API
        fn (Callable[[ModerationResponse], Any], optional): extraction fn.
                                                            Defaults to None.

    Returns:
        Any: the response passed through fn (or unaltered if fn is None).
              By default, assume a `ModerationResponse` object.
    """

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
    """
    Prompt the ChatCompletion endpoint with both a system and user msg as
    well as few-short learning examples.

    Args:
        user_msg (str): the message from the user
        meta_msg (str): a message describing the system message (higher-level)
        system_msg (str): the system message used for the user chat
        examples (Examples): few-shot learning examples. Expected to have a
                             'messages' field with child objects having
                             'role' and 'content' fields representing chat
                             messages demonstrating user input and api
                             output.  In other words, 'user' and 'assistant'
                             roles in alternation.
        input_delim (str, optional): delimiter to put around user message.
                                     Defaults to '###'.
        output_delim (str, optional): delimiter to use for extracting response.
                                      Defaults to '***'.
        fn (Callable[[str], Any], optional): processing fn for result.
                                             Defaults to None.

    Returns:
        Any: Response message from chat endpoint, or result of applying fn()
             on the response if an fn is given.
    """

    chat = Chat()
    chat.add_system_msg(meta_msg.format(system=system_msg))
    chat.add_msges(examples['messages'])
    chat.add_user_msg(user_msg=user_msg, input_delim=input_delim)

    result = chat.predict_assistant_msg(output_delim=output_delim)

    if fn:
        return fn(result)
    else:
        return result


class Chat:
    """
    An ongoing LLM chat with memory.

    Attributes:
        model(str): LLM model to use.  Defaults to 'got-3.5-turbo'.
        temperature(float): randomness in responses.  Defaults to 0.0.
        messages(list[str]): the messages so far (all roles).

    """

    model: str
    temperature: float
    messages: list[str]

    def __init__(self, model: str = 'gpt-3.5-turbo', temperature: float = 0.0):
        """
        Create a new chat instance.

        Args:
            model (str, optional): LLM model to use. Defaults to gpt-3.5-turbo.
            temperature (float, optional): randomness. Defaults to 0.0.
        """

        self.model = model
        self.temperature = temperature
        self.messages = []

    def remove_msg(self) -> None:
        """
        Remove the last message from the history.

        Only the local chat history is affected (no server call made).
        """

        self.messages.pop()

    def add_msg(self,
                role: str,
                msg: str,
                input_delim: str | None = None) -> None:
        """
        Add a message to the end of the chat history.

        Only the local chat history is affected (no server call made).

        Args:
            role (str): the role for the message (eg. 'user')
            msg (str): the message content
            input_delim (str | None, optional): Optional delim to put around
                                                message. Defaults to None.
        """

        self.messages.append({
            'role': role,
            'content': delimit_text(msg, input_delim),
        })

    def add_msges(self, msges: list[dict[str, str]]):
        """
        Add a list of messages to the chat history.

        Only the local chat history is affected (no server call made).

        Args:
            msges (list[dict[str, str]]): list of messages in order.
                                          each should have 'role' and
                                          'content'.
        """

        for msg in msges:
            self.add_msg(role=msg['role'], msg=msg['content'])

    def add_system_msg(self,
                       system_msg: str,
                       input_delim: str | None = None) -> None:
        """
        Add a system message to the chat history.

        Only the local chat history is affected (no server call made).

        Args:
            system_msg (str): the system message
            input_delim (str | None, optional): delimitter to wrap it in.
                                                Defaults to None.
        """

        self.add_msg('system', system_msg, input_delim)

    def add_user_msg(self,
                     user_msg: str,
                     input_delim: str | None = None) -> None:
        """
        Add a user message to the chat history.

        Only the local chat history is affected (no server call made).

        Args:
            user_msg (str): the user message
            input_delim (str | None, optional): delimitter to wrap it in.
                                                Defaults to None.
        """

        self.add_msg('user', user_msg, input_delim)

    def add_assistant_msg(self,
                          agent_msg: str,
                          input_delim: str | None = None) -> None:
        """
        Add an assistant (AI) message to the chat history.

        Only the local chat history is affected (no server call made).

        Args:
            system_msg (str): the agent message
            input_delim (str | None, optional): delimitter to wrap it in.
                                                Defaults to None.
        """

        self.add_msg('assistant', agent_msg, input_delim)

    def predict_assistant_msg(self, output_delim: str | None = None) -> str:
        """
        Get an assistant message from the OpenAI ChatCompletion endpoint
        via server call based on the whole chat history so far.

        The new message is both added to the end of the local chat history as
        well as directly returned from the function for convenience.

        TODO: consider looking at choices other than [0].

        Args:
            output_delim (str | None, optional): Wrapping delims to extract
                                                 from. Defaults to None.

        Returns:
            str: the assistant message from the server
        """

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

    def __str__(self) -> str:
        """
        Get string representation of the chat history so far.

        Returns:
            str: the string reprsesentation showing roles and messages.
        """

        formatted_messages = [
            f'{message["role"]}: {message["content"]}'
            for message in self.messages
        ]
        return '\n'.join(formatted_messages)
