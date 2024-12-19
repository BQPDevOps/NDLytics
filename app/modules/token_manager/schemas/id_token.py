from pydantic import BaseModel, Field
from typing import Optional, List


class IDTokenSchema(BaseModel):
    sub: Optional[str] = None
    cognito_groups: Optional[List[str]] = Field(default=None, alias="cognito:groups")
    email_verified: Optional[bool] = None
    iss: Optional[str] = None
    phone_number_verified: Optional[bool] = None
    cognito_username: Optional[str] = Field(default=None, alias="cognito:username")
    given_name: Optional[str] = None
    origin_jti: Optional[str] = None
    aud: Optional[str] = None
    event_id: Optional[str] = None
    token_use: Optional[str] = None
    auth_time: Optional[int] = None
    name: Optional[str] = None
    phone_number: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    family_name: Optional[str] = None
    jti: Optional[str] = None
    email: Optional[str] = None
