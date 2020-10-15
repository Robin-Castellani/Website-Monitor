"""
Script to monitor website changes comparing the sha256 hash of the
desired portion of the website.

Websites to be monitored are read from a ``.csv`` file.

Any change is sent through Telegram or is printed in the CLI.
"""

import pathlib
import hashlib
import requests
import argparse
import datetime
import typing
import time

import telegram
from bs4 import BeautifulSoup
import pandas as pd

# TODO: parallelize with ThreadPoolExecutor
#   see https://realpython.com/python-concurrency/#threading-version


def get_output_channel(cli_args: argparse.Namespace):
    """
    Use the CLI arguments to select the channel where to redirect the
    output of the website check.

    If Telegram token and the chat-id are passed in,
    send a Telegram message.

    If no argument is passed, print the output to the command line.

    :param cli_args: arguments parsed with argparse.
    :return: ``None`` if no CLI argument is passed is, otherwise
        the instantiated Telegram bot and the chat-id.
    """

    telegram_token = cli_args.token
    telegram_chat_id = cli_args.chat_id

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


def check_file(csv_file_path: pathlib.Path) -> None:
    """
    Perform some checks over the passed file.

    :param csv_file_path: path to the .csv file.
    :return: None
    :raise FileNotFoundError: the file passed in does not exist.
    :raise IsADirectoryError: the path points to a directory, not to a file.
    """

    if not csv_file_path.resolve().exists():
        raise FileNotFoundError(
            f'"{csv_file_path}" does not exist\n'
            f'The full path passed in is "{csv_file_path.resolve()}"'
        )
    if not csv_file_path.resolve().is_file():
        raise IsADirectoryError(
            f'"{csv_file_path}" points to a directory, not to a file\n'
            f'The full path passed in is "{csv_file_path.resolve()}"\n'
            'Pass a formatted properly file (see README for specifications)'
        )


def get_csv_data(csv_file_path: pathlib.Path) -> dict:
    """
    Open the .csv file and parse the urls and information, such as hash,
    last visit date and more.

    Skips rows beginning with the ``#`` character.

    :param csv_file_path: path to the .csv file.
    :return: dictionary ``{website: {info1: value1, ...}}``.
    """
    websites_and_hashes = pd.read_csv(
        csv_file_path,
        index_col=0, comment='#',
    )
    websites_and_hashes = websites_and_hashes.where(
        ~pd.isna(websites_and_hashes), None,
    )
    return websites_and_hashes.to_dict(orient='index')


def get_commented_data(csv_file_path: pathlib.Path) -> dict:
    """
    Read the commented lines in the `csv_file_path` to preserve them
    and to lately write them at the very end of the csv file.

    :param csv_file_path: path to the .csv file.
    :return: dictionary ``{website: {info1: value1, ...}}``.
    """

    with csv_file_path.open('r', encoding='utf-8') as f:
        header = f.readline().rstrip().lstrip(',').split(',')
        comments = [
            line.lstrip('#').rstrip().split(',')
            for line in f
            if line.startswith('#')
        ]

    if not comments:
        return {}
    else:
        comments_dict = {
            f'#{comment[0]}': dict(zip(header, comment[1:]))
            for comment in comments
        }

        return comments_dict


def send_output(
        list_of_changes: typing.List[str],
        telegram_output: typing.Optional[tuple]
) -> None:
    """
    Changed websites? Notify me via Telegram or at the terminal!

    :param list_of_changes: list of strings with the messages to send.
    :param telegram_output: tuple with Telegram token and chat-id or
        ``None`` to print to the terminal.
    :return: ``None``.
    """

    if len(list_of_changes) != 0:
        if telegram_output is not None:
            bot = telegram_output[0]
            chat_id = telegram_output[1]
            bot.send_message(
                chat_id=chat_id,
                text='\n\n'.join(list_of_changes)
            )
        else:
            print('⏬ Check results ⏬')
            print('\n\n'.join(list_of_changes))


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


