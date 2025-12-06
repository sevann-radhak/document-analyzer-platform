"""Utility functions for structured logging."""
import logging
from typing import Optional, Any, Dict
from functools import wraps
import time

from app.core.logging_config import get_logger


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
    file_id: Optional[int] = None,
    **kwargs: Any
) -> None:
    """
    Log an event with structured data.
    
    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        event_type: Type of event (optional)
        user_id: User ID associated with the event (optional)
        document_id: Document ID (optional)
        file_id: File ID (optional)
        **kwargs: Additional context data
    """
    extra: Dict[str, Any] = {}
    
    if event_type:
        extra["event_type"] = event_type
    if user_id:
        extra["user_id"] = user_id
    if document_id:
        extra["document_id"] = document_id
    if file_id:
        extra["file_id"] = file_id
    
    extra.update(kwargs)
    
    logger.log(level, message, extra=extra)


def log_function_call(
    logger: logging.Logger,
    function_name: str,
    **kwargs: Any
) -> None:
    """
    Log a function call with parameters.
    
    Args:
        logger: Logger instance
        function_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items() if k != "db")
    logger.debug(f"Calling {function_name}({params})", extra=kwargs)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **kwargs: Any
) -> None:
    """
    Log performance metrics.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        **kwargs: Additional context
    """
    extra = {"duration_ms": duration_ms, **kwargs}
    logger.info(f"Performance: {operation} took {duration_ms:.2f}ms", extra=extra)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with context information.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context data
    """
    extra = context or {}
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra=extra
    )


def timed_operation(operation_name: str):
    """
    Decorator to log operation duration.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(logger, operation_name, duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_error_with_context(logger, e, {"operation": operation_name, "duration_ms": duration_ms})
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(logger, operation_name, duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_error_with_context(logger, e, {"operation": operation_name, "duration_ms": duration_ms})
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

