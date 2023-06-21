"""General checks to be used in jupyter notebooks."""

from termcolor import colored


def check_condition(condition: bool, prefix: str, print_fn=None) -> None:
    """
    Test whether a condition is true or false and print a formatted result.

    Args:
        condition (bool): The condition to check.
        prefix (str): A prefix string (eg. test name).
        print_fn (function): Optional override for testing.

    Returns:
        None
    """

    if print_fn is None:
        print_fn = print

    if condition:
        result = colored("Pass", "green")
    else:
        result = colored("Fail", "red")
    print_fn(f'{colored(prefix, "blue", attrs=["dark"])}: {result}')
