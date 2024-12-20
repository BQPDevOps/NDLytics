from pydantic import BaseModel, Field
from datetime import date


class TransactionRecordModel(BaseModel):
    client_number: int = Field(default=0)
    contingency_amount: float = Field(default=0.0)
    description: str = Field(default="")
    file_number: int = Field(default=0)
    operator: str = Field(default="")
    payment_amount: float = Field(default=0.0)
    payment_date: date = Field(default_factory=date.today)
    payment_date_day: int = Field(default=0)
    payment_date_month: int = Field(default=0)
    payment_date_year: int = Field(default=0)
    posted_by: str = Field(default="")
    posted_date: date = Field(default_factory=date.today)
    posted_date_day: int = Field(default=0)
    posted_date_month: int = Field(default=0)
    posted_date_year: int = Field(default=0)
    transaction_type: str = Field(default="")
