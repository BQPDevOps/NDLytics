from nicegui import app


class StorageManager:
    def __init__(self):
        self.session_id = app.storage.user.get("session_id")

    def get_from_storage(self, key):
        return app.storage.user.get(key)

    def set_in_storage(self, key, value):
        app.storage.user.set(key, value)

    def delete_from_storage(self, key):
        app.storage.user.delete(key)
