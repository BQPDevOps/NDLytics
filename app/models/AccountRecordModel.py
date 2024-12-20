from pydantic import BaseModel, Field
from datetime import date


class AccountRecordModel(BaseModel):
    account_status: int = Field(default=0)
    amount_paid: float = Field(default=0.0)
    client_name: str = Field(default="")
    client_number: int = Field(default=0)
    current_upb: float = Field(default=0.0)
    file_number: int = Field(default=0)
    listed_date: date = Field(default_factory=date.today)
    listed_date_day: int = Field(default=0)
    listed_date_month: int = Field(default=0)
    listed_date_year: int = Field(default=0)
    operator: str = Field(default="")
    original_upb_loaded: float = Field(default=0.0)
    tu_score: int = Field(default=0)
    zip_code: str = Field(default="")
