"""
utils.py — Production-grade shared utilities for urban-wildlife-rescue-coordinator.

This module provides:
- Hash computation and data validation
- Retry logic with exponential backoff
- Progression tracking
- Correlation ID generation
- Error handling utilities
- Performance measurement
- Context management
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import string
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

T = TypeVar("T")

# Configuration imports (will be updated to use new config module)
ROOT_DIR = Path(__file__).resolve().parent.parent
BRAIN_PATH = ROOT_DIR / "SECOND-KNOWLEDGE-BRAIN.md"
LOGS_DIR = ROOT_DIR / "logs"

LOGS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("urban-wildlife-rescue")


def setup_logging(name: str = "urban-wildlife-rescue", level: int = logging.INFO) -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(LOGS_DIR / "tools.log", encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    return log


def compute_hash(identifier: str) -> str:
    return hashlib.sha256(identifier.strip().lower().encode()).hexdigest()


def load_existing_hashes(brain_path: Optional[Path] = None) -> Set[str]:
    p = brain_path or BRAIN_PATH
    if not p.exists():
        return set()
    hashes: Set[str] = set()
    content = p.read_text(encoding="utf-8")
    for m in re.finditer(r"\*\*DOI/URL:\*\*\s*(\S+)", content):
        hashes.add(compute_hash(m.group(1)))
    return hashes


def timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def date_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def retry_with_backoff(fn, max_retries: int = 3, base_delay: float = 2.0):
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(base_delay * (2 ** attempt))
            return fn()
        except Exception as exc:
            logger.warning("Attempt %d/%d failed: %s", attempt + 1, max_retries, exc)
            if attempt >= max_retries - 1:
                raise
    return None


def load_progression(prog_path: Optional[Path] = None) -> Dict[str, Any]:
    p = prog_path or (Path(__file__).parent.parent / "progression.json")
    if not p.exists():
        return {
            "skill_id": "223",
            "skill_name": "urban-wildlife-rescue-coordinator",
            "version": "1.0.0",
            "phases": {},
            "last_updated": timestamp_now(),
        }
    return json.loads(p.read_text(encoding="utf-8"))


def save_progression(data: Dict[str, Any], prog_path: Optional[Path] = None) -> None:
    p = prog_path or (Path(__file__).parent.parent / "progression.json")
    data["last_updated"] = timestamp_now()
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_verdict(verdict: str) -> bool:
    from .config import ANALYSIS_VERDICTS

    return verdict in ANALYSIS_VERDICTS


def markdown_limitation_banner(level: int) -> str:
    return (
        "---\n"
        f"⚠️ LIMITATION NOTICE\n"
        f"This output was generated with reduced data availability (Level {level}). "
        "Cross-check with current data before acting on it. Substituted/missing sources "
        "are flagged inline.\n"
        "---\n"
    )


# =============================================================================
# Correlation ID and Tracking
# =============================================================================


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a short alphanumeric ID for non-critical tracking."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def validate_correlation_id(correlation_id: str) -> bool:
    """Validate a correlation ID format."""
    try:
        uuid.UUID(correlation_id)
        return True
    except ValueError:
        return False


# =============================================================================
# Performance and Timing
# =============================================================================


@contextmanager
def measure_time(operation_name: str) -> Generator[None, None, Dict[str, float]]:
    """
    Context manager to measure execution time.

    Yields a dictionary that will be populated with timing metrics.

    Example:
        >>> with measure_time("data_fetch") as metrics:
        ...     result = fetch_data()
        >>> print(f"Operation took {metrics['elapsed_ms']}ms")
    """
    start_time = time.time()
    start_cpu = time.process_time()
    metrics: Dict[str, float] = {}

    try:
        yield metrics
    finally:
        end_time = time.time()
        end_cpu = time.process_time()

        metrics.update({
            "elapsed_ms": (end_time - start_time) * 1000,
            "cpu_time_ms": (end_cpu - start_cpu) * 1000,
            "start_time": start_time,
            "end_time": end_time,
        })

        logger.debug(f"Performance: {operation_name}", extra={
            "operation": operation_name,
            **metrics
        })


def time_it(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with measure_time(func.__name__) as metrics:
            result = func(*args, **kwargs)
        return result
    return wrapper


# =============================================================================
# Enhanced Retry Logic
# =============================================================================


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> T:
    """
    Execute a function with retry logic and exponential backoff.

    Args:
        fn: Function to execute (should take no arguments)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter: Whether to add random jitter to delay
        on_retry: Optional callback called on each retry (attempt, exception)

    Returns:
        Result of the function execution

    Raises:
        Last exception if all retries fail

    Example:
        >>> result = retry_with_backoff(
        ...     lambda: requests.get(url),
        ...     max_retries=3,
        ...     on_retry=lambda attempt, exc: logger.warning(f"Retry {attempt}")
        ... )
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_exception = exc
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {exc}",
                extra={"attempt": attempt + 1, "max_retries": max_retries}
            )

            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                # Add jitter if requested
                if jitter:
                    delay = delay * (0.5 + random.random())

                logger.debug(f"Retrying after {delay:.2f}s delay")
                time.sleep(delay)

                # Call on_retry callback if provided
                if on_retry:
                    on_retry(attempt + 1, exc)

    # All retries failed
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed with no exception")


