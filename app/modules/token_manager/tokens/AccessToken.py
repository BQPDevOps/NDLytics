import jwt
from typing import Optional, Dict, Any
from ..schemas import AccessTokenSchema


class AccessToken:
    def __init__(self, encoded_token: str):
        self.token_data = self._initialize_token(encoded_token)

    def _initialize_token(self, encoded_token: str) -> AccessTokenSchema:
        decoded_token = self._decode_token(encoded_token)
        return (
            AccessTokenSchema(encoded_token=encoded_token, **decoded_token)
            if decoded_token
            else None
        )

    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None

    @property
    def is_authenticated(self) -> bool:
        return self.token_data and self.token_data.username is not None

    @property
    def encoded_token(self) -> str:
        return self.token_data.encoded_token if self.token_data else None

    @property
    def decoded_token(self) -> Dict[str, Any]:
        return self.token_data.model_dump() if self.token_data else None

    def has_group(self, group_name: str) -> bool:
        return (
            self.token_data
            and self.token_data.cognito_groups
            and group_name in self.token_data.cognito_groups
        )

    def has_scope(self, scope: str) -> bool:
        return (
            self.token_data
            and self.token_data.scope
            and scope in self.token_data.scope.split()
        )

    def get_user_id(self) -> Optional[str]:
        return self.token_data.sub if self.token_data else None

    def __bool__(self) -> bool:
        return self.is_authenticated
