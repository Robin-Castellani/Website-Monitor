"""
Script per monitorare siti web periodicamente
Il processo di verifica si basa sul confronto dell'hash da sha256
I siti web vengono letti da file .csv
"""

import csv
import os
import hashlib
import requests
import time
import argparse
import telegram

# TODO: parallelizza con ThreadPoolExecutor
#   guarda https://realpython.com/python-concurrency/#threading-version
# TODO: commenta


def open_website(web_site):
    with requests.Session() as session:
        with session.get(web_site) as response:
            assert type(response.content) == bytes
            return response.content


def get_sha256(byte_string):
    my_hash = hashlib.sha256(byte_string)
    hash_result = my_hash.hexdigest()
    return hash_result


def get_csv_data(csv_file_path):
    with open(csv_file_path, mode='r', encoding='utf=8') as f:
        reader = csv.reader(f)
        websites_and_hashes = {row[0]: row[1] for row in reader}
        return websites_and_hashes


def write_csv_data(csv_file_path, data):
    with open(csv_file_path, mode='w', encoding='utf=8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        for row in data.items():
            assert len(row) == 2
            writer.writerow(row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('token', help='Telegram bot token')
    parser.add_argument('chatid', help='ID of the chat opened with your')
    args = parser.parse_args()
    token = args.token
    chat_id = args.chatid

    bot = telegram.Bot(token=token)

    wait_time = 60 * 60 * 12

    file_path = os.path.join(os.curdir, 'websites.csv')

    while True:
        websites_hashes = get_csv_data(file_path)

        changed_list = list()

        for website, previous_hash in websites_hashes.items():
            print(f'Cheching {website}')
            byte_response = open_website(website)
            new_hash = get_sha256(byte_response)

            if new_hash != previous_hash:
                changed_list.append(f'{website} è cambiato!')
                websites_hashes[website] = new_hash

        if len(changed_list) != 0:
            bot.send_message(chat_id=chat_id, text='\n\n'.join(changed_list))

        write_csv_data(file_path, websites_hashes)

        print('Waiting {wait_time}')
        time.sleep(wait_time)
