from pydantic import BaseModel, Field
from datetime import date, datetime


class OutboundRecordModel(BaseModel):
    broadcast_id: str = Field(default="")
    agent_id: str = Field(default="")
    caller_id: str = Field(default="")
    call_id: str = Field(default="")
    call_recorded: bool = Field(default=False)
    short_code: str = Field(default="")
    call_type: str = Field(default="")
    delivery_cost: float = Field(default=0.0)
    delivery_length: int = Field(default=0)
    file_number: int = Field(default=0)
    client_number: int = Field(default=0)
    score: int = Field(default=0)
    status: str = Field(default="")
    zip_code: str = Field(default="")
    balance: float = Field(default=0.0)
    phone_cell: str = Field(default="")
    phone_home: str = Field(default="")
    phone_work: str = Field(default="")
    phone_other: str = Field(default="")
    tcn_dialed: str = Field(default="")
    start_time: datetime = Field(default_factory=datetime.now)
    interaction: str = Field(default="")
    result: str = Field(default="")
    call_completed_date_day: int = Field(default=0)
    call_completed_date_month: int = Field(default=0)
    call_completed_date_year: int = Field(default=0)
    call_completed_date_hour: int = Field(default=0)
    call_completed_date_minute: int = Field(default=0)
    charge_date_month: int = Field(default=0)
    charge_date_day: int = Field(default=0)
    charge_date_year: int = Field(default=0)
