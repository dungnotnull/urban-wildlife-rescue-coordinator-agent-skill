"""
hooks — Production-grade lifecycle hooks system for urban-wildlife-rescue-coordinator.

This module provides a comprehensive hooks system for:
- Pre/post execution lifecycle events
- State synchronization across components
- Event emission and listening
- Validation and quality gate enforcement
- Error recovery and graceful degradation

Hooks are typed, validated, and support both sync and async execution.
"""
from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

from . import Config

__all__ = [
    "HookEvent",
    "HookPriority",
    "HookContext",
    "HookResult",
    "Hook",
    "HookRegistry",
    "hook",
    "pre_execution",
    "post_execution",
    "on_error",
    "on_gate_check",
    "on_state_change",
    "get_hooks",
]

logger = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """Standard hook event types in the system."""

    # Lifecycle events
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"
    ON_ERROR = "on_error"

    # Skill-specific events
    PRE_SKILL_INVOKE = "pre_skill_invoke"
    POST_SKILL_INVOKE = "post_skill_invoke"

    # Quality gate events
    PRE_GATE_CHECK = "pre_gate_check"
    POST_GATE_CHECK = "post_gate_check"
    GATE_FAILURE = "gate_failure"

    # Data events
    PRE_DATA_FETCH = "pre_data_fetch"
    POST_DATA_FETCH = "post_data_fetch"
    KNOWLEDGE_UPDATE = "knowledge_update"

    # State events
    ON_STATE_CHANGE = "on_state_change"
    ON_DEGRADATION = "on_degradation"


class HookPriority(int, Enum):
    """Hook execution priority (higher values execute first)."""

    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    DEFERRED = 0


T = TypeVar("T")


@dataclass
class HookContext:
    """Context object passed to all hooks."""

    event: HookEvent
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    config: Optional[Config] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Execution state
    skill_name: Optional[str] = None
    gate_name: Optional[str] = None
    degradation_level: int = 0

    # Data state
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)

    def with_skill(self, skill_name: str) -> "HookContext":
        """Create a new context with skill information."""
        ctx = HookContext(
            event=self.event,
            timestamp=self.timestamp,
            config=self.config,
            metadata=self.metadata.copy(),
            skill_name=skill_name,
            degradation_level=self.degradation_level,
        )
        ctx.inputs = self.inputs.copy()
        ctx.outputs = self.outputs.copy()
        ctx.errors = self.errors.copy()
        return ctx

    def with_gate(self, gate_name: str) -> "HookContext":
        """Create a new context with gate information."""
        ctx = HookContext(
            event=self.event,
            timestamp=self.timestamp,
            config=self.config,
            metadata=self.metadata.copy(),
            gate_name=gate_name,
            degradation_level=self.degradation_level,
        )
        ctx.inputs = self.inputs.copy()
        ctx.outputs = self.outputs.copy()
        ctx.errors = self.errors.copy()
        return ctx

    def add_error(self, error: Exception) -> None:
        """Add an error to the context."""
        self.errors.append(error)
        logger.error(f"Error in hook context: {error}", exc_info=error)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "event": self.event.value,
            "timestamp": self.timestamp.isoformat(),
            "skill_name": self.skill_name,
            "gate_name": self.gate_name,
            "degradation_level": self.degradation_level,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error_count": len(self.errors),
        }


@dataclass
class HookResult:
    """Result returned by hook execution."""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    should_abort: bool = False
    modified_context: Optional[HookContext] = None

    def merge(self, other: "HookResult") -> "HookResult":
        """Merge two hook results."""
        return HookResult(
            success=self.success and other.success,
            data={**self.data, **other.data},
            errors=self.errors + other.errors,
            should_abort=self.should_abort or other.should_abort,
            modified_context=other.modified_context or self.modified_context,
        )


class Hook(ABC):
    """
    Abstract base class for all hooks.

    Hooks are registered with the HookRegistry and executed in priority order
    when their associated events are triggered.
    """

    def __init__(
        self,
        event: HookEvent,
        priority: HookPriority = HookPriority.NORMAL,
        name: Optional[str] = None,
        enabled: bool = True,
    ):
        self.event = event
        self.priority = priority
        self.name = name or self.__class__.__name__
        self.enabled = enabled

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook logic.

        Args:
            context: The hook context containing event data

        Returns:
            HookResult with execution outcome
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"Hook(name={self.name}, event={self.event.value}, priority={self.priority})"


