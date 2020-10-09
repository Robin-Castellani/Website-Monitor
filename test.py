import unittest
from unittest import mock
import io
import sys
import copy

import responses

from main import *


class TestGetSha256(unittest.TestCase):
    def test_get_sha256(self):
        self.assertEqual(
            get_sha256(b'hello world'),
            'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
        )


class TestFilterElement(unittest.TestCase):
    def setUp(self):
        self.fake_html = b'''
            <!DOCTYPE html>
            <html>
            <head>
            </head>
            <body>
        
            <p>This is a paragraph.</p>
            <p id="id01">I am an id paragraph.</p>
            <p class="class01">I am a class paragraph.</p>
        
            </body>
            </html>
        '''

    def test_filter_by_id(self):
        self.assertEqual(
            filter_element(self.fake_html, 'id01'),
            b'<p id="id01">I am an id paragraph.</p>'
        )

    def test_filter_by_class(self):
        self.assertEqual(
            filter_element(self.fake_html, 'class01'),
            b'<p class="class01">I am a class paragraph.</p>'
        )

    def test_filter_no_element(self):
        self.assertEqual(
            filter_element(self.fake_html, ''),
            self.fake_html
        )

    def test_filter_raise_assertion_error(self):
        with self.assertRaises(AssertionError):
            filter_element(self.fake_html, 'non_existing_id_nor_class')


class TestGetCsvData(unittest.TestCase):
    def setUp(self):
        self.fake_websites_data = io.StringIO(
            ",hash,filter,last_change_date\n"
            "https://apple.com,"
            "1ec1ea5fa8cd4e378f03dcce8b61667c19bef3343a4160ab122af04fbc7a9f6f,"
            "page-home ac-nav-overlap,2020-10-01\n"
            "https://www.provincia.brescia.it/istituzionale/concorsi,"
            "714120cf1abda6bac178b4e23c9c2fbacc93b87c5b9b560d90af4e9904dc3be4,"
            "col-sm-9,2020-05-21"
        )
        self.fake_websites_data_comment = io.StringIO(
            ",hash,filter,last_change_date\n"
            "#https://apple.com,"
            "1ec1ea5fa8cd4e378f03dcce8b61667c19bef3343a4160ab122af04fbc7a9f6f,"
            "page-home ac-nav-overlap,2020-10-01\n"
            "https://www.provincia.brescia.it/istituzionale/concorsi,"
            "714120cf1abda6bac178b4e23c9c2fbacc93b87c5b9b560d90af4e9904dc3be4,"
            "col-sm-9,2020-05-21"
        )

    def test_get_csv_data(self):
        self.assertEqual(
            get_csv_data(self.fake_websites_data),
            {
                'https://apple.com': {
                    'hash': '1ec1ea5fa8cd4e378f03dcce8b61667c19bef334'
                            '3a4160ab122af04fbc7a9f6f',
                    'filter': 'page-home ac-nav-overlap',
                    'last_change_date': '2020-10-01',
                },
                'https://www.provincia.brescia.it/istituzionale/concorsi': {
                    'hash': '714120cf1abda6bac178b4e23c9c2fbacc93b87c5'
                            'b9b560d90af4e9904dc3be4',
                    'filter': 'col-sm-9',
                    'last_change_date': '2020-05-21',
                }
            }
        )

    def test_get_csv_data_with_comments(self):
        self.assertEqual(
            get_csv_data(self.fake_websites_data_comment),
            {
                'https://www.provincia.brescia.it/istituzionale/concorsi': {
                    'hash': '714120cf1abda6bac178b4e23c9c2fbacc93b87c5'
                            'b9b560d90af4e9904dc3be4',
                    'filter': 'col-sm-9',
                    'last_change_date': '2020-05-21',
                }
            }
        )


