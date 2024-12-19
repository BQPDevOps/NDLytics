from pydantic import BaseModel
from typing import List
from datetime import datetime
from .CompanyContactModel import CompanyContactModel
from .RoleModel import RoleModel


class CompanyModel(BaseModel):
    company_id: str
    company_users: List[str]
    company_name: str
    company_contacts: List[CompanyContactModel]
    company_roles: List[RoleModel]
    created_on: str
    created_by: str
    updated_on: str
    updated_by: str

    class Config:
        json_encoders = {datetime: lambda dt: int(dt.timestamp())}

    @classmethod
    def from_dynamo_item(cls, item: dict):
        """Convert DynamoDB item to CompanyModel"""
        return cls(
            company_id=item["company_id"]["S"],
            company_users=[u["S"] for u in item["company_users"]["L"]],
            company_name=item["company_name"]["S"],
            company_contacts=[
                CompanyContactModel(
                    contact_name=contact["M"]["contact_name"]["S"],
                    contact_role=contact["M"]["contact_role"]["S"],
                    contact_email=contact["M"]["contact_email"]["S"],
                    contact_phone=contact["M"]["contact_phone"]["S"],
                    primary_contact=contact["M"]["primary_contact"]["BOOL"],
                )
                for contact in item["company_contacts"]["L"]
            ],
            company_roles=[
                RoleModel(
                    role_id=role["M"]["role_id"]["S"],
                    role_name=role["M"]["role_name"]["S"],
                    role_description=role["M"]["role_description"]["S"],
                    role_reports_to=[
                        r["S"] for r in role["M"].get("role_reports_to", {"L": []})["L"]
                    ],
                    role_reporting_team=[
                        r["S"]
                        for r in role["M"].get("role_reporting_team", {"L": []})["L"]
                    ],
                    role_responsibilities=[
                        r["S"]
                        for r in role["M"].get("role_responsibilities", {"L": []})["L"]
                    ],
                    role_displayed_in_org=role["M"].get(
                        "role_displayed_in_org", {"BOOL": False}
                    )["BOOL"],
                    assigned_to=[
                        a["S"] for a in role["M"].get("assigned_to", {"L": []})["L"]
                    ],
                    created_on=role["M"].get("created_on", {"S": ""})["S"],
                    created_by=role["M"].get("created_by", {"S": ""})["S"],
                    updated_on=role["M"].get("updated_on", {"S": ""})["S"],
                    updated_by=role["M"].get("updated_by", {"S": ""})["S"],
                )
                for role in item["company_roles"]["L"]
            ],
            created_on=item.get("created_on", {"S": ""})["S"],
            created_by=item.get("created_by", {"S": ""})["S"],
            updated_on=item.get("updated_on", {"S": ""})["S"],
            updated_by=item.get("updated_by", {"S": ""})["S"],
        )

    def to_dynamo_item(self) -> dict:
        """Convert CompanyModel to DynamoDB item format"""
        return {
            "company_id": {"S": self.company_id},
            "company_users": {"L": [{"S": user} for user in self.company_users]},
            "company_name": {"S": self.company_name},
            "company_contacts": {
                "L": [
                    {
                        "M": {
                            "contact_name": {"S": contact.contact_name},
                            "contact_role": {"S": contact.contact_role},
                            "contact_email": {"S": contact.contact_email},
                            "contact_phone": {"S": contact.contact_phone},
                            "primary_contact": {"BOOL": contact.primary_contact},
                        }
                    }
                    for contact in self.company_contacts
                ]
            },
            "company_roles": {
                "L": [
                    {
                        "M": {
                            "role_id": {"S": role.role_id},
                            "role_name": {"S": role.role_name},
                            "role_description": {"S": role.role_description},
                            "role_reports_to": {
                                "L": [{"S": r} for r in role.role_reports_to]
                            },
                            "role_reporting_team": {
                                "L": [{"S": r} for r in role.role_reporting_team]
                            },
                            "role_responsibilities": {
                                "L": [{"S": r} for r in role.role_responsibilities]
                            },
                            "role_displayed_in_org": {
                                "BOOL": role.role_displayed_in_org
                            },
                            "created_on": {"S": role.created_on},
                            "created_by": {"S": role.created_by},
                            "updated_on": {"S": role.updated_on},
                            "updated_by": {"S": role.updated_by},
                        }
                    }
                    for role in self.company_roles
                ]
            },
            "created_on": {"S": self.created_on},
            "created_by": {"S": self.created_by},
            "updated_on": {"S": self.updated_on},
            "updated_by": {"S": self.updated_by},
        }
