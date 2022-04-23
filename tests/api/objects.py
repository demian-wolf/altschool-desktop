import unittest

import requests

from pyalt.api.objects import AltObject


class TestAPIObjects(unittest.TestCase):
    def setUp(self):
        url_fmt = "https://online-shkola.com.ua/api/v2/users/1269/thematic/subject/{}"

        self.responses = {
            requests.get(url_fmt.format(n))
            for n in (3, 4, 6)
        }

    def _verify(self, src, dest):
        if isinstance(src, list):
            for src_item, dest_item in zip(src, dest):
                self._verify(src_item, dest_item)
            return

        if isinstance(src, dict):
            for key, src_value in src.items():
                dest_value = getattr(dest, key)
                self._verify(src_value, dest_value)
            return

        self.assertEqual(src, dest)

    def test__from_json(self):
        for response in self.responses:
            self._verify(
                response.json(),
                AltObject.from_json(response.content)
            )

    def test__from_request(self):
        for response in self.responses:
            self._verify(
                response.json(),
                AltObject.from_response(response),
            )
