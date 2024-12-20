from pydantic import BaseModel, Field
from datetime import date


class ContactRecordModel(BaseModel):
    account_balance: float = Field(default=0.0)
    account_status: str = Field(default="")
    client_number: int = Field(default=0)
    completed: int = Field(default=0)
    created_date: date = Field(default_factory=date.today)
    created_date_day: int = Field(default=0)
    created_date_month: int = Field(default=0)
    created_date_year: int = Field(default=0)
    done_by: str = Field(default="")
    due_date: date = Field(default_factory=date.today)
    due_date_day: int = Field(default=0)
    due_date_month: int = Field(default=0)
    due_date_year: int = Field(default=0)
    file_number: int = Field(default=0)
    operator: str = Field(default="")
    payment_amount: float = Field(default=0.0)
