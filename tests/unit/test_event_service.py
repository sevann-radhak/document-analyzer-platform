"""Unit tests for event service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from app.services.event_service import (
    create_event,
    get_event_by_id,
    get_events,
    count_events,
    log_document_upload,
    log_ai_classification,
    log_user_interaction,
    EventType
)
from app.models.event import Event
from tests.unit.conftest import mock_db


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return Event(
        id=1,
        event_type=EventType.DOCUMENT_UPLOAD,
        description="Test event description",
        user_id=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_events():
    """Create multiple sample events for testing."""
    base_time = datetime.now(timezone.utc)
    return [
        Event(
            id=1,
            event_type=EventType.DOCUMENT_UPLOAD,
            description="Document 'test.pdf' uploaded",
            user_id=1,
            created_at=base_time,
            updated_at=base_time
        ),
        Event(
            id=2,
            event_type=EventType.AI,
            description="AI classified document 'test.pdf' as 'Invoice'",
            user_id=1,
            created_at=base_time + timedelta(seconds=10),
            updated_at=base_time + timedelta(seconds=10)
        ),
        Event(
            id=3,
            event_type=EventType.USER_INTERACTION,
            description="User logged in",
            user_id=2,
            created_at=base_time + timedelta(seconds=20),
            updated_at=base_time + timedelta(seconds=20)
        )
    ]


@pytest.fixture
def mock_event_repository():
    """Mock for EventRepository."""
    with patch('app.services.event_service.EventRepository') as mock_repo_class:
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        yield mock_repo


class TestCreateEvent:
    """Test cases for create_event function."""

    def test_create_event_returns_event_instance(self, mock_db, mock_event_repository, sample_event):
        """Test that create_event returns an Event instance."""
        mock_event_repository.create.return_value = sample_event
        
        result = create_event(
            db=mock_db,
            event_type=EventType.DOCUMENT_UPLOAD,
            description="Test description",
            user_id=1
        )
        
        assert isinstance(result, Event)
        assert result.id == 1

    def test_create_event_calls_repository_create(self, mock_db, mock_event_repository, sample_event):
        """Test that create_event calls repository create method."""
        mock_event_repository.create.return_value = sample_event
        
        create_event(
            db=mock_db,
            event_type=EventType.DOCUMENT_UPLOAD,
            description="Test description",
            user_id=1
        )
        
        mock_event_repository.create.assert_called_once_with(
            event_type=EventType.DOCUMENT_UPLOAD,
            description="Test description",
            user_id=1
        )

    def test_create_event_without_user_id(self, mock_db, mock_event_repository, sample_event):
        """Test that create_event works without user_id."""
        sample_event.user_id = None
        mock_event_repository.create.return_value = sample_event
        
        result = create_event(
            db=mock_db,
            event_type=EventType.AI,
            description="Test description",
            user_id=None
        )
        
        assert result.user_id is None
        mock_event_repository.create.assert_called_once_with(
            event_type=EventType.AI,
            description="Test description",
            user_id=None
        )

    def test_create_event_with_different_event_types(self, mock_db, mock_event_repository, sample_event):
        """Test that create_event works with different event types."""
        event_types = [EventType.DOCUMENT_UPLOAD, EventType.AI, EventType.USER_INTERACTION]
        
        for event_type in event_types:
            sample_event.event_type = event_type
            mock_event_repository.create.return_value = sample_event
            
            result = create_event(
                db=mock_db,
                event_type=event_type,
                description="Test",
                user_id=1
            )
            
            assert result.event_type == event_type


class TestGetEventById:
    """Test cases for get_event_by_id function."""

    def test_get_event_by_id_returns_event_when_found(self, mock_db, mock_event_repository, sample_event):
        """Test that get_event_by_id returns event when found."""
        mock_event_repository.get_by_id.return_value = sample_event
        
        result = get_event_by_id(db=mock_db, event_id=1)
        
        assert result == sample_event
        mock_event_repository.get_by_id.assert_called_once_with(1)

    def test_get_event_by_id_returns_none_when_not_found(self, mock_db, mock_event_repository):
        """Test that get_event_by_id returns None when event not found."""
        mock_event_repository.get_by_id.return_value = None
        
        result = get_event_by_id(db=mock_db, event_id=999)
        
        assert result is None
        mock_event_repository.get_by_id.assert_called_once_with(999)

    def test_get_event_by_id_calls_repository_with_correct_id(self, mock_db, mock_event_repository, sample_event):
        """Test that get_event_by_id calls repository with correct ID."""
        mock_event_repository.get_by_id.return_value = sample_event
        
        get_event_by_id(db=mock_db, event_id=5)
        
        mock_event_repository.get_by_id.assert_called_once_with(5)


class TestGetEvents:
    """Test cases for get_events function."""

    def test_get_events_returns_list_of_events(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events returns a list of events."""
        mock_event_repository.get_events.return_value = sample_events
        
        result = get_events(db=mock_db)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(event, Event) for event in result)

    def test_get_events_filters_by_event_type(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events filters by event type."""
        filtered_events = [sample_events[0]]
        mock_event_repository.get_events.return_value = filtered_events
        
        result = get_events(db=mock_db, event_type=EventType.DOCUMENT_UPLOAD)
        
        mock_event_repository.get_events.assert_called_once()
        call_kwargs = mock_event_repository.get_events.call_args[1]
        assert call_kwargs["event_type"] == EventType.DOCUMENT_UPLOAD

    def test_get_events_filters_by_user_id(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events filters by user ID."""
        filtered_events = [sample_events[0], sample_events[1]]
        mock_event_repository.get_events.return_value = filtered_events
        
        result = get_events(db=mock_db, user_id=1)
        
        call_kwargs = mock_event_repository.get_events.call_args[1]
        assert call_kwargs["user_id"] == 1

    def test_get_events_filters_by_description(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events filters by description."""
        filtered_events = [sample_events[0]]
        mock_event_repository.get_events.return_value = filtered_events
        
        result = get_events(db=mock_db, description="uploaded")
        
        call_kwargs = mock_event_repository.get_events.call_args[1]
        assert call_kwargs["description"] == "uploaded"

    def test_get_events_filters_by_date_range(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events filters by date range."""
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        mock_event_repository.get_events.return_value = sample_events
        
        result = get_events(db=mock_db, start_date=start_date, end_date=end_date)
        
        call_kwargs = mock_event_repository.get_events.call_args[1]
        assert call_kwargs["start_date"] == start_date
        assert call_kwargs["end_date"] == end_date

    def test_get_events_supports_pagination(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events supports pagination with skip and limit."""
        mock_event_repository.get_events.return_value = sample_events[1:]
        
        result = get_events(db=mock_db, skip=1, limit=2)
        
        call_kwargs = mock_event_repository.get_events.call_args[1]
        assert call_kwargs["skip"] == 1
        assert call_kwargs["limit"] == 2

    def test_get_events_returns_empty_list_when_no_matches(self, mock_db, mock_event_repository):
        """Test that get_events returns empty list when no events match."""
        mock_event_repository.get_events.return_value = []
        
        result = get_events(db=mock_db, event_type="NonExistent")
        
        assert result == []
        assert len(result) == 0

    def test_get_events_combines_multiple_filters(self, mock_db, mock_event_repository, sample_events):
        """Test that get_events combines multiple filters correctly."""
        filtered_events = [sample_events[0]]
        mock_event_repository.get_events.return_value = filtered_events
        
        result = get_events(
            db=mock_db,
            event_type=EventType.DOCUMENT_UPLOAD,
            user_id=1,
            description="test",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        
        call_kwargs = mock_event_repository.get_events.call_args[1]
        assert call_kwargs["event_type"] == EventType.DOCUMENT_UPLOAD
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["description"] == "test"
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None


class TestCountEvents:
    """Test cases for count_events function."""

    def test_count_events_returns_integer(self, mock_db, mock_event_repository):
        """Test that count_events returns an integer."""
        mock_event_repository.count_with_filters.return_value = 5
        
        result = count_events(db=mock_db)
        
        assert isinstance(result, int)
        assert result == 5

    def test_count_events_filters_by_event_type(self, mock_db, mock_event_repository):
        """Test that count_events filters by event type."""
        mock_event_repository.count_with_filters.return_value = 3
        
        result = count_events(db=mock_db, event_type=EventType.DOCUMENT_UPLOAD)
        
        call_kwargs = mock_event_repository.count_with_filters.call_args[1]
        assert call_kwargs["event_type"] == EventType.DOCUMENT_UPLOAD

    def test_count_events_filters_by_user_id(self, mock_db, mock_event_repository):
        """Test that count_events filters by user ID."""
        mock_event_repository.count_with_filters.return_value = 2
        
        result = count_events(db=mock_db, user_id=1)
        
        call_kwargs = mock_event_repository.count_with_filters.call_args[1]
        assert call_kwargs["user_id"] == 1

    def test_count_events_filters_by_description(self, mock_db, mock_event_repository):
        """Test that count_events filters by description."""
        mock_event_repository.count_with_filters.return_value = 1
        
        result = count_events(db=mock_db, description="invoice")
        
        call_kwargs = mock_event_repository.count_with_filters.call_args[1]
        assert call_kwargs["description"] == "invoice"

    def test_count_events_filters_by_date_range(self, mock_db, mock_event_repository):
        """Test that count_events filters by date range."""
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        mock_event_repository.count_with_filters.return_value = 10
        
        result = count_events(db=mock_db, start_date=start_date, end_date=end_date)
        
        call_kwargs = mock_event_repository.count_with_filters.call_args[1]
        assert call_kwargs["start_date"] == start_date
        assert call_kwargs["end_date"] == end_date

    def test_count_events_returns_zero_when_no_matches(self, mock_db, mock_event_repository):
        """Test that count_events returns 0 when no events match."""
        mock_event_repository.count_with_filters.return_value = 0
        
        result = count_events(db=mock_db, event_type="NonExistent")
        
        assert result == 0

    def test_count_events_combines_multiple_filters(self, mock_db, mock_event_repository):
        """Test that count_events combines multiple filters."""
        mock_event_repository.count_with_filters.return_value = 5
        
        result = count_events(
            db=mock_db,
            event_type=EventType.AI,
            user_id=1,
            description="classified",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc)
        )
        
        call_kwargs = mock_event_repository.count_with_filters.call_args[1]
        assert call_kwargs["event_type"] == EventType.AI
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["description"] == "classified"
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None


class TestLogDocumentUpload:
    """Test cases for log_document_upload function."""

    def test_log_document_upload_returns_event(self, mock_db, mock_event_repository, sample_event):
        """Test that log_document_upload returns an Event."""
        sample_event.event_type = EventType.DOCUMENT_UPLOAD
        mock_event_repository.create.return_value = sample_event
        
        result = log_document_upload(
            db=mock_db,
            filename="test.pdf",
            classification="Invoice",
            document_id=123,
            user_id=1
        )
        
        assert isinstance(result, Event)
        assert result.event_type == EventType.DOCUMENT_UPLOAD

    def test_log_document_upload_creates_correct_description(self, mock_db, mock_event_repository, sample_event):
        """Test that log_document_upload creates correct description."""
        mock_event_repository.create.return_value = sample_event
        
        log_document_upload(
            db=mock_db,
            filename="invoice.pdf",
            classification="Invoice",
            document_id=456,
            user_id=1
        )
        
        call_kwargs = mock_event_repository.create.call_args[1]
        assert "invoice.pdf" in call_kwargs["description"]
        assert "Invoice" in call_kwargs["description"]
        assert "456" in call_kwargs["description"]

    def test_log_document_upload_without_user_id(self, mock_db, mock_event_repository, sample_event):
        """Test that log_document_upload works without user_id."""
        sample_event.user_id = None
        mock_event_repository.create.return_value = sample_event
        
        result = log_document_upload(
            db=mock_db,
            filename="test.pdf",
            classification="Information",
            document_id=789,
            user_id=None
        )
        
        call_kwargs = mock_event_repository.create.call_args[1]
        assert call_kwargs["user_id"] is None


class TestLogAiClassification:
    """Test cases for log_ai_classification function."""

    def test_log_ai_classification_returns_event(self, mock_db, mock_event_repository, sample_event):
        """Test that log_ai_classification returns an Event."""
        sample_event.event_type = EventType.AI
        mock_event_repository.create.return_value = sample_event
        
        result = log_ai_classification(
            db=mock_db,
            filename="test.pdf",
            classification="Invoice",
            user_id=1
        )
        
        assert isinstance(result, Event)
        assert result.event_type == EventType.AI

    def test_log_ai_classification_creates_correct_description(self, mock_db, mock_event_repository, sample_event):
        """Test that log_ai_classification creates correct description."""
        mock_event_repository.create.return_value = sample_event
        
        log_ai_classification(
            db=mock_db,
            filename="report.pdf",
            classification="Information",
            user_id=1
        )
        
        call_kwargs = mock_event_repository.create.call_args[1]
        assert "report.pdf" in call_kwargs["description"]
        assert "Information" in call_kwargs["description"]
        assert call_kwargs["event_type"] == EventType.AI


class TestLogUserInteraction:
    """Test cases for log_user_interaction function."""

    def test_log_user_interaction_returns_event(self, mock_db, mock_event_repository, sample_event):
        """Test that log_user_interaction returns an Event."""
        sample_event.event_type = EventType.USER_INTERACTION
        mock_event_repository.create.return_value = sample_event
        
        result = log_user_interaction(
            db=mock_db,
            description="User logged in",
            user_id=1
        )
        
        assert isinstance(result, Event)
        assert result.event_type == EventType.USER_INTERACTION

    def test_log_user_interaction_uses_provided_description(self, mock_db, mock_event_repository, sample_event):
        """Test that log_user_interaction uses provided description."""
        mock_event_repository.create.return_value = sample_event
        
        log_user_interaction(
            db=mock_db,
            description="User viewed report",
            user_id=2
        )
        
        call_kwargs = mock_event_repository.create.call_args[1]
        assert call_kwargs["description"] == "User viewed report"
        assert call_kwargs["event_type"] == EventType.USER_INTERACTION
        assert call_kwargs["user_id"] == 2

    def test_log_user_interaction_without_user_id(self, mock_db, mock_event_repository, sample_event):
        """Test that log_user_interaction works without user_id."""
        sample_event.user_id = None
        mock_event_repository.create.return_value = sample_event
        
        result = log_user_interaction(
            db=mock_db,
            description="System event",
            user_id=None
        )
        
        call_kwargs = mock_event_repository.create.call_args[1]
        assert call_kwargs["user_id"] is None

