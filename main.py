"""
Script per monitorare siti web periodicamente
Il processo di verifica si basa sul confronto dell'hash da sha256
I siti web vengono letti da file .csv
"""

import csv
import os
import hashlib
import requests

# TODO: parallelizza con ThreadPoolExecutor
#   guarda https://realpython.com/python-concurrency/#threading-version
# TODO: invia i siti cambiati via Telegram ad un bot
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
    file_path = os.path.join(os.curdir, 'websites.csv')

    websites_hashes = get_csv_data(file_path)

    for website, previous_hash in websites_hashes.items():
        byte_response = open_website(website)
        new_hash = get_sha256(byte_response)

        if new_hash != previous_hash:
            print(f'{website} è cambiato!')
            websites_hashes[website] = new_hash

    write_csv_data(file_path, websites_hashes)
