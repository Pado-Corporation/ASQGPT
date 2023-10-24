import os

import requests

supabase_key = os.getenv("ASQ_DB_KEY")


def read_file(filename):
    """
    Reads the file corresponding to the given `filename` in the `prompts` directory.
    :param filename: The name of the file containing the prompt
    :type filename: str
    :return: The prompt
    """
    with open(f"./prompts/{filename}", 'r') as file:
        return file.read()


def check_completion(tag, message):
    """
    Check if the agent has completed its role, by searching for a "tag".
    :param tag: Indicator that the task has been completed
    :type tag: str
    :param message: Content that needs to be checked
    :type message: str
    :return:
    """
    return tag in message

def get_report(id):
    url = 'https://crhertcomzmmxpsmqozi.supabase.co/rest/v1/reports?id=eq.1&select=*'
    payload = {'id': id, 'select': 'report_type'}
    headers = {'apikey': supabase_key, 'Authorization': f'Bearer {supabase_key}', 'Range': '0-9'}
    response = requests.get(url, params=payload, headers=headers)