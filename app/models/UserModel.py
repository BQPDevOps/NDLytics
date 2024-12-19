from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserModel(BaseModel):
    given_name: str  # Cognito's first name attribute
    family_name: str  # Cognito's last name attribute
    email: EmailStr  # Cognito's email attribute
    phone_number: Optional[str]  # Cognito's phone_number attribute
    company_id: str  # Cognito's custom:company_id attribute
    name: str  # Cognito's name attribute (full name)
    groups: List[str]  # Cognito user groups (permissions)

    @classmethod
    def from_cognito_attributes(cls, attributes: dict):
        """
        Create UserModel from Cognito user attributes
        """
        return cls(
            given_name=attributes.get("given_name", ""),
            family_name=attributes.get("family_name", ""),
            email=attributes.get("email", ""),
            phone_number=attributes.get("phone_number"),
            company_id=attributes.get("custom:company_id", ""),
            name=attributes.get("name", ""),
            groups=attributes.get("cognito:groups", []),
        )

    def to_cognito_attributes(self) -> List[dict]:
        """
        Convert UserModel to Cognito attribute format
        """
        attributes = [
            {"Name": "given_name", "Value": self.given_name},
            {"Name": "family_name", "Value": self.family_name},
            {"Name": "email", "Value": str(self.email)},
            {"Name": "name", "Value": self.name},
            {"Name": "custom:company_id", "Value": self.company_id},
        ]

        if self.phone_number:
            attributes.append({"Name": "phone_number", "Value": self.phone_number})

        return attributes