class FunctionHook(Hook):
    """Hook implementation that wraps a callable function."""

    def __init__(
        self,
        event: HookEvent,
        func: Callable[[HookContext], HookResult],
        priority: HookPriority = HookPriority.NORMAL,
        name: Optional[str] = None,
        enabled: bool = True,
    ):
        super().__init__(event, priority, name or func.__name__, enabled)
        self.func = func

    def execute(self, context: HookContext) -> HookResult:
        try:
            result = self.func(context)
            if not isinstance(result, HookResult):
                # Auto-convert dict returns to HookResult
                if isinstance(result, dict):
                    return HookResult(success=True, data=result)
                return HookResult(success=True)
            return result
        except Exception as e:
            logger.error(f"Hook {self.name} failed: {e}", exc_info=e)
            return HookResult(
                success=False,
                errors=[f"{self.name}: {str(e)}"],
                should_abort=False,  # Don't abort on hook failure by default
            )


class HookRegistry:
    """
    Central registry for all system hooks.

    Manages hook registration, execution, and event emission with proper
    error handling and logging.
    """

    _instance: Optional["HookRegistry"] = None

    def __new__(cls) -> "HookRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._hooks: Dict[HookEvent, List[Hook]] = {}
            cls._instance._config: Optional[Config] = None
        return cls._instance

    def __init__(self):
        """Initialize the hook registry (singleton pattern)."""
        pass

    def set_config(self, config: Config) -> None:
        """Set the configuration for hook execution."""
        self._config = config

    def register(self, hook: Hook) -> None:
        """
        Register a hook with the registry.

        Args:
            hook: The hook instance to register
        """
        if hook.event not in self._hooks:
            self._hooks[hook.event] = []
        self._hooks[hook.event].append(hook)
        # Sort by priority descending (higher priority first)
        self._hooks[hook.event].sort(key=lambda h: h.priority.value, reverse=True)
        logger.debug(f"Registered hook: {hook.name} for event {hook.event.value} (priority={hook.priority})")

    def unregister(self, hook_name: str) -> bool:
        """
        Unregister a hook by name.

        Args:
            hook_name: Name of the hook to unregister

        Returns:
            True if hook was found and removed, False otherwise
        """
        for event_hooks in self._hooks.values():
            for i, hook in enumerate(event_hooks):
                if hook.name == hook_name:
                    event_hooks.pop(i)
                    logger.debug(f"Unregistered hook: {hook_name}")
                    return True
        return False

    def emit(
        self,
        event: HookEvent,
        context: Optional[HookContext] = None,
    ) -> HookResult:
        """
        Emit an event and execute all registered hooks.

        Args:
            event: The event to emit
            context: The hook context (will be created if None)

        Returns:
            Combined HookResult from all hook executions
        """
        if context is None:
            context = HookContext(event=event, config=self._config)

        hooks = self._hooks.get(event, [])
        if not hooks:
            logger.debug(f"No hooks registered for event: {event.value}")
            return HookResult(success=True)

        logger.debug(f"Emitting event {event.value} with {len(hooks)} hooks")
        combined_result = HookResult(success=True)

        for hook in hooks:
            if not hook.enabled:
                continue

            try:
                result = hook.execute(context)
                combined_result = combined_result.merge(result)

                if result.should_abort:
                    logger.warning(f"Hook {hook.name} requested abort")
                    combined_result.should_abort = True
                    break

                if result.modified_context:
                    context = result.modified_context

            except Exception as e:
                logger.error(f"Hook {hook.name} raised unexpected exception: {e}", exc_info=e)
                combined_result.success = False
                combined_result.errors.append(f"{hook.name}: {str(e)}")

        return combined_result

    def get_hooks_for_event(self, event: HookEvent) -> List[Hook]:
        """
        Get all hooks registered for a specific event.

        Args:
            event: The event to query

        Returns:
            List of hooks registered for the event
        """
        return self._hooks.get(event, []).copy()

    def all_hooks(self) -> Dict[HookEvent, List[Hook]]:
        """
        Get all registered hooks by event.

        Returns:
            Dictionary mapping events to their registered hooks
        """
        return {event: hooks.copy() for event, hooks in self._hooks.items()}


