import sys
from metagpt.const import PROJECT_ROOT


def read_file(filename):
    """
    Reads the file corresponding to the given `filename` in the `prompts` directory.
    :param filename: The name of the file containing the prompt
    :type filename: str
    :return: The prompt
    """
    with open(f"{PROJECT_ROOT}/metagpt/boss_agent/prompts/{filename}", "r") as file:
        return file.read()


def check_completion(tag, message):
    """
    Check if the agent has completed its role, by searching for a "tag". If true, finish the process.
    :param tag: Indicator that the task has been completed
    :type tag: str
    :param message: Content that needs to be checked
    :type message: str
    :return:
    """
    return tag in message
