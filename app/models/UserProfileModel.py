from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class UserProfileModel(BaseModel):
    user_id: str
    company_id: str
    role: str
    responsibilities: List[Dict]
    updated_on: datetime
    updated_by: str
    created_on: datetime
    created_by: str
    goals: List[Dict]

    class Config:
        json_encoders = {datetime: lambda dt: int(dt.timestamp())}
