"""
Script to monitor website changes comparing the sha256 hash of the
desired portion of the website.

Websites to be monitored are read from a ``.csv`` file.

Any change is sent through Telegram.
"""

import csv
import os
import hashlib
import requests
import argparse
import datetime

import telegram
from bs4 import BeautifulSoup
import pandas as pd

# TODO: parallelize with ThreadPoolExecutor
#   see https://realpython.com/python-concurrency/#threading-version


def open_website(web_site: str) -> bytes:
    """
    Open a website and return the content as bytes.

    :param web_site: url as string.
    :return: bytes with the HTML content of the webpage.
    """
    with requests.Session() as session:
        with session.get(web_site) as response:
            assert type(response.content) == bytes
            return response.content


def filter_element(content: bytes, element: str) -> bytes:
    """
    Get the desired element (an ``id`` or a ``class`` in the html)
    or the whole webpage if no element has been selected.

    :param content: raw html.
    :param element: name of the ``id`` or the ``class`` in the raw html.
    :return: the raw html associated with ``element``.
    :raise AssertionError:
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
    Compute the sha256 hash of a bytes string (the HTML content of the webpage).

    :param byte_string: string of which compute the hash.
    :return: a string with the sha256 hash.
    """
    my_hash = hashlib.sha256(byte_string)
    hash_result = my_hash.hexdigest()
    return hash_result


def get_csv_data(csv_file_path: str) -> dict:
    """
    Open the .csv file and parse the urls and information, such as hash,
    last visit date and more.

    :param csv_file_path: path to the .csv file.
    :return: dictionary ``{website: {info1: value1, ...}}``.
    """
    with open(csv_file_path, mode='r', encoding='utf=8') as f:
        reader = csv.reader(f)
        # get the first line of the .csv file holding the column names
        header = next(reader)
        # populate the dictionary {website: {info1: value1, ...}, ...}
        websites_and_hashes = {
            row[0]: {
                key: value
                for key, value in zip(header[1:], row[1:])
            }
            for row in reader
        }
        return websites_and_hashes


def write_csv_data(csv_file_path: str, data: dict) -> None:
    """
    Write the data to the ``.csv`` file.

    :param csv_file_path: path of the .csv file.
    :param data: dictionary ``{website: {info1: value1, ...}}``.
    :return: None.
    """
    # convert the dictionary to a DataFrame to write it easier as a .csv file
    # transpose the DataFrame to have websites as index
    df = pd.DataFrame(data).T
    df.to_csv(csv_file_path, mode='w', encoding='utf=8')


if __name__ == '__main__':
    # first parse the Telegram bot token and the chat id
    parser = argparse.ArgumentParser()
    parser.add_argument('token', help='Telegram bot token')
    parser.add_argument('chatid', help='ID of the chat opened with your')
    args = parser.parse_args()
    token = args.token
    chat_id = args.chatid

    # instantiate the bot
    bot = telegram.Bot(token=token)

    # define the path of the .csv file
    file_path = os.path.join(os.curdir, 'websites.csv')

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
            print(f'{website} è cambiato!')
            # add the website to the list for the Telegram notification
            changed_list.append(f'{website} è cambiato!')
            # update data to be store into the .csv file
            websites_data[website]['hash'] = new_hash
            websites_data[website]['last_change_date'] = \
                datetime.datetime.today().strftime('%Y-%m-%d')

    # changed websites? Notify me via Telegram
    if len(changed_list) != 0:
        bot.send_message(chat_id=chat_id, text='\n\n'.join(changed_list))

    # store new data in the .csv file
    write_csv_data(file_path, websites_data)
