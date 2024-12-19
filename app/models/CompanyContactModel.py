from pydantic import BaseModel


class CompanyContactModel(BaseModel):
    contact_name: str
    contact_role: str
    contact_email: str
    contact_phone: str
    primary_contact: bool
