from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .UserProfileModel import UserProfileModel


class UserModelExpanded(BaseModel):
    username: str
    user_id: str
    email: str
    given_name: str
    family_name: str
    phone_number: Optional[str]
    company_id: str
    enabled: bool
    user_status: str
    user_create_date: datetime
    user_last_modified_date: datetime
    groups: List[str] = []
    profile: Optional[UserProfileModel] = None

    @classmethod
    def from_cognito_user(cls, user_data: dict, company_id: str = None):
        attributes = {
            attr["Name"]: attr["Value"] for attr in user_data.get("Attributes", [])
        }

        # Get the role from Cognito groups
        groups = user_data.get("Groups", [])
        role = next(
            (g.replace("_role_", "") for g in groups if g.startswith("_role_")), ""
        )

        # Create initial profile with role from Cognito
        initial_profile = UserProfileModel(
            user_id=attributes.get("sub"),
            company_id=company_id,
            role=role,  # Set role from Cognito groups
            responsibilities=[],
            updated_on=datetime.now(),
            updated_by=attributes.get("sub"),
            created_on=datetime.now(),
            created_by=attributes.get("sub"),
            goals=[],
        )

        return cls(
            username=user_data.get("Username"),
            user_id=attributes.get("sub"),
            email=attributes.get("email"),
            given_name=attributes.get("given_name"),
            family_name=attributes.get("family_name"),
            phone_number=attributes.get("phone_number"),
            company_id=attributes.get("custom:company_id", company_id),
            enabled=user_data.get("Enabled", False),
            user_status=user_data.get("UserStatus", ""),
            user_create_date=user_data.get("UserCreateDate"),
            user_last_modified_date=user_data.get("UserLastModifiedDate"),
            groups=groups,
            profile=initial_profile,  # Set the initial profile
        )
