from nicegui import app
from modules.token_manager import TokenManager, TokenType
from middleware.dynamo import create_dynamo_middleware
from typing import Optional, Dict, Any
from config import config


class SessionManager:
    def __init__(self):
        self.session_id = app.storage.user.get("session_id")
        self.dynamo = create_dynamo_middleware(config.aws_sessions_table_name)

    def get_from_storage(self, key):
        return app.storage.user.get(key)

    def set_in_storage(self, key, value):
        app.storage.user[key] = value

    def delete_from_storage(self, key):
        if key in app.storage.user:
            del app.storage.user[key]

    def get(self, key):
        return app.storage.user.get(key)

    def set(self, key, value):
        app.storage.user[key] = value

    def delete(self, key):
        if key in app.storage.user:
            del app.storage.user[key]

    def list(self):
        return list(app.storage.user.keys())

    def get_user_groups(self):
        return app.storage.user.get("user_groups", [])

    def get_session_id(self):
        return self.get("session_id")

    def verify_session(self) -> bool:
        """Verify if the current session is valid and not expired"""
        session_id = self.get("session_id")
        id_token = self.get("id_token")

        if not session_id or not id_token:
            return False

        try:
            # Check if token is valid and not expired
            token_manager = TokenManager(TokenType.ID, encoded_token=id_token)
            if not token_manager.is_authenticated or token_manager.is_expired():
                return False

            # Verify session exists in DynamoDB
            session = self.dynamo.get_item({"session_id": {"S": session_id}})
            if not session:
                return False

            return True
        except Exception:
            return False

    def get_user(self) -> Optional[Dict[str, Any]]:
        check_token = app.storage.user.get("id_token")
        if check_token and self.verify_session():
            try:
                return TokenManager(
                    TokenType.ID, encoded_token=check_token
                ).get_decoded_token()
            except Exception:
                return None
        return None
