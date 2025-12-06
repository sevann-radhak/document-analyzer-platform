"""Unit tests for logger utility functions."""
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from app.utils.logger import (
    log_event,
    log_function_call,
    log_performance,
    log_error_with_context,
    timed_operation
)


class TestLogEvent:
    """Test cases for log_event function."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=logging.Logger)
    
    def test_log_event_logs_with_basic_message(self, mock_logger):
        """Test that log_event logs with basic message."""
        log_event(mock_logger, logging.INFO, "Test message")
        
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.INFO
        assert call_args[0][1] == "Test message"
    
    def test_log_event_includes_event_type(self, mock_logger):
        """Test that log_event includes event_type in extra."""
        log_event(mock_logger, logging.INFO, "Test", event_type="Document upload")
        
        call_args = mock_logger.log.call_args
        assert call_args[1]['extra']['event_type'] == "Document upload"
    
    def test_log_event_includes_user_id(self, mock_logger):
        """Test that log_event includes user_id in extra."""
        log_event(mock_logger, logging.INFO, "Test", user_id=1)
        
        call_args = mock_logger.log.call_args
        assert call_args[1]['extra']['user_id'] == 1
    
    def test_log_event_includes_document_id(self, mock_logger):
        """Test that log_event includes document_id in extra."""
        log_event(mock_logger, logging.INFO, "Test", document_id=1)
        
        call_args = mock_logger.log.call_args
        assert call_args[1]['extra']['document_id'] == 1
    
    def test_log_event_includes_file_id(self, mock_logger):
        """Test that log_event includes file_id in extra."""
        log_event(mock_logger, logging.INFO, "Test", file_id=1)
        
        call_args = mock_logger.log.call_args
        assert call_args[1]['extra']['file_id'] == 1
    
    def test_log_event_includes_additional_kwargs(self, mock_logger):
        """Test that log_event includes additional kwargs in extra."""
        log_event(mock_logger, logging.INFO, "Test", custom_key="custom_value")
        
        call_args = mock_logger.log.call_args
        assert call_args[1]['extra']['custom_key'] == "custom_value"
    
    def test_log_event_combines_all_fields(self, mock_logger):
        """Test that log_event combines all fields."""
        log_event(
            mock_logger,
            logging.INFO,
            "Test",
            event_type="Test",
            user_id=1,
            document_id=2,
            file_id=3,
            custom="value"
        )
        
        call_args = mock_logger.log.call_args
        extra = call_args[1]['extra']
        assert extra['event_type'] == "Test"
        assert extra['user_id'] == 1
        assert extra['document_id'] == 2
        assert extra['file_id'] == 3
        assert extra['custom'] == "value"
    
    def test_log_event_with_different_log_levels(self, mock_logger):
        """Test that log_event works with different log levels."""
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            log_event(mock_logger, level, f"Test {level}")
            
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == level
    
    def test_log_event_without_optional_fields(self, mock_logger):
        """Test that log_event works without optional fields."""
        log_event(mock_logger, logging.INFO, "Test")
        
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        assert 'event_type' not in extra
        assert 'user_id' not in extra


class TestLogFunctionCall:
    """Test cases for log_function_call function."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=logging.Logger)
    
    def test_log_function_call_logs_function_name(self, mock_logger):
        """Test that log_function_call logs function name."""
        log_function_call(mock_logger, "test_function")
        
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        assert "test_function" in call_args[0][0]
    
    def test_log_function_call_includes_parameters(self, mock_logger):
        """Test that log_function_call includes parameters."""
        log_function_call(mock_logger, "test_function", param1="value1", param2="value2")
        
        call_args = mock_logger.debug.call_args
        assert "param1=value1" in call_args[0][0] or "param2=value2" in call_args[0][0]
    
    def test_log_function_call_excludes_db_parameter(self, mock_logger):
        """Test that log_function_call excludes db parameter."""
        log_function_call(mock_logger, "test_function", db="excluded", param1="value1")
        
        call_args = mock_logger.debug.call_args
        assert "db=" not in call_args[0][0]
        assert "param1=value1" in call_args[0][0]
    
    def test_log_function_call_includes_extra(self, mock_logger):
        """Test that log_function_call includes extra data."""
        log_function_call(mock_logger, "test_function", param1="value1")
        
        call_args = mock_logger.debug.call_args
        assert call_args[1]['extra']['param1'] == "value1"


