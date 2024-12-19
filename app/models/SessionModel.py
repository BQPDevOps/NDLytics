from pydantic import BaseModel


class SessionModel(BaseModel):
    user_id: str
    session_id: str
    expiration_time: int
    created_at: int
    last_accessed: int
    is_active: bool = True
