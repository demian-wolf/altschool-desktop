import requests

from pyalt.api.constants.langs import LANGS, UKRAINIAN


class AltSession(requests.Session):
    def __init__(self, lang=UKRAINIAN):
        super().__init__()

        self.lang = lang

    @property
    def lang(self):
        return self.cookies.get("lang")

    @lang.setter
    def lang(self, value):
        if value not in LANGS:
            raise ValueError("invalid language: {}".format(value))

        self.cookies.set("lang", value)
