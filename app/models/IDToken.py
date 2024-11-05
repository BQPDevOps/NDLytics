from dataclasses import dataclass
import jwt


@dataclass
class IDToken:
    encoded_token: str
    sub: str = None
    cognito_groups: list = None
    email_verified: bool = None
    iss: str = None
    phone_number_verified: bool = None
    cognito_username: str = None
    given_name: str = None
    origin_jti: str = None
    aud: str = None
    event_id: str = None
    token_use: str = None
    auth_time: int = None
    name: str = None
    phone_number: str = None
    exp: str = None
    iat: str = None
    family_name: str = None
    jti: str = None
    email: str = None

    def __post_init__(self):

        if self.encoded_token:
            decoded_token = self.decode_token(self.encoded_token)

            self.sub = decoded_token.get("sub")
            self.cognito_groups = decoded_token.get("cognito:groups")
            self.email_verified = decoded_token.get("email_verified")
            self.iss = decoded_token.get("iss")
            self.phone_number_verified = decoded_token.get("phone_number_verified")
            self.cognito_username = decoded_token.get("cognito:username")
            self.given_name = decoded_token.get("given_name")
            self.origin_jti = decoded_token.get("origin_jti")
            self.aud = decoded_token.get("aud")
            self.event_id = decoded_token.get("event_id")
            self.token_use = decoded_token.get("token_use")
            self.auth_time = decoded_token.get("auth_time")
            self.name = decoded_token.get("name")
            self.phone_number = decoded_token.get("phone_number")
            self.exp = decoded_token.get("exp")
            self.iat = decoded_token.get("iat")
            self.family_name = decoded_token.get("family_name")
            self.jti = decoded_token.get("jti")
            self.email = decoded_token.get("email")

    def decode_token(self, token: str):
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None

    def is_authenticated(self):
        return self.email is not None

    def get_decoded_token(self):
        return self.decode_token(self.encoded_token)

    def get_encoded_token(self):
        return self.encoded_token
