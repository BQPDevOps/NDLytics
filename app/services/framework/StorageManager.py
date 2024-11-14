from nicegui import app
from models import IDToken


class StorageManager:
    def __init__(self):
        self.session_id = app.storage.user.get("session_id")

    def get_from_storage(self, key):
        return app.storage.user.get(key)

    def set_in_storage(self, key, value):
        app.storage.user.set(key, value)

    def delete_from_storage(self, key):
        app.storage.user.delete(key)

    def list_storage_keys(self):
        return list(app.storage.user.keys())

    def get_user_id(self):
        user_token = IDToken(app.storage.user.get("id_token"))
        return user_token.sub
