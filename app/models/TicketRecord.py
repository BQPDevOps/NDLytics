from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime


class TicketRecord(BaseModel):
    primary_key: UUID = Field(default_factory=uuid4)
    sort_key: str = Field(alias="tag")
    uuid: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    attributes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "primary_key": "123e4567-e89b-12d3-a456-426614174000",
                "uuid": "ticket_system",
                "tag": "ticket_system",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "attributes": {
                    "ticket_id": {"value": "TICKET-001", "data_type": "string"},
                    "description": {"value": "Login Issue", "data_type": "string"},
                    "status": {"value": "open", "data_type": "string"},
                },
            }
        }

    def to_dict(self) -> dict:
        """Convert TicketRecord to simplified dictionary format matching ag-grid columns."""
        return {
            "uuid": self.uuid,
            "ticket_id": self.attributes.get("ticket_id", {}).get("value", ""),
            "status": self.attributes.get("status", {}).get("value", ""),
            "description": self.attributes.get("description", {}).get("value", ""),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
