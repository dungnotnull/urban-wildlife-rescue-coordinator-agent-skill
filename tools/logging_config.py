"""
logging_config — Production-grade structured logging for urban-wildlife-rescue-coordinator.

This module provides:
- Structured logging with JSON formatting
- Log level management per component
- Context-aware logging with metadata
- Performance metrics tracking
- Error aggregation and reporting

All log entries include: timestamp, level, component, correlation_id, message, metadata
"""
from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)

from .utils import generate_correlation_id

__all__ = [
    "LogLevel",
    "LogContext",
    "StructuredLogger",
    "get_logger",
    "log_execution",
    "log_errors",
    "log_performance",
    "with_logging",
]


class LogLevel(str, Enum):
    """Log levels matching standard Python logging."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Context information for log entries."""

    component: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    skill_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "component": self.component,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "skill_name": self.skill_name,
            "metadata": self.metadata,
        }


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add context metadata if present
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        # Add any additional fields
        for key, value in record.__dict__.items():
            if key not in {"name", "msg", "args", "levelname", "levelno", "pathname",
                          "filename", "module", "exc_info", "exc_text", "stack_info",
                          "lineno", "funcName", "created", "msecs", "relativeCreated",
                          "thread", "threadName", "processName", "process", "message",
                          "asctime", "context"}:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """
    Production-grade logger with structured output.

    Provides context-aware logging with automatic correlation ID tracking,
    performance metrics, and error aggregation.
    """

    def __init__(
        self,
        name: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        log_file: Optional[Path] = None,
        enable_console: bool = True,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value if isinstance(level, LogLevel) else level))

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create formatter
        formatter = StructuredFormatter()

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_file.parent.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Correlation ID tracking
        self._correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for this logger instance."""
        self._correlation_id = correlation_id

    def get_correlation_id(self) -> str:
        """Get the current correlation ID, generating one if needed."""
        if self._correlation_id is None:
            self._correlation_id = generate_correlation_id()
        return self._correlation_id

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs,
    ) -> None:
        """Internal logging method with context support."""
        # Create log record with extra context
        extra = {"context": context.to_dict() if context else {}} if context else {}

        # Add correlation ID if set
        if self._correlation_id:
            if "context" not in extra:
                extra["context"] = {}
            extra["context"]["correlation_id"] = self._correlation_id

        # Add any additional fields
        extra.update(kwargs)

        # Log the message
        log_func = getattr(self.logger, level.value.lower())
        log_func(message, extra=extra)

    def debug(self, message: str, context: Optional[LogContext] = None, **kwargs) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context, **kwargs)

    def info(self, message: str, context: Optional[LogContext] = None, **kwargs) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, context, **kwargs)

    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context, **kwargs)

    def error(
        self,
        message: str,
        context: Optional[LogContext] = None,
        exc_info: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """Log error message with optional exception info."""
        if exc_info:
            kwargs["exc_info"] = exc_info
        self._log(LogLevel.ERROR, message, context, **kwargs)

    def critical(
        self,
        message: str,
        context: Optional[LogContext] = None,
        exc_info: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """Log critical message with optional exception info."""
        if exc_info:
            kwargs["exc_info"] = exc_info
        self._log(LogLevel.CRITICAL, message, context, **kwargs)


class LoggerManager:
    """Manager for all loggers in the system."""

    _instance: Optional["LoggerManager"] = None
    _loggers: Dict[str, StructuredLogger] = {}

    def __new__(cls) -> "LoggerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_logger(
        name: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        log_file: Optional[Path] = None,
        enable_console: bool = True,
    ) -> StructuredLogger:
        """Get or create a logger with the given configuration."""
        if name not in LoggerManager._loggers:
            LoggerManager._loggers[name] = StructuredLogger(
                name=name,
                level=level,
                log_file=log_file,
                enable_console=enable_console,
            )
        return LoggerManager._loggers[name]


def get_logger(
    name: str,
    level: Union[LogLevel, str] = LogLevel.INFO,
    log_file: Optional[Path] = None,
) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically component name)
        level: Log level
        log_file: Optional file to write logs to

    Returns:
        StructuredLogger instance

    Example:
        >>> logger = get_logger("my_component", LogLevel.INFO)
        >>> logger.info("Processing started", context=LogContext(component="my_component"))
    """
    return LoggerManager.get_logger(name, level, log_file)


# Decorators for automatic logging


