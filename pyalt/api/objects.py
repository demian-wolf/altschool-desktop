from types import SimpleNamespace
import json


class AltObject(SimpleNamespace):
    @classmethod
    def _object_hook(cls, data):
        return cls(**data)

    @classmethod
    def from_json(cls, json_):
        return json.loads(
            json_,
            object_hook=cls._object_hook,
        )

    @classmethod
    def from_response(cls, response):
        return response.json(
            object_hook=cls._object_hook,
        )
