import unittest

from pyalt.api.sessions import AltSession
from pyalt.api.constants.langs import LANGS


class TestAPISessions(unittest.TestCase):
    def test__lang(self):
        for lang in ("invalid", "foo", "bar"):
            self.assertRaises(
                ValueError,
                lambda: AltSession(lang=lang),
            )

        session = AltSession()

        self.assertIsNotNone(session.lang)
        self.assertIn(session.lang, LANGS)

        for lang in LANGS:
            session.lang = lang
            self.assertEqual(session.lang, lang)
