"""
Script to monitor website changes comparing the sha256 hash of the
desired portion of the website.

Websites to be monitored are read from a ``.csv`` file.

Any change is sent through Telegram.
"""

import pathlib
import hashlib
import requests
import argparse
import datetime
import typing

import telegram
from bs4 import BeautifulSoup
import pandas as pd

# TODO: parallelize with ThreadPoolExecutor
#   see https://realpython.com/python-concurrency/#threading-version


def get_output_channel():
    """
    Parse the optional CLI arguments, which consist of the Telegram
    token and the chat-id.

    If no argument is passed, print the output to the command line.

    :return: ``None`` if no CLI argument is passed is, otherwise
        the instantiated Telegram bot and the chat-id.
    """

    # first parse the Telegram bot token and the chat id
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--token',
        required=False, help='Telegram bot token'
    )
    parser.add_argument(
        '-c', '--chat-id', required=False,
        help='ID of the chat opened with your bot'
    )
    args = parser.parse_args()

    telegram_token = args.token
    telegram_chat_id = args.chat_id

    if telegram_token is None or telegram_chat_id is None:
        print(
            '⚠ Telegram token and chat-id not passed through the command line',
            '➡ I will print the output to this terminal window',
            sep='\n', end='\n------------\n'
        )
        return

    # instantiate the bot
    telegram_bot = telegram.Bot(token=telegram_token)

    return telegram_bot, telegram_chat_id


def open_website(web_site: str) -> bytes:
    """
    Open a website and return the content as bytes.

    :param web_site: url as string.
    :return: bytes with the HTML content of the web-page.
    :raise AssertionError: type of the response content is not bytes.
    """
    with requests.Session() as session:
        with session.get(web_site) as response:
            assert type(response.content) == bytes
            return response.content


def filter_element(content: bytes, element: str) -> bytes:
    """
    Get the desired element (an ``id`` or a ``class`` in the html)
    or the whole web-page if no element has been selected.

    :param content: raw html.
    :param element: name of the ``id`` or the ``class`` in the raw html.
    :return: the raw html associated with ``element``.
    :raise AssertionError: the ``element`` is not present
        in the ``content``.
    """
    if not element:
        return content
    soup = BeautifulSoup(content, features="html.parser")
    to_monitor = soup.find(id=element)
    if to_monitor is None:
        to_monitor = soup.find(class_=element)
    assert to_monitor is not None
    return bytes(str(to_monitor), encoding='utf-8')


def get_sha256(byte_string: bytes) -> str:
    """
    Compute the sha256 hash of a bytes string
    (which is meant to be the HTML content of the web-page).

    :param byte_string: string of which compute the hash.
    :return: a string with the sha256 hash.
    """
    my_hash = hashlib.sha256(byte_string)
    hash_result = my_hash.hexdigest()
    return hash_result


def get_csv_data(csv_file_path: typing.Union[str, pathlib.Path]) -> dict:
    """
    Open the .csv file and parse the urls and information, such as hash,
    last visit date and more.

    :param csv_file_path: path to the .csv file.
    :return: dictionary ``{website: {info1: value1, ...}}``.
    """
    websites_and_hashes = pd.read_csv(
        csv_file_path,
        index_col=0,
    )
    websites_and_hashes.where(
        ~pd.isna(websites_and_hashes), None,
        inplace=True
    )
    return websites_and_hashes.to_dict(orient='index')


def write_csv_data(csv_file_path: str, data: dict) -> None:
    """
    Write the data to the ``.csv`` file.

    :param csv_file_path: path of the .csv file.
    :param data: dictionary ``{website: {info1: value1, ...}}``.
    :return: None.
    """
    # convert the dictionary to a DataFrame to write it
    # in an easier way as a .csv file
    # transpose the DataFrame to have websites as index
    df = pd.DataFrame(data).T
    df.to_csv(csv_file_path, mode='w', encoding='utf=8')


if __name__ == '__main__':

    # get the channel (Telegram or terminal) where to send the output
    output_channel = get_output_channel()

    # define the path of the .csv file relatively to this script's folder
    file_path = pathlib.Path(__file__).with_name('websites.csv')

    # start monitoring
    websites_data = get_csv_data(file_path)

    # list to store changed website to send to the bot
    changed_list = list()

    for website, values in websites_data.items():
        print(f'Checking {website}')

        # get data from the dictionary
        previous_hash = values['hash']
        id_to_monitor = values['filter']

        # access to the website and compute the hash
        byte_response = open_website(website)
        element_to_monitor = filter_element(byte_response, id_to_monitor)
        new_hash = get_sha256(element_to_monitor)

        # compare the previous hash with the new one
        if new_hash != previous_hash:
            print(f'{website} changed!')
            # add the website to the list for the Telegram notification
            changed_list.append(f'{website} changed!')
            # update data to be store into the .csv file
            websites_data[website]['hash'] = new_hash
            websites_data[website]['last_change_date'] = \
                datetime.datetime.today().strftime('%Y-%m-%d')

    # changed websites? Notify me via Telegram or at the terminal
    if len(changed_list) != 0:
        if output_channel is not None:
            output_channel[0].send_message(
                chat_id=output_channel[1],
                text='\n\n'.join(changed_list)
            )
        else:
            print('\n------------')
            print('⏬ Check results ⏬')
            print('\n\n'.join(changed_list))

        # store new data in the .csv file
        write_csv_data(file_path, websites_data)
