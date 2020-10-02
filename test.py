import unittest
import io
from main import *

html_id_class = b'''
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

fake_websites_data = io.StringIO("""
,hash,filter,last_change_date
https://apple.com,1ec1ea5fa8cd4e378f03dcce8b61667c19bef3343a4160ab122af04fbc7a9f6f,page-home ac-nav-overlap,2020-10-01
https://www.provincia.brescia.it/istituzionale/concorsi,714120cf1abda6bac178b4e23c9c2fbacc93b87c5b9b560d90af4e9904dc3be4,col-sm-9,2020-05-21
""")


class TestFunctions(unittest.TestCase):
    def test_get_sha256(self):
        self.assertEqual(
            get_sha256(b'hello world'),
            'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
        )

    def test_filter_by_id(self):
        self.assertEqual(
            filter_element(html_id_class, 'id01'),
            b'<p id="id01">I am an id paragraph.</p>'
        )

    def test_filter_by_class(self):
        self.assertEqual(
            filter_element(html_id_class, 'class01'),
            b'<p class="class01">I am a class paragraph.</p>'
        )

    def test_filter_no_element(self):
        self.assertEqual(
            filter_element(html_id_class, ''),
            html_id_class
        )

    def test_filter_raise_assertion_error(self):
        with self.assertRaises(AssertionError):
            filter_element(html_id_class, 'non_existing_id_nor_class')

    def test_get_csv_data(self):
        self.assertEqual(
            get_csv_data(fake_websites_data),
            {
                'https://apple.com': {
                    'hash': '1ec1ea5fa8cd4e378f03dcce8b61667c19bef3343a4160ab122af04fbc7a9f6f',
                    'filter': 'page-home ac-nav-overlap',
                    'last_change_date': '2020-10-01',
                },
                'https://www.provincia.brescia.it/istituzionale/concorsi': {
                    'hash': '714120cf1abda6bac178b4e23c9c2fbacc93b87c5b9b560d90af4e9904dc3be4',
                    'filter': 'col-sm-9',
                    'last_change_date': '2020-05-21',
                }
            }
        )


if __name__ == '__main__':
    unittest.main()
