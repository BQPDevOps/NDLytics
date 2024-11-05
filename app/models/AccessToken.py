import jwt


class AccessToken:
    def __init__(self, encoded_token: str):
        self.encoded_token = encoded_token
        self.sub = None
        self.cognito_groups = None
        self.iss = None
        self.client_id = None
        self.origin_jti = None
        self.event_id = None
        self.token_use = None
        self.scope = None
        self.username = None
        self._onload()

    def _onload(self):

        if self.encoded_token:
            decoded_token = self._decode_token(self.encoded_token)

            self.sub = decoded_token.get("sub")
            self.cognito_groups = decoded_token.get("cognito:groups")
            self.iss = decoded_token.get("iss")
            self.client_id = decoded_token.get("client_id")
            self.origin_jti = decoded_token.get("origin_jti")
            self.event_id = decoded_token.get("event_id")
            self.token_use = decoded_token.get("token_use")
            self.scope = decoded_token.get("scope")
            self.username = decoded_token.get("username")

    def _decode_token(self, token: str):
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None

    def is_authenticated(self):
        return self.username is not None

    def get_decoded_token(self):
        return self._decode_token(self.encoded_token)

    def get_encoded_token(self):
        return self.encoded_token
