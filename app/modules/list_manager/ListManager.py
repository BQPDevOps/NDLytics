import uuid
from .lists import application_lists


class ListManager:
    def __init__(self):
        self._id = str(uuid.uuid4())
        self._lists = application_lists

    def get_list(self, list_name: str):
        return self._lists.get(list_name, [])
