"""
Script per monitorare siti web periodicamente
Il processo di verifica si basa sul confronto dell'hash da sha256
I siti web vengono letti da file .csv
Via Telegram si riceve la notifica se i siti sono cambiati
"""

import csv
import os
import hashlib
import requests
import time
import argparse
import telegram
from bs4 import BeautifulSoup

# TODO: parallelizza con ThreadPoolExecutor
#   guarda https://realpython.com/python-concurrency/#threading-version
# TODO: aggiungi ultima data di modifica


def open_website(web_site: str) -> bytes:
    """
    Open a website and return the content as bytes
    :param web_site: url as string
    :return: bytes with the HTML content of the webpage
    """
    with requests.Session() as session:
        with session.get(web_site) as response:
            assert type(response.content) == bytes
            return response.content


def filter_element(content: bytes, element: str) -> bytes:
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
    Compute the sha256 hash of a bytes string (the HTML content of the webpage)
    :param byte_string: string of which compute the hash
    :return: a string with the sha256 hash
    """
    my_hash = hashlib.sha256(byte_string)
    hash_result = my_hash.hexdigest()
    return hash_result


def get_csv_data(csv_file_path: str) -> dict:
    """
    Open the .csv file and parse the urls and the hashes
    :param csv_file_path: path to the .csv file
    :return: dictionary {website: hash}
    """
    with open(csv_file_path, mode='r', encoding='utf=8') as f:
        reader = csv.reader(f)
        websites_and_hashes = {
            row[0]: {
                'hash': row[1],
                'element_to_monitor': row[2]
            }
            for row in reader
        }
        return websites_and_hashes


def write_csv_data(csv_file_path: str, data: dict) -> None:
    """
    Write the data to the .csv file
    :param csv_file_path: path of the .csv file
    :param data: dictionary {website: hash}
    :return: None
    """
    with open(csv_file_path, mode='w', encoding='utf=8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        for url, info in data.items():
            to_write = [url] + [*info.values()]
            assert len(to_write) == 3
            writer.writerow(to_write)


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

    # define the frequency of the website monitoring
    wait_time = 60 * 60 * 12

    # define the path of the .csv file
    file_path = os.path.join(os.curdir, 'websites.csv')

    # continue monitoring forever
    while True:
        websites_data = get_csv_data(file_path)

        # list to store changed website to send to the bot
        changed_list = list()

        for website, values in websites_data.items():
            print(f'Checking {website}')

            # get data from the dictionary
            previous_hash = values['hash']
            id_to_monitor = values['element_to_monitor']

            # access to the website and compute the hash
            byte_response = open_website(website)
            element_to_monitor = filter_element(byte_response, id_to_monitor)
            new_hash = get_sha256(element_to_monitor)

            # compare the previous hash with the new one
            if new_hash != previous_hash:
                print(f'{website} è cambiato!')
                changed_list.append(f'{website} è cambiato!')
                websites_data[website]['hash'] = new_hash

        # changed websites? Notify me via Telegram
        if len(changed_list) != 0:
            bot.send_message(chat_id=chat_id, text='\n\n'.join(changed_list))

        # store new data in the .csv file
        write_csv_data(file_path, websites_data)

        print(f'Waiting {wait_time / 3600:.0f} hours')
        time.sleep(wait_time)