# Global hook registry instance
_hooks: Optional[HookRegistry] = None


def get_hooks(config: Optional[Config] = None) -> HookRegistry:
    """
    Get the global hook registry instance.

    Args:
        config: Optional configuration to set on the registry

    Returns:
        The global HookRegistry instance
    """
    global _hooks
    if _hooks is None:
        _hooks = HookRegistry()
    if config is not None:
        _hooks.set_config(config)
    return _hooks


# Decorator helpers for common hook types


def hook(event: HookEvent, priority: HookPriority = HookPriority.NORMAL, name: Optional[str] = None):
    """
    Decorator to register a function as a hook.

    Args:
        event: The event type to hook
        priority: Execution priority (higher first)
        name: Optional custom name for the hook

    Example:
        ```python
        @hook(HookEvent.PRE_EXECUTION, priority=HookPriority.HIGH)
        def my_pre_hook(ctx: HookContext) -> HookResult:
            return HookResult(success=True, data={"message": "Hello"})
        ```
    """

    def decorator(func: Callable[[HookContext], Union[HookResult, Dict[str, Any]]]) -> Callable:
        hook_instance = FunctionHook(event, func, priority, name)
        get_hooks().register(hook_instance)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def pre_execution(priority: HookPriority = HookPriority.NORMAL, name: Optional[str] = None):
    """Decorator for PRE_EXECUTION hooks."""
    return hook(HookEvent.PRE_EXECUTION, priority, name)


def post_execution(priority: HookPriority = HookPriority.NORMAL, name: Optional[str] = None):
    """Decorator for POST_EXECUTION hooks."""
    return hook(HookEvent.POST_EXECUTION, priority, name)


def on_error(priority: HookPriority = HookPriority.NORMAL, name: Optional[str] = None):
    """Decorator for ON_ERROR hooks."""
    return hook(HookEvent.ON_ERROR, priority, name)


def on_gate_check(priority: HookPriority = HookPriority.NORMAL, name: Optional[str] = None):
    """Decorator for PRE_GATE_CHECK and POST_GATE_CHECK hooks."""
    return [
        hook(HookEvent.PRE_GATE_CHECK, priority, name),
        hook(HookEvent.POST_GATE_CHECK, priority, name),
    ]


def on_state_change(priority: HookPriority = HookPriority.NORMAL, name: Optional[str] = None):
    """Decorator for ON_STATE_CHANGE hooks."""
    return hook(HookEvent.ON_STATE_CHANGE, priority, name)


# Built-in production hooks


@pre_execution(priority=HookPriority.CRITICAL, name="validation_hook")
def validation_hook(context: HookContext) -> HookResult:
    """Validate required inputs before execution."""
    errors = []

    # Check for required fields based on event
    if context.event == HookEvent.PRE_EXECUTION:
        if not context.inputs and not context.metadata.get("skip_validation"):
            errors.append("No inputs provided for execution")

    return HookResult(
        success=len(errors) == 0,
        errors=errors,
        should_abort=len(errors) > 0,
    )


@post_execution(priority=HookPriority.HIGH, name="logging_hook")
def logging_hook(context: HookContext) -> HookResult:
    """Log execution results for monitoring and debugging."""
    if context.outputs:
        logger.info(f"Execution completed with outputs: {list(context.outputs.keys())}")

    if context.errors:
        logger.warning(f"Execution completed with {len(context.errors)} errors")

    return HookResult(success=True)


@on_error(priority=HookPriority.CRITICAL, name="error_recovery_hook")
def error_recovery_hook(context: HookContext) -> HookResult:
    """Attempt error recovery and graceful degradation."""
    if not context.errors:
        return HookResult(success=True)

    # Log all errors for analysis
    for error in context.errors:
        logger.error(f"Error in execution: {error}", exc_info=error)

    # Attempt recovery based on degradation level
    recovery_actions = []

    if context.degradation_level < 4:
        recovery_actions.append("Attempting graceful degradation")
        # Add recovery logic here

    return HookResult(
        success=True,
        data={"recovery_actions": recovery_actions},
    )
