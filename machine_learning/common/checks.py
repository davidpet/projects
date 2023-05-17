from termcolor import colored


def check_condition(condition: bool, prefix: str) -> None:
    """Test whether a condition is true or false and print a formatted result.

    Args:
        condition (bool): The condition to check.
        prefix (str): A prefix string (eg. test name).

    Returns:
        None
    """

    if condition:
        result = colored("Pass", "green")
    else:
        result = colored("Fail", "red")
    print(f'{colored(prefix, "blue", attrs=["dark"])}: {result}')