def perform_check(websites_info: dict, *, verbose: bool) -> typing.List[str]:
    """
    Integrate the functions to check the websites and prepare the
    strings reporting which website has changed.

    :param dict websites_info: dictionary like
        ``{website_url: {hash: ..., changed_date: ...}}``.
    :param bool verbose: whether to print more output to the CLI.
    :return: list of strings of changed websites;
        strings have to be sent to the output channel.
    """

    # print function more verbose
    vprint = lambda *arg, **kwarg: print(*arg, **kwarg) if verbose is True \
        else None

    # list to store changed website to send to the bot
    who_changed_list = list()

    for website, values in websites_info.items():
        vprint(f'Checking {website}')

        # get data from the dictionary
        previous_hash = values['hash']
        id_to_monitor = values['filter']

        # access to the website and compute the hash
        byte_response = open_website(website)
        element_to_monitor = filter_element(byte_response, id_to_monitor)
        new_hash = get_sha256(element_to_monitor)

        # compare the previous hash with the new one
        if new_hash != previous_hash:
            vprint(f'{website} changed!')
            # add the website to the list for the Telegram notification
            who_changed_list.append(f'{website} changed!')
            # update data to be store into the .csv file
            websites_info[website]['hash'] = new_hash
            websites_info[website]['last_change_date'] = \
                datetime.datetime.today().strftime('%Y-%m-%d')

        vprint('...\n------------')

    return who_changed_list


if __name__ == '__main__':

    # parse the CLI arguments
    parser = argparse.ArgumentParser(
        description='Willing to know when a portion of a website has changed? '
                    'This is the right tool! '
                    'Just pass the file with the list of websites '
                    'to be monitored (check out the README before). '
                    'You can be notified via Telegram '
                    'or having a look at the terminal ;)'
    )
    parser.add_argument(
        '-t', '--token',
        required=False, help='Telegram bot token'
    )
    parser.add_argument(
        '-c', '--chat-id', required=False,
        help='ID of the chat opened with your bot'
    )
    parser.add_argument(
        '-r', '--repeat-every',
        required=False, type=int,
        help='Do you want to repeat the monitoring check every X hours? '
             'Insert the hours you want the script to wait between '
             'each monitoring check. Accepts only integers'
    )
    parser.add_argument(
        '-m', '--max-repetition',
        required=False, type=int, default=0,
        help='Maximum number of monitoring checks. Must be set together '
             'with --repeat-every (-r) argument. Accepts only integers'
    )
    parser.add_argument(
        '-v', '--verbose',
        required=False, action='store_true',
        help='Let the output on the CLI be more verbose...'
    )
    parser.add_argument(
        'file',
        type=str,
        help='file holding data about the websites to monitor; '
             'can either be a relative or an absolute path; '
             'see the README to know more about the configuration'
    )

    args = parser.parse_args()
    if args.max_repetition and args.repeat_every is None:
        parser.error('--max-repetition (-m) requires --repeat-every (-r)')
    output_channel = get_output_channel(args)

    # convert the passed file to a Path
    file_path = pathlib.Path(args.file)

    # count the number of checks performed
    n_checks = 0

    while True:
        # check the file at each repetition as it could have been moved
        check_file(file_path)

        # start monitoring
        websites_data = get_csv_data(file_path)
        commented_websites = get_commented_data(file_path)

        changed_list = perform_check(websites_data, verbose=args.verbose)

        # send the output (i.e. the list of changed websites) through the
        # appropriate channel (print to terminal or Telegram chat)
        send_output(changed_list, output_channel)

        # store new data in the .csv file
        # also, append the commented websites (if present)
        #  to the updated ones
        write_csv_data(file_path, {**websites_data, **commented_websites})

        # update the number of checks performed
        n_checks += 1
        # if the maximum number of repetition has already been done, exit
        if n_checks >= args.max_repetition:
            print('*' * 30)
            print(f'{n_checks} checks have been done, '
                  f'maximum number of checks is {args.max_repetition},'
                  f' now exit. Bye bye! 👋')
            break
            
        # wait some hours, if applicable
        if args.repeat_every:

            print('...\n...')
            print('*' * 30)
            print(f'Performed {n_checks} check(s)')
            print(f'Now let me sleep {args.repeat_every} hour(s)...')
            print('*' * 30)
            print('\n\n')
            # wait...
            time.sleep(args.repeat_every)
