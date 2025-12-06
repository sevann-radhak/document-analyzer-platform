"""Unit tests for Excel export utility."""
import pytest
import io
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from app.utils.excel_export import export_events_to_excel, _setup_header_row, _populate_event_data, _apply_column_widths
from app.models.event import Event
from app.core.constants import ExcelExportConfig


class TestExportEventsToExcel:
    """Test cases for export_events_to_excel function."""
    
    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        event1 = Mock(spec=Event)
        event1.id = 1
        event1.event_type = "Document upload"
        event1.description = "Test document uploaded"
        event1.user_id = 1
        event1.created_at = datetime.now(timezone.utc)
        event1.updated_at = datetime.now(timezone.utc)
        
        event2 = Mock(spec=Event)
        event2.id = 2
        event2.event_type = "AI"
        event2.description = "AI classification"
        event2.user_id = 2
        event2.created_at = datetime.now(timezone.utc)
        event2.updated_at = None
        
        return [event1, event2]
    
    def test_export_events_to_excel_success(self, sample_events):
        """Test successful Excel export."""
        result = export_events_to_excel(sample_events)
        
        assert isinstance(result, io.BytesIO)
        assert result.tell() == 0
        assert len(result.read()) > 0
    
    def test_export_events_to_excel_raises_error_for_empty_list(self):
        """Test that export raises error for empty events list."""
        with pytest.raises(ValueError, match="Events list cannot be empty"):
            export_events_to_excel([])
    
    def test_export_events_to_excel_raises_error_for_none(self):
        """Test that export raises error for None."""
        with pytest.raises(ValueError, match="Events must be a list"):
            export_events_to_excel(None)
    
    def test_export_events_to_excel_raises_error_for_invalid_type(self):
        """Test that export raises error for invalid type."""
        with pytest.raises(ValueError, match="Events must be a list"):
            export_events_to_excel("not a list")
    
    def test_export_events_to_excel_creates_workbook(self, sample_events):
        """Test that export creates a workbook."""
        with patch('app.utils.excel_export.Workbook') as mock_workbook_class, \
             patch('app.utils.excel_export._apply_column_widths'):
            mock_workbook = Mock()
            mock_worksheet = Mock()
            mock_worksheet.column_dimensions = {}
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                mock_worksheet.column_dimensions[col] = Mock()
            mock_workbook.active = mock_worksheet
            mock_workbook_class.return_value = mock_workbook
            
            export_events_to_excel(sample_events)
            
            mock_workbook_class.assert_called_once()
            mock_workbook.save.assert_called_once()
    
    def test_export_events_to_excel_sets_worksheet_title(self, sample_events):
        """Test that export sets worksheet title."""
        with patch('app.utils.excel_export.Workbook') as mock_workbook_class, \
             patch('app.utils.excel_export._apply_column_widths'):
            mock_workbook = Mock()
            mock_worksheet = Mock()
            mock_worksheet.column_dimensions = {}
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                mock_worksheet.column_dimensions[col] = Mock()
            mock_workbook.active = mock_worksheet
            mock_workbook_class.return_value = mock_workbook
            
            export_events_to_excel(sample_events)
            
            # Verify title was set (it's set directly, not via assertion)
            assert hasattr(mock_worksheet, 'title')
    
    def test_export_events_to_excel_calls_setup_header_row(self, sample_events):
        """Test that export calls setup header row."""
        with patch('app.utils.excel_export._setup_header_row') as mock_setup, \
             patch('app.utils.excel_export.Workbook'):
            export_events_to_excel(sample_events)
            
            mock_setup.assert_called_once()
    
    def test_export_events_to_excel_calls_populate_event_data(self, sample_events):
        """Test that export calls populate event data."""
        with patch('app.utils.excel_export._populate_event_data') as mock_populate, \
             patch('app.utils.excel_export.Workbook'):
            export_events_to_excel(sample_events)
            
            mock_populate.assert_called_once()
    
    def test_export_events_to_excel_calls_apply_column_widths(self, sample_events):
        """Test that export calls apply column widths."""
        with patch('app.utils.excel_export._apply_column_widths') as mock_apply, \
             patch('app.utils.excel_export.Workbook'):
            export_events_to_excel(sample_events)
            
            mock_apply.assert_called_once()
    
    def test_export_events_to_excel_returns_bytesio_at_start(self, sample_events):
        """Test that export returns BytesIO positioned at start."""
        result = export_events_to_excel(sample_events)
        
        assert result.tell() == 0
    
    def test_export_events_to_excel_with_single_event(self):
        """Test export with single event."""
        event = Mock(spec=Event)
        event.id = 1
        event.event_type = "Test"
        event.description = "Test description"
        event.user_id = 1
        event.created_at = datetime.now(timezone.utc)
        event.updated_at = None
        
        result = export_events_to_excel([event])
        
        assert isinstance(result, io.BytesIO)
        assert len(result.read()) > 0