class TestLogPerformance:
    """Test cases for log_performance function."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=logging.Logger)
    
    def test_log_performance_logs_operation(self, mock_logger):
        """Test that log_performance logs operation."""
        log_performance(mock_logger, "test_operation", 100.5)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "test_operation" in call_args[0][0]
    
    def test_log_performance_includes_duration(self, mock_logger):
        """Test that log_performance includes duration."""
        log_performance(mock_logger, "test_operation", 100.5)
        
        call_args = mock_logger.info.call_args
        assert "100.50" in call_args[0][0] or "100.5" in call_args[0][0]
    
    def test_log_performance_includes_duration_in_extra(self, mock_logger):
        """Test that log_performance includes duration in extra."""
        log_performance(mock_logger, "test_operation", 100.5)
        
        call_args = mock_logger.info.call_args
        assert call_args[1]['extra']['duration_ms'] == 100.5
    
    def test_log_performance_includes_additional_context(self, mock_logger):
        """Test that log_performance includes additional context."""
        log_performance(mock_logger, "test_operation", 100.5, user_id=1)
        
        call_args = mock_logger.info.call_args
        assert call_args[1]['extra']['user_id'] == 1


class TestLogErrorWithContext:
    """Test cases for log_error_with_context function."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=logging.Logger)
    
    def test_log_error_with_context_logs_error(self, mock_logger):
        """Test that log_error_with_context logs error."""
        error = ValueError("Test error")
        log_error_with_context(mock_logger, error)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "ValueError" in call_args[0][0]
        assert "Test error" in call_args[0][0]
    
    def test_log_error_with_context_includes_exc_info(self, mock_logger):
        """Test that log_error_with_context includes exc_info."""
        error = ValueError("Test error")
        log_error_with_context(mock_logger, error)
        
        call_args = mock_logger.error.call_args
        assert call_args[1]['exc_info'] is True
    
    def test_log_error_with_context_includes_context(self, mock_logger):
        """Test that log_error_with_context includes context."""
        error = ValueError("Test error")
        context = {"user_id": 1, "operation": "test"}
        log_error_with_context(mock_logger, error, context)
        
        call_args = mock_logger.error.call_args
        assert call_args[1]['extra']['user_id'] == 1
        assert call_args[1]['extra']['operation'] == "test"
    
    def test_log_error_with_context_without_context(self, mock_logger):
        """Test that log_error_with_context works without context."""
        error = ValueError("Test error")
        log_error_with_context(mock_logger, error)
        
        call_args = mock_logger.error.call_args
        assert call_args[1].get('extra', {}) == {}


class TestTimedOperation:
    """Test cases for timed_operation decorator."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=logging.Logger)
    
    def test_timed_operation_decorates_sync_function(self):
        """Test that timed_operation decorates sync function."""
        @timed_operation("test_operation")
        def test_func():
            return "result"
        
        with patch('app.utils.logger.get_logger', return_value=Mock()):
            result = test_func()
            assert result == "result"
    
    def test_timed_operation_logs_performance(self):
        """Test that timed_operation logs performance."""
        @timed_operation("test_operation")
        def test_func():
            return "result"
        
        mock_logger = Mock()
        with patch('app.utils.logger.get_logger', return_value=mock_logger):
            test_func()
            
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "test_operation" in call_args[0][0]
    
    def test_timed_operation_handles_exceptions(self):
        """Test that timed_operation handles exceptions."""
        @timed_operation("test_operation")
        def test_func():
            raise ValueError("Test error")
        
        mock_logger = Mock()
        with patch('app.utils.logger.get_logger', return_value=mock_logger):
            with pytest.raises(ValueError):
                test_func()
            
            mock_logger.error.assert_called()
    
    def test_timed_operation_decorates_async_function(self):
        """Test that timed_operation decorates async function."""
        @timed_operation("test_operation")
        async def test_func():
            return "result"
        
        import asyncio
        mock_logger = Mock()
        with patch('app.utils.logger.get_logger', return_value=mock_logger):
            result = asyncio.run(test_func())
            assert result == "result"
    
    def test_timed_operation_logs_performance_for_async(self):
        """Test that timed_operation logs performance for async function."""
        @timed_operation("test_operation")
        async def test_func():
            return "result"
        
        import asyncio
        mock_logger = Mock()
        with patch('app.utils.logger.get_logger', return_value=mock_logger):
            asyncio.run(test_func())
            
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "test_operation" in call_args[0][0]

