"""Base models for the application."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MongoModel(BaseModel):
    """Base model for MongoDB documents."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        json_schema_extra={"example": {}},
    )

    id: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
