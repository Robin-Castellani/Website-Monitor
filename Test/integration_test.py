"""
Integration test suite.
"""

import unittest
import copy

import responses

from main import *


class TestPerformCheck(unittest.TestCase):
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
