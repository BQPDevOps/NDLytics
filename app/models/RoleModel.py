from pydantic import BaseModel
from typing import List
from datetime import datetime


class RoleModel(BaseModel):
    role_id: str
    role_name: str
    role_description: str
    role_reports_to: List[str]
    role_reporting_team: List[str]
    role_responsibilities: List[str]
    role_displayed_in_org: bool
    assigned_to: List[str]
    created_on: str
    created_by: str
    updated_on: str
    updated_by: str

    class Config:
        json_encoders = {
            datetime: lambda dt: int(
                dt.timestamp()
            )  # Convert to Unix timestamp for DynamoDB
        }

    @classmethod
    def from_dynamo_item(cls, item: dict):
        """Convert DynamoDB item to RoleModel"""
        return cls(
            role_id=item["role_id"]["S"],
            role_name=item["role_name"]["S"],
            role_description=item["role_description"]["S"],
            role_reports_to=[r["S"] for r in item["role_reports_to"]["L"]],
            role_reporting_team=[r["S"] for r in item["role_reporting_team"]["L"]],
            role_responsibilities=[r["S"] for r in item["role_responsibilities"]["L"]],
            role_displayed_in_org=item["role_displayed_in_org"]["BOOL"],
            assigned_to=[a["S"] for a in item["assigned_to"]["L"]],
            created_on=item["created_on"]["S"],
            created_by=item["created_by"]["S"],
            updated_on=item["updated_on"]["S"],
            updated_by=item["updated_by"]["S"],
        )

    def to_dynamo_item(self) -> dict:
        """Convert RoleModel to DynamoDB item format"""
        return {
            "role_id": {"S": self.role_id},
            "role_name": {"S": self.role_name},
            "role_description": {"S": self.role_description},
            "role_reports_to": {"L": [{"S": role} for role in self.role_reports_to]},
            "role_reporting_team": {
                "L": [{"S": role} for role in self.role_reporting_team]
            },
            "role_responsibilities": {
                "L": [{"S": resp} for resp in self.role_responsibilities]
            },
            "role_displayed_in_org": {"BOOL": self.role_displayed_in_org},
            "assigned_to": {"L": [{"S": user} for user in self.assigned_to]},
            "created_on": {"S": self.created_on},
            "created_by": {"S": self.created_by},
            "updated_on": {"S": self.updated_on},
            "updated_by": {"S": self.updated_by},
        }
