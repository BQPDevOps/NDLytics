from enum import Enum
from typing import Union
from .tokens import IDToken, AccessToken


class TokenType(Enum):
    ID = "id"
    ACCESS = "access"


class TokenManager:
    def __init__(self, token_type: TokenType, encoded_token: str):
        self.token_type = token_type
        self._token = self._initialize_token(encoded_token)

    def _initialize_token(self, encoded_token: str) -> Union[IDToken, AccessToken]:
        if self.token_type == TokenType.ID:
            return IDToken(encoded_token)
        return AccessToken(encoded_token)

    @property
    def is_authenticated(self) -> bool:
        return (
            self._token.is_authenticated()
            if isinstance(self._token, IDToken)
            else self._token.is_authenticated
        )

    def is_expired(self) -> bool:
        if isinstance(self._token, IDToken):
            return self._token.is_expired()
        return False  # AccessToken doesn't implement is_expired

    def has_role(self, role: str) -> bool:
        if isinstance(self._token, IDToken):
            return self._token.has_role(role)
        return self._token.has_group(role)

    def get_encoded_token(self) -> str:
        return (
            self._token.get_encoded_token()
            if isinstance(self._token, IDToken)
            else self._token.encoded_token
        )

    def get_decoded_token(self):
        return self._token.decoded_token

    def get_user_info(self) -> dict:
        if isinstance(self._token, IDToken):
            return {
                "email": self._token.get_user_email(),
                "name": self._token.get_user_name(),
                "roles": self._token.get_user_roles(),
            }
        return {
            "username": (
                self._token.token_data.username if self._token.token_data else None
            ),
            "groups": (
                self._token.token_data.cognito_groups
                if self._token.token_data
                else None
            ),
            "scopes": (
                self._token.token_data.scope.split()
                if self._token.token_data and self._token.token_data.scope
                else None
            ),
        }

    def has_scope(self, scope: str) -> bool:
        if isinstance(self._token, AccessToken):
            return self._token.has_scope(scope)
        return False  # IDToken doesn't implement has_scope
