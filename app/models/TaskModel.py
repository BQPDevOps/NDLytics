from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class TaskModel(BaseModel):
    task_id: str
    user_id: str
    task_name: str
    task_description: str
    task_create_on: datetime
    task_created_by: str
    task_updated_on: datetime
    task_updated_by: str
    task_assigned_to: List[str]
    task_priority: int
    task_due_date: datetime
    task_comments: List[Dict]
    task_status: str

    class Config:
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")}