@contextmanager
def log_execution(
    logger: StructuredLogger,
    operation: str,
    context: Optional[LogContext] = None,
):
    """
    Context manager for logging execution performance.

    Args:
        logger: Logger instance
        operation: Operation description
        context: Optional log context

    Example:
        >>> with log_execution(logger, "data_fetch", context):
        ...     result = fetch_data()
    """
    start_time = time.time()
    correlation_id = logger.get_correlation_id()

    logger.info(f"Starting: {operation}", context=context)

    try:
        yield
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Completed: {operation}",
            context=context,
            extra={
                "operation": operation,
                "elapsed_ms": elapsed_ms,
                "correlation_id": correlation_id,
            },
        )
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Failed: {operation}",
            context=context,
            exc_info=e,
            extra={
                "operation": operation,
                "elapsed_ms": elapsed_ms,
                "correlation_id": correlation_id,
            },
        )
        raise


def log_errors(
    logger: StructuredLogger,
    context: Optional[LogContext] = None,
    reraise: bool = True,
):
    """
    Decorator for automatic error logging.

    Args:
        logger: Logger instance
        context: Optional log context
        reraise: Whether to re-raise the exception

    Example:
        >>> @log_errors(logger, context=LogContext(component="my_component"))
        ... def risky_operation():
        ...     ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}",
                    context=context,
                    exc_info=e,
                    extra={"function": func.__name__},
                )
                if reraise:
                    raise
                return None

        return wrapper

    return decorator


def log_performance(
    logger: StructuredLogger,
    context: Optional[LogContext] = None,
):
    """
    Decorator for logging function performance metrics.

    Args:
        logger: Logger instance
        context: Optional log context

    Example:
        >>> @log_performance(logger, context=LogContext(component="my_component"))
        ... def expensive_operation():
        ...     ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_id = logger.get_correlation_id()

            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"Performance: {func.__name__}",
                    context=context,
                    extra={
                        "function": func.__name__,
                        "elapsed_ms": elapsed_ms,
                        "success": True,
                        "correlation_id": correlation_id,
                    },
                )

                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000

                logger.error(
                    f"Performance: {func.__name__}",
                    context=context,
                    exc_info=e,
                    extra={
                        "function": func.__name__,
                        "elapsed_ms": elapsed_ms,
                        "success": False,
                        "correlation_id": correlation_id,
                    },
                )
                raise

        return wrapper

    return decorator


def with_logging(
    logger: Optional[StructuredLogger] = None,
    log_name: str = "default",
    log_level: LogLevel = LogLevel.INFO,
):
    """
    Decorator to add logging to a function automatically.

    Args:
        logger: Optional logger instance (will create if None)
        log_name: Name for logger if creating new one
        log_level: Log level for new logger

    Example:
        >>> @with_logging(log_name="my_component")
        ... def my_function(x, y):
        ...     return x + y
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger

            if logger is None:
                logger = get_logger(log_name, log_level)

            func_name = func.__name__
            logger.info(f"Entering {func_name}", extra={"function": func_name, "args": str(args), "kwargs": str(kwargs)})

            try:
                result = func(*args, **kwargs)
                logger.info(f"Exiting {func_name}", extra={"function": func_name, "result": str(result)[:100]})
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}", exc_info=e, extra={"function": func_name})
                raise

        return wrapper

    return decorator


class PerformanceTracker:
    """Track performance metrics across operations."""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.metrics: Dict[str, List[float]] = {}

    def record(self, operation: str, duration_ms: float) -> None:
        """Record a performance metric."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration_ms)

    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}

        durations = self.metrics[operation]
        return {
            "count": len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "avg_ms": sum(durations) / len(durations),
            "total_ms": sum(durations),
        }

    def log_summary(self, context: Optional[LogContext] = None) -> None:
        """Log a summary of all tracked metrics."""
        for operation, durations in self.metrics.items():
            stats = self.get_stats(operation)
            self.logger.info(
                f"Performance summary: {operation}",
                context=context,
                extra={"operation": operation, **stats},
            )


# Initialize default loggers for system components


def initialize_system_logging(
    log_dir: Path,
    level: Union[LogLevel, str] = LogLevel.INFO,
) -> Dict[str, StructuredLogger]:
    """
    Initialize loggers for all system components.

    Args:
        log_dir: Directory to store log files
        level: Log level for all loggers

    Returns:
        Dictionary of component name to logger
    """
    log_dir.mkdir(exist_ok=True)

    loggers = {}

    # Core component loggers
    components = [
        "skill_registry",
        "knowledge_updater",
        "gate_checker",
        "hooks",
        "main",
    ]

    for component in components:
        log_file = log_dir / f"{component}.log"
        loggers[component] = get_logger(component, level, log_file)

    return loggers