class TestGetOutputChannel(unittest.TestCase):
    def setUp(self):
        self.fake_token = '0123456789:AAHkOz6994U2SilZ3Z4cba6aZaZabcd38Z8'
        self.fake_chat_id = 'chat_id'
        self.args_telegram = argparse.Namespace(
            token=self.fake_token, chat_id=self.fake_chat_id
        )
        self.args_no_telegram = argparse.Namespace(token=None, chat_id=None)

    def test_get_output_channel_no_args(self):
        self.assertIsNone(get_output_channel(self.args_no_telegram))

    @mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_get_output_channel_no_args_print(self, mock_print):
        get_output_channel(self.args_no_telegram)
        self.assertEqual(
            mock_print.getvalue(),
            '⚠ Telegram token and chat-id '
            'not passed through the command line\n'
            '➡ I will print the output to this terminal window\n'
            '------------\n'
        )

    def test_get_output_channel_args(self):
        telegram_tuple = get_output_channel(self.args_telegram)
        self.assertEqual(
            telegram_tuple,
            (telegram.Bot(token=self.fake_token), 'chat_id')
        )


class TestSendOutput(unittest.TestCase):
    @mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_send_output_to_cli_print(self, mock_print):
        send_output(['first', 'second'], None)
        self.assertEqual(
            mock_print.getvalue(),
            '\n------------\n'
            '⏬ Check results ⏬\n'
            'first\n\n'
            'second\n'
        )

    def test_send_output_to_cli_return(self):
        self.assertIsNone(send_output(['first', 'second'], None))

    @mock.patch('telegram.Bot.send_message')
    def test_send_output_to_telegram(self, mock_bot):
        send_output(
            ['first', 'second'],
            (
                telegram.Bot(
                    token='0123456789:AAHkOz6994U2SilZ3Z4cba6aZaZabcd38Z8'
                ),
                'chat_id'
            )
        )
        mock_bot.assert_called_with(
            chat_id='chat_id',
            text='\n\n'.join(['first', 'second'])
        )


class TestOpenWebsite(unittest.TestCase):
    @responses.activate
    def test_open_website(self):
        responses.add(
            responses.GET, 'http://www.test.com',
            body=b'Hello world!', status=200
        )

        response_content = open_website('http://www.test.com')

        self.assertEqual(response_content, b'Hello world!')


class TestPerformCheck(unittest.TestCase):
    # actually this is an Integration test
    def setUp(self):
        # create websites to monitor,
        # the first will change, the second won't
        self.fake_website_data = {
            'http://www.changed.com': {
                'hash': 'fakehash',
                'filter': 'my_id',
                'last_change_date': '2020-01-01',
            },
            'http://www.unchanged.com': {
                'hash': '10501de66339424ad03fe30cdc4d8ea6246f81aa65065493'
                        'fb2692599717aa6f',
                'filter': 'my_class',
                'last_change_date': datetime.date.today().isoformat()
            }
        }

        # set the responses of the fake websites
        responses.add(
            method=responses.GET, url='http://www.changed.com',
            body=b"<!DOCTYPE html><html><body>"
                 b"<p id='my_id'>This is a paragraph.</p>"
                 b"</body></html>",
            status=200
        )
        responses.add(
            method=responses.GET, url='http://www.unchanged.com',
            body=b"<!DOCTYPE html><html><body>"
                 b"<p class='my_class'>hello world</p>"
                 b"</body></html>",
            status=200
        )

    @responses.activate
    def test_output(self):
        changed = perform_check(copy.deepcopy(self.fake_website_data))

        self.assertEqual(changed, ["http://www.changed.com changed!"])

    @responses.activate
    def test_changed_dict(self):
        # deepcopy the fake dict to prevent it from being modified
        copy_fake_website_data = copy.deepcopy(self.fake_website_data)
        perform_check(copy_fake_website_data)

        self.assertEqual(
            copy_fake_website_data['http://www.changed.com'],
            {
                'hash': 'f7605b3e0e68c7823e4de3c2911f3c1a899ca0758d2d2222'
                        'afd193e824ef0133',
                'filter': 'my_id',
                'last_change_date': datetime.date.today().isoformat()
            }
        )


if __name__ == '__main__':
    unittest.main()