# =============================================================================
# Data Validation and Sanitization
# =============================================================================


def sanitize_string(text: str, max_length: int = 10000) -> str:
    """
    Sanitize a string for safe logging and storage.

    Args:
        text: Input text to sanitize
        max_length: Maximum length to return

    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return str(text)

    # Remove null bytes
    text = text.replace("\x00", "")

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "... (truncated)"

    return text


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON with default fallback.

    Args:
        text: JSON text to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


# =============================================================================
# File System Utilities
# =============================================================================


def ensure_directory(path: Path, permissions: int = 0o755) -> None:
    """
    Ensure a directory exists with proper permissions.

    Args:
        path: Directory path to create
        permissions: Unix permissions (not applicable on Windows)
    """
    path.mkdir(parents=True, exist_ok=True)
    # Note: chmod is no-op on Windows
    try:
        path.chmod(permissions)
    except (OSError, AttributeError):
        pass


def safe_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Safely write content to a file with atomic write.

    Args:
        path: File path to write to
        content: Content to write
        encoding: File encoding
    """
    # Write to temporary file first
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        temp_path.write_text(content, encoding=encoding)
        # Atomic rename
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


def atomic_json_write(path: Path, data: Any, indent: int = 2) -> None:
    """
    Atomically write JSON data to a file.

    Args:
        path: File path to write to
        data: Data to serialize and write
        indent: JSON indentation
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
    safe_write(path, content)


# =============================================================================
# Context Management
# =============================================================================


@dataclass
class ExecutionContext:
    """Context information for execution tracking."""

    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    skill_name: Optional[str] = None
    start_time: float = time.time()
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "skill_name": self.skill_name,
            "start_time": self.start_time,
            "elapsed_ms": (time.time() - self.start_time) * 1000,
            "metadata": self.metadata,
        }


@contextmanager
def execution_context(
    skill_name: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Generator[ExecutionContext, None, None]:
    """
    Context manager for execution tracking.

    Args:
        skill_name: Optional skill name
        user_id: Optional user identifier
        session_id: Optional session identifier

    Example:
        >>> with execution_context(skill_name="my_skill") as ctx:
        ...     result = execute_skill()
        ...     print(f"Execution took {ctx.to_dict()['elapsed_ms']}ms")
    """
    ctx = ExecutionContext(
        correlation_id=generate_correlation_id(),
        user_id=user_id,
        session_id=session_id,
        skill_name=skill_name,
    )

    try:
        yield ctx
    finally:
        # Context is finalized when exiting the block
        pass


# =============================================================================
# Error Handling Utilities
# =============================================================================


@dataclass
class ErrorDetail:
    """Detailed error information for logging and reporting."""

    code: str
    message: str
    component: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "component": self.component,
            "context": self.context,
            "timestamp": self.timestamp,
            "iso_timestamp": datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat(),
        }


def format_exception(exc: Exception, include_traceback: bool = False) -> ErrorDetail:
    """
    Format an exception into a structured error detail.

    Args:
        exc: Exception to format
        include_traceback: Whether to include traceback in context

    Returns:
        ErrorDetail with structured information
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)
    error_code = f"{exc_type}_ERROR"

    context: Dict[str, Any] = {
        "exception_type": exc_type,
        "exception_message": exc_message,
    }

    if include_traceback:
        import traceback
        context["traceback"] = traceback.format_exc()

    return ErrorDetail(
        code=error_code,
        message=exc_message,
        context=context,
    )


class ErrorCollector:
    """Collect and aggregate errors during execution."""

    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self.errors: List[ErrorDetail] = []

    def add_error(self, error: ErrorDetail) -> None:
        """Add an error to the collector."""
        self.errors.append(error)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)

    def add_exception(self, exc: Exception, component: Optional[str] = None) -> None:
        """Add an exception as an error detail."""
        detail = format_exception(exc, include_traceback=True)
        if component:
            detail.component = component
        self.add_error(detail)

    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected errors."""
        if not self.errors:
            return {"total_errors": 0, "by_code": {}}

        by_code: Dict[str, int] = {}
        for error in self.errors:
            by_code[error.code] = by_code.get(error.code, 0) + 1

        return {
            "total_errors": len(self.errors),
            "by_code": by_code,
            "recent_errors": [e.to_dict() for e in self.errors[-5:]],
        }


# =============================================================================
# Cache Management
# =============================================================================


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: float = 3600.0):
        self.default_ttl = default_ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if not expired."""
        if key not in self.cache:
            return None

        value, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value in cache with optional TTL."""
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if expiry < current_time
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
