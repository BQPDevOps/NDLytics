from pydantic import BaseModel
from .ModificationOption import ModificationOption
from .MortgageLoan import MortgageLoan


class ModificationRequest(BaseModel):
    """A modification request."""

    uid: str
    first_name: str
    last_name: str
    dob: str
    loan_number: str
    payoff_principal_balance: float
    payoff_accrued_interest: float
    payoff_legal_fees: float
    payoff_late_fees: float
    payoff_per_diem: float
    payoff_interest_rate: float
    payoff_expiration_date: str
    payoff_total_amount: float
    requested_monthly_payment: float
    requested_down_payment: float
    modification_options: list[ModificationOption]
    mortgage_loan: MortgageLoan
    created_at: str
    updated_at: str
    status: str
