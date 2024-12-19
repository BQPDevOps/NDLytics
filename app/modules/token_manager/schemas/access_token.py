from pydantic import BaseModel, Field
from typing import Optional, List


class AccessTokenSchema(BaseModel):
    encoded_token: str
    sub: Optional[str] = None
    cognito_groups: Optional[List[str]] = Field(default=None, alias="cognito:groups")
    iss: Optional[str] = None
    client_id: Optional[str] = None
    origin_jti: Optional[str] = None
    event_id: Optional[str] = None
    token_use: Optional[str] = None
    scope: Optional[str] = None
    username: Optional[str] = None

    class Config:
        populate_by_name = True
