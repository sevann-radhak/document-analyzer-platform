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
    dependencies=[Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]))]
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
    
    Supports filtering by:
    - Event type (Document upload, AI, User interaction)
    - Description (partial match, case-insensitive)
    - Date range (start_date and end_date)
    - User ID
    
    Results are paginated and ordered by creation date (most recent first).
    
    Requires authentication with user, admin, or moderator role.
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
    dependencies=[Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]))]
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
    
    Supports the same filtering options as the events list endpoint:
    - Event type (Document upload, AI, User interaction)
    - Description (partial match, case-insensitive)
    - Date range (start_date and end_date)
    - User ID
    
    Returns an Excel file (.xlsx) with all matching events.
    The file includes formatted headers and all event data.
    
    Requires authentication with user, admin, or moderator role.
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