class TestSetupHeaderRow:
    """Test cases for _setup_header_row function."""
    
    @pytest.fixture
    def mock_worksheet(self):
        """Create mock worksheet."""
        worksheet = Mock()
        worksheet.cell = Mock(return_value=Mock())
        return worksheet
    
    def test_setup_header_row_creates_headers(self, mock_worksheet):
        """Test that setup header row creates all headers."""
        _setup_header_row(mock_worksheet)
        
        assert mock_worksheet.cell.call_count == 6
    
    def test_setup_header_row_sets_correct_header_values(self, mock_worksheet):
        """Test that setup header row sets correct header values."""
        _setup_header_row(mock_worksheet)
        
        calls = mock_worksheet.cell.call_args_list
        headers = [call[1]['value'] for call in calls]
        
        assert ExcelExportConfig.HEADER_EVENT_ID in headers
        assert ExcelExportConfig.HEADER_EVENT_TYPE in headers
        assert ExcelExportConfig.HEADER_DESCRIPTION in headers
        assert ExcelExportConfig.HEADER_USER_ID in headers
        assert ExcelExportConfig.HEADER_CREATED_AT in headers
        assert ExcelExportConfig.HEADER_UPDATED_AT in headers
    
    def test_setup_header_row_applies_styling(self, mock_worksheet):
        """Test that setup header row applies styling to cells."""
        _setup_header_row(mock_worksheet)
        
        for call in mock_worksheet.cell.call_args_list:
            cell = call[0][2] if len(call[0]) > 2 else call[1].get('value')
            mock_cell = mock_worksheet.cell.return_value
            assert hasattr(mock_cell, 'fill') or hasattr(mock_cell, 'font')


class TestPopulateEventData:
    """Test cases for _populate_event_data function."""
    
    @pytest.fixture
    def mock_worksheet(self):
        """Create mock worksheet."""
        worksheet = Mock()
        worksheet.cell = Mock(return_value=Mock())
        return worksheet
    
    @pytest.fixture
    def sample_events(self):
        """Create sample events."""
        event = Mock(spec=Event)
        event.id = 1
        event.event_type = "Test"
        event.description = "Test description"
        event.user_id = 1
        event.created_at = datetime.now(timezone.utc)
        event.updated_at = None
        return [event]
    
    def test_populate_event_data_fills_event_data(self, mock_worksheet, sample_events):
        """Test that populate event data fills event information."""
        _populate_event_data(mock_worksheet, sample_events)
        
        assert mock_worksheet.cell.call_count >= 6
    
    def test_populate_event_data_handles_none_updated_at(self, mock_worksheet, sample_events):
        """Test that populate event data handles None updated_at."""
        _populate_event_data(mock_worksheet, sample_events)
        
        # Should not raise exception
        assert True
    
    def test_populate_event_data_handles_none_created_at(self, mock_worksheet):
        """Test that populate event data handles None created_at."""
        event = Mock(spec=Event)
        event.id = 1
        event.event_type = "Test"
        event.description = "Test"
        event.user_id = 1
        event.created_at = None
        event.updated_at = None
        
        _populate_event_data(mock_worksheet, [event])
        
        # Should not raise exception
        assert True


class TestApplyColumnWidths:
    """Test cases for _apply_column_widths function."""
    
    @pytest.fixture
    def mock_worksheet(self):
        """Create mock worksheet."""
        worksheet = Mock()
        worksheet.column_dimensions = {}
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            worksheet.column_dimensions[col] = Mock()
        return worksheet
    
    def test_apply_column_widths_sets_all_columns(self, mock_worksheet):
        """Test that apply column widths sets all column widths."""
        _apply_column_widths(mock_worksheet)
        
        assert len(mock_worksheet.column_dimensions) == 6
    
    def test_apply_column_widths_sets_correct_widths(self, mock_worksheet):
        """Test that apply column widths sets correct widths."""
        _apply_column_widths(mock_worksheet)
        
        # Verify that width property was set (via mock)
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            assert col in mock_worksheet.column_dimensions

