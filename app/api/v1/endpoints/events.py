"""Event history endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from datetime import datetime

from app.schemas.event import EventResponse, EventFilter, EventListResponse
from app.services.event_service import get_events, count_events
from app.utils.database import get_db
from app.utils.excel_export import export_events_to_excel
from app.core.dependencies import require_roles
from app.core.constants import UserRoles

router = APIRouter()


@router.get(
    "",
    response_model=EventListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]))],
    summary="Get Event Log",
    description="""
    Retrieve event log with optional filters and pagination.
    
    Returns a paginated list of events ordered by creation date (most recent first).
    Supports filtering by event type, description, date range, and user ID.
    
    **Authentication Required**: Yes (Bearer token)
    **Required Role**: user, admin, or moderator
    """,
    response_description="Paginated list of events",
    tags=["events"]
)
async def get_events_endpoint(
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type (Document upload, AI, User interaction)"
    ),
    description: Optional[str] = Query(
        None,
        description="Filter by description (partial match, case-insensitive)"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Filter events from this date (inclusive, ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Filter events until this date (inclusive, ISO format)"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user ID"
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip (for pagination)"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return (max 1000)"
    ),
    current_user: Dict[str, Any] = Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR])),
    db: Session = Depends(get_db)
) -> EventListResponse:
    """
    Get event log with optional filters.
    
    **Query Parameters**:
    - `event_type`: Filter by event type (Document upload, AI, User interaction)
    - `description`: Filter by description (partial match, case-insensitive)
    - `start_date`: Filter events from this date (ISO format, inclusive)
    - `end_date`: Filter events until this date (ISO format, inclusive)
    - `user_id`: Filter by user ID
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 100, max: 1000)
    
    **Response**:
    - `events`: List of event objects
    - `total`: Total number of events matching filters
    - `skip`: Number of records skipped
    - `limit`: Maximum records returned
    
    **Example Request**:
    ```
    GET /api/v1/events?event_type=Document%20upload&start_date=2024-12-01T00:00:00Z&limit=50
    ```
    
    **Example Response**:
    ```json
    {
        "events": [
            {
                "id": 1,
                "event_type": "Document upload",
                "description": "Document 'invoice.pdf' uploaded and classified as 'Invoice'. Document ID: 1",
                "user_id": 1,
                "created_at": "2024-12-06T10:30:00Z"
            }
        ],
        "total": 1,
        "skip": 0,
        "limit": 50
    }
    ```
    
    **Errors**:
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: Insufficient permissions
    - `500 Internal Server Error`: Database errors
    """
    try:
        events = get_events(
            db=db,
            event_type=event_type,
            user_id=user_id,
            description=description,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        total = count_events(
            db=db,
            event_type=event_type,
            user_id=user_id,
            description=description,
            start_date=start_date,
            end_date=end_date
        )
        
        event_responses = [
            EventResponse(
                id=event.id,
                event_type=event.event_type,
                description=event.description,
                user_id=event.user_id,
                created_at=event.created_at
            )
            for event in events
        ]
        
        return EventListResponse(
            events=event_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        ) from e


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]))],
    summary="Export Events to Excel",
    description="""
    Export event log to Excel format with optional filters.
    
    Generates an Excel file (.xlsx) containing all events matching the specified filters.
    The file includes formatted headers and all event data.
    
    **Authentication Required**: Yes (Bearer token)
    **Required Role**: user, admin, or moderator
    
    **Supported Filters**: Same as the events list endpoint
    **Export Limit**: Up to 10,000 events per export
    """,
    response_description="Excel file (.xlsx) with event data",
    tags=["events"]
)
async def export_events_endpoint(
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type (Document upload, AI, User interaction)"
    ),
    description: Optional[str] = Query(
        None,
        description="Filter by description (partial match, case-insensitive)"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Filter events from this date (inclusive, ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Filter events until this date (inclusive, ISO format)"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Filter by user ID"
    ),
    current_user: Dict[str, Any] = Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR])),
    db: Session = Depends(get_db)
) -> Response:
    """
    Export event log to Excel format with optional filters.
    
    **Query Parameters** (same as events list endpoint):
    - `event_type`: Filter by event type
    - `description`: Filter by description (partial match)
    - `start_date`: Filter events from this date (ISO format)
    - `end_date`: Filter events until this date (ISO format)
    - `user_id`: Filter by user ID
    
    **Response**:
    - Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
    - File name: `events_export_YYYYMMDD_HHMMSS.xlsx`
    - Excel file with columns: Event ID, Event Type, Description, User ID, Created At, Updated At
    
    **Example Request**:
    ```
    GET /api/v1/events/export?event_type=Document%20upload&start_date=2024-12-01T00:00:00Z
    ```
    
    **Example Response**:
    - Binary Excel file download
    - Filename: `events_export_20241206_103000.xlsx`
    
    **Errors**:
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: Insufficient permissions
    - `404 Not Found`: No events found matching the filters
    - `500 Internal Server Error`: Database or Excel generation errors
    """
    try:
        events = get_events(
            db=db,
            event_type=event_type,
            user_id=user_id,
            description=description,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=10000
        )
        
        if not events:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No events found matching the specified filters"
            )
        
        excel_file = export_events_to_excel(events)
        excel_content = excel_file.getvalue()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"events_export_{timestamp}.xlsx"
        
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during export: {str(e)}"
        ) from e

