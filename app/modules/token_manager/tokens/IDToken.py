import jwt
from datetime import datetime
from typing import Optional
from ..schemas import IDTokenSchema


class IDToken:
    def __init__(self, encoded_token: str):
        self.encoded_token = encoded_token
        self._decoded_token: Optional[IDTokenSchema] = None
        self._decode_token()

    def _decode_token(self) -> None:
        try:
            decoded = jwt.decode(
                self.encoded_token, options={"verify_signature": False}
            )
            self._decoded_token = IDTokenSchema(**decoded)
        except Exception as e:
            print(f"Error decoding token: {e}")
            self._decoded_token = None

    @property
    def decoded_token(self) -> Optional[IDTokenSchema]:
        return self._decoded_token

    def is_authenticated(self) -> bool:
        return self._decoded_token is not None and self._decoded_token.email is not None

    def is_expired(self) -> bool:
        if not self._decoded_token or not self._decoded_token.exp:
            return True
        return datetime.utcnow().timestamp() > self._decoded_token.exp

    def get_user_roles(self) -> list:
        return self._decoded_token.cognito_groups if self._decoded_token else []

    def has_role(self, role: str) -> bool:
        return role in self.get_user_roles()

    def get_user_email(self) -> Optional[str]:
        return self._decoded_token.email if self._decoded_token else None

    def get_user_name(self) -> Optional[str]:
        if not self._decoded_token:
            return None
        return (
            self._decoded_token.name
            or f"{self._decoded_token.given_name} {self._decoded_token.family_name}".strip()
        )

    def get_user_id(self) -> Optional[str]:
        return self._decoded_token.sub if self._decoded_token else None

    def get_encoded_token(self) -> str:
        return self.encoded_token
