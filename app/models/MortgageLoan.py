from pydantic import BaseModel


class MortgageLoan(BaseModel):
    """A mortgage loan."""

    loan_number: str
    principal_balance: float
    borrower_first_name: str
    borrower_last_name: str
    property_address: str
    property_city: str
    property_state: str
    property_zip: str
    property_fmv: float
    senior_lien_amount: float
    note_purchase_date: str
    note_purchase_price: float
    mortgage_last_payment_date: str
    original_loan_amount: float
    original_interest_rate: float
    original_term: int
