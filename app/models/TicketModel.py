from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class TicketModel(BaseModel):
    ticket_id: str
    user_id: str
    ticket_title: str
    ticket_description: str
    ticket_create_on: datetime
    ticket_created_by: str
    ticket_updated_on: datetime
    ticket_updated_by: str
    ticket_assigned_to: List[str]
    ticket_priority: int
    ticket_due_date: datetime
    ticket_comments: List[Dict]
    ticket_status: str
    ticket_tags: List[str]

    class Config:
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")}
