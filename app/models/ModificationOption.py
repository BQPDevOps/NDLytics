from pydantic import BaseModel


class ModificationOption(BaseModel):
    """A modification option."""

    term: int
    interest_rate: float
    monthly_payment: float
    down_payment: float
    new_principal_balance: float
    has_deferred_interest: bool
    has_deferred_principal: bool
    deferred_type: str
