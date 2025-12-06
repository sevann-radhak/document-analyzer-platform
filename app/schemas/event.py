"""Event schemas for event logging and history."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.services.event_service import EventType


class EventResponse(BaseModel):
    """Response schema for a single event."""
    
    id: int = Field(..., description="Event ID")
    event_type: str = Field(..., description="Type of event (Document upload, AI, User interaction)")
    description: str = Field(..., description="Event description")
    user_id: Optional[int] = Field(None, description="User ID associated with the event")
    created_at: datetime = Field(..., description="Timestamp when event was created")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "event_type": "Document upload",
                "description": "Document 'invoice.pdf' uploaded and classified as 'Invoice'. Document ID: 1",
                "user_id": 1,
                "created_at": "2024-12-06T10:30:00Z"
            }
        }
    )


class EventFilter(BaseModel):
    """Filter schema for event queries."""
    
    event_type: Optional[str] = Field(
        None,
        description="Filter by event type (Document upload, AI, User interaction)"
    )
    description: Optional[str] = Field(
        None,
        description="Filter by description (partial match, case-insensitive)"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Filter events from this date (inclusive)"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Filter events until this date (inclusive)"
    )
    user_id: Optional[int] = Field(
        None,
        description="Filter by user ID"
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip (for pagination)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return (max 1000)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "Document upload",
                "description": "invoice",
                "start_date": "2024-12-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "user_id": 1,
                "skip": 0,
                "limit": 50
            }
        }
    )


class EventListResponse(BaseModel):
    """Response schema for a list of events."""
    
    events: List[EventResponse] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events matching the filters")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "events": [
                    {
                        "id": 1,
                        "event_type": "Document upload",
                        "description": "Document 'invoice.pdf' uploaded and classified as 'Invoice'. Document ID: 1",
                        "user_id": 1,
                        "created_at": "2024-12-06T10:30:00Z"
                    },
                    {
                        "id": 2,
                        "event_type": "AI",
                        "description": "AI classified document 'report.pdf' as 'Information'",
                        "user_id": 1,
                        "created_at": "2024-12-06T10:25:00Z"
                    }
                ],
                "total": 2,
                "skip": 0,
                "limit": 100
            }
        }
    )

