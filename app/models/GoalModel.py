from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class GoalModel(BaseModel):
    goal_id: str
    user_id: str
    goal_name: str
    goal_description: str
    goal_create_on: datetime
    goal_created_by: str
    goal_updated_on: datetime
    goal_updated_by: str
    goal_assigned_to: List[str]
    goal_priority: int
    goal_due_date: datetime
    goal_comments: List[Dict]
    goal_status: str

    class Config:
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")}
