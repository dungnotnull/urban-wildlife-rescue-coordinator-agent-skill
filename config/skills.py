"""
skills — Flexible skill architecture for urban-wildlife-rescue-coordinator.

This module provides:
- Dynamic skill loading and registration
- Chain-of-thought routing for skill selection
- Modular skill-registry pattern
- Skill dependency resolution
- Execution orchestration with hooks integration

Supports multiple skill patterns:
- Static skill chains (main orchestrator)
- Dynamic skill resolution (pattern matching)
- Chain-of-thought routing (multi-step reasoning)
- Specialized sub-agents (domain-specific skills)
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from . import Config, hooks
from .hooks import HookContext, HookEvent, get_hooks

__all__ = [
    "Skill",
    "SkillRegistry",
    "SkillInput",
    "SkillOutput",
    "SkillResult",
    "SkillRouter",
    "ChainOfThoughtRouter",
    "PatternMatchRouter",
    "get_skill_registry",
]

logger = logging.getLogger(__name__)


class SkillType(str, Enum):
    """Types of skills in the system."""

    MAIN = "main"  # Primary orchestrator skills
    SUB = "sub"  # Specialized sub-skills
    ADVISOR = "advisor"  # Analysis and synthesis skills
    COLLECTOR = "collector"  # Data gathering skills
    ANALYZER = "analyzer"  # Domain analysis skills
    UPDATER = "updater"  # Knowledge update skills
    UTILITY = "utility"  # General utility skills


class SkillPriority(int, Enum):
    """Skill execution priority."""

    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    DEFERRED = 0


@dataclass
class SkillInput:
    """Standardized input structure for all skills."""

    skill_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    # Language preference
    language: str = "en"

    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize input to dictionary."""
        return {
            "skill_name": self.skill_name,
            "inputs": self.inputs,
            "context": self.context,
            "options": self.options,
            "language": self.language,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillInput":
        """Create SkillInput from dictionary."""
        return cls(
            skill_name=data["skill_name"],
            inputs=data.get("inputs", {}),
            context=data.get("context", {}),
            options=data.get("options", {}),
            language=data.get("language", "en"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )


@dataclass
class SkillOutput:
    """Standardized output structure for all skills."""

    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Execution metrics
    execution_time_ms: int = 0
    tokens_used: int = 0

    # Quality gate results
    quality_checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Degradation level
    degradation_level: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize output to dictionary."""
        return {
            "success": self.success,
            "outputs": self.outputs,
            "errors": self.errors,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
            "tokens_used": self.tokens_used,
            "quality_checks": self.quality_checks,
            "degradation_level": self.degradation_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillOutput":
        """Create SkillOutput from dictionary."""
        return cls(
            success=data["success"],
            outputs=data.get("outputs", {}),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
            execution_time_ms=data.get("execution_time_ms", 0),
            tokens_used=data.get("tokens_used", 0),
            quality_checks=data.get("quality_checks", {}),
            degradation_level=data.get("degradation_level", 0),
        )


@dataclass
class SkillMetadata:
    """Metadata for skill registration and execution."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    skill_type: SkillType = SkillType.UTILITY
    priority: SkillPriority = SkillPriority.NORMAL
    enabled: bool = True

    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    # Execution constraints
    timeout_ms: int = 120000
    max_retries: int = 2
    requires_network: bool = False

    # Resource requirements
    estimated_tokens: int = 5000
    estimated_time_ms: int = 5000

    # File metadata
    file_path: Optional[Path] = None
    file_hash: Optional[str] = None
    last_modified: Optional[datetime] = None

    # Execution stats
    total_executions: int = 0
    successful_executions: int = 0
    avg_execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "skill_type": self.skill_type.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "dependencies": self.dependencies,
            "conflicts": self.conflicts,
            "timeout_ms": self.timeout_ms,
            "max_retries": self.max_retries,
            "requires_network": self.requires_network,
            "estimated_tokens": self.estimated_tokens,
            "estimated_time_ms": self.estimated_time_ms,
            "file_path": str(self.file_path) if self.file_path else None,
            "file_hash": self.file_hash,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "avg_execution_time_ms": self.avg_execution_time_ms,
        }


class Skill(ABC):
    """
    Abstract base class for all skills in the system.

    Skills are domain-specific capabilities that can be invoked
    to accomplish specific tasks. They follow a standard lifecycle:
    registration, resolution, execution, and quality validation.
    """

    def __init__(
        self,
        metadata: SkillMetadata,
        config: Optional[Config] = None,
    ):
        self.metadata = metadata
        self.config = config
        self._execution_count = 0

    @abstractmethod
    def execute(self, inputs: SkillInput) -> SkillOutput:
        """
        Execute the skill with the given inputs.

        Args:
            inputs: Standardized skill inputs

        Returns:
            SkillOutput with execution results
        """
        raise NotImplementedError

    def validate_inputs(self, inputs: SkillInput) -> Tuple[bool, List[str]]:
        """
        Validate skill inputs before execution.

        Args:
            inputs: Inputs to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        if not inputs.inputs:
            errors.append("Input dictionary cannot be empty")

        # Check for skill-specific required fields
        # Subclasses should override this method

        return len(errors) == 0, errors

    def validate_outputs(self, outputs: SkillOutput) -> Tuple[bool, List[str]]:
        """
        Validate skill outputs after execution.

        Args:
            outputs: Outputs to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check success status
        if not outputs.success and not outputs.errors:
            errors.append("Unsuccessful execution must have error messages")

        # Check for required output fields
        # Subclasses should override this method

        return len(errors) == 0, errors

    def pre_execute(self, inputs: SkillInput) -> SkillInput:
        """
        Pre-execution hook for input transformation.

        Args:
            inputs: Original inputs

        Returns:
            Transformed inputs
        """
        # Emit pre-execution hook
        hooks_registry = get_hooks(self.config)
        context = HookContext(
            event=HookEvent.PRE_SKILL_INVOKE,
            config=self.config,
            skill_name=self.metadata.name,
            inputs=inputs.to_dict(),
        )
        result = hooks_registry.emit(HookEvent.PRE_SKILL_INVOKE, context)

        if result.should_abort:
            inputs.options["abort"] = True
            inputs.options["abort_reason"] = result.errors

        return inputs

    def post_execute(self, outputs: SkillOutput) -> SkillOutput:
        """
        Post-execution hook for output transformation.

        Args:
            outputs: Original outputs

        Returns:
            Transformed outputs
        """
        # Emit post-execution hook
        hooks_registry = get_hooks(self.config)
        context = HookContext(
            event=HookEvent.POST_SKILL_INVOKE,
            config=self.config,
            skill_name=self.metadata.name,
            outputs=outputs.to_dict(),
        )
        hooks_registry.emit(HookEvent.POST_SKILL_INVOKE, context)

        # Update execution stats
        self._execution_count += 1
        self.metadata.total_executions += 1
        if outputs.success:
            self.metadata.successful_executions += 1

        return outputs

    def __repr__(self) -> str:
        return f"Skill(name={self.metadata.name}, type={self.metadata.skill_type.value})"


class FileBasedSkill(Skill):
    """
    Skill implementation that loads execution logic from a markdown file.

    Parses the skill file frontmatter and provides workflow execution.
    """

    def __init__(
        self,
        file_path: Path,
        config: Optional[Config] = None,
    ):
        # Parse frontmatter from file
        frontmatter, content = self._parse_skill_file(file_path)

        # Create metadata from frontmatter
        metadata = SkillMetadata(
            name=frontmatter.get("name", file_path.stem),
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            skill_type=SkillType(frontmatter.get("skill_type", "utility")),
            priority=SkillPriority(frontmatter.get("priority", 50)),
            enabled=frontmatter.get("enabled", True),
            dependencies=frontmatter.get("dependencies", []),
            file_path=file_path,
            file_hash=self._compute_file_hash(file_path),
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc),
        )

        super().__init__(metadata, config)

        self.content = content
        self.frontmatter = frontmatter

    def _parse_skill_file(self, file_path: Path) -> Tuple[Dict[str, Any], str]:
        """Parse skill file to extract frontmatter and content."""
        content = file_path.read_text(encoding="utf-8")

        # Extract frontmatter between --- delimiters
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            try:
                frontmatter = self._parse_yaml_frontmatter(frontmatter_text)
            except Exception:
                frontmatter = {}
            content = content[frontmatter_match.end():]
        else:
            frontmatter = {}

        return frontmatter, content

    def _parse_yaml_frontmatter(self, text: str) -> Dict[str, Any]:
        """Simple YAML frontmatter parser."""
        data = {}
        for line in text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()
        return data

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def execute(self, inputs: SkillInput) -> SkillOutput:
        """
        Execute the file-based skill.

        For file-based skills, the actual execution is delegated
        to the runtime (Claude Code). This method provides the
        structure and hooks integration.
        """
        # Pre-execution hook
        inputs = self.pre_execute(inputs)

        # Check for abort signal
        if inputs.options.get("abort"):
            return SkillOutput(
                success=False,
                errors=[inputs.options.get("abort_reason", "Execution aborted by pre-hook")],
                metadata={"skill": self.metadata.name, "aborted": True},
            )

        # Validate inputs
        is_valid, errors = self.validate_inputs(inputs)
        if not is_valid:
            return SkillOutput(
                success=False,
                errors=errors,
                metadata={"skill": self.metadata.name, "validation_failed": True},
            )

        # The actual execution happens in the runtime
        # This is a placeholder for the output structure
        output = SkillOutput(
            success=True,
            outputs={"content": self.content},
            metadata={"skill": self.metadata.name, "file_based": True},
        )

        # Validate outputs
        is_valid, errors = self.validate_outputs(output)
        if not is_valid:
            output.success = False
            output.errors.extend(errors)

        # Post-execution hook
        output = self.post_execute(output)

        return output


class SkillRouter(ABC):
    """
    Abstract base class for skill routers.

    Routers determine which skills to execute based on
    user queries, context, and system state.
    """

    @abstractmethod
    def route(
        self,
        query: str,
        context: Dict[str, Any],
        available_skills: List[Skill],
    ) -> List[Skill]:
        """
        Determine which skills to execute for the given query.

        Args:
            query: User query or request
            context: Execution context
            available_skills: List of available skills

        Returns:
            List of skills to execute, in order
        """
        raise NotImplementedError


class ChainOfThoughtRouter(SkillRouter):
    """
    Router that uses chain-of-thought reasoning to select skills.

    This router analyzes the query, breaks it down into steps,
    and selects appropriate skills for each step.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config

    def route(
        self,
        query: str,
        context: Dict[str, Any],
        available_skills: List[Skill],
    ) -> List[Skill]:
        """
        Route using chain-of-thought analysis.

        The process:
        1. Analyze the query structure
        2. Identify key components
        3. Determine required capabilities
        4. Select skills for each component
        5. Order skills by dependency
        """
        # Analyze query structure
        components = self._analyze_query(query)

        # Score each skill for each component
        scored_skills = self._score_skills(components, available_skills)

        # Select top skills per component
        selected = self._select_skills(scored_skills)

        # Order by dependency
        ordered = self._order_by_dependency(selected)

        return ordered

    def _analyze_query(self, query: str) -> List[Dict[str, Any]]:
        """Analyze query to identify components."""
        components = []

        # Detect language
        if any(c in query for c in "àáảãạăâèéêìíòóôơùúưý"):
            components.append({"type": "language", "value": "vi"})
        else:
            components.append({"type": "language", "value": "en"})

        # Detect domain keywords
        domain_keywords = {
            "wildlife": "wildlife_rescue",
            "rescue": "wildlife_rescue",
            "animal": "wildlife_rescue",
            "injured": "triage",
            "capture": "capture_handling",
            "rehabilitate": "rehabilitation",
            "release": "release_criteria",
        }

        for keyword, domain in domain_keywords.items():
            if keyword.lower() in query.lower():
                components.append({"type": "domain", "value": domain})
                break

        # Detect action type
        action_keywords = {
            "analyze": "analysis",
            "coordinate": "coordination",
            "recommend": "recommendation",
            "assess": "assessment",
        }

        for keyword, action in action_keywords.items():
            if keyword.lower() in query.lower():
                components.append({"type": "action", "value": action})
                break

        return components

    def _score_skills(
        self,
        components: List[Dict[str, Any]],
        available_skills: List[Skill],
    ) -> List[Tuple[Skill, float]]:
        """Score skills based on component relevance."""
        scored = []

        for skill in available_skills:
            score = 0.0

            # Description relevance (40%)
            for component in components:
                if component["value"] in skill.metadata.description.lower():
                    score += 0.4

            # Name relevance (30%)
            for component in components:
                if component["value"] in skill.metadata.name.lower():
                    score += 0.3

            # Priority (20%)
            score += (skill.metadata.priority.value / 100) * 0.2

            # Success rate (10%)
            if skill.metadata.total_executions > 0:
                success_rate = skill.metadata.successful_executions / skill.metadata.total_executions
                score += success_rate * 0.1

            scored.append((skill, score))

        return scored

    def _select_skills(
        self,
        scored_skills: List[Tuple[Skill, float]],
        threshold: float = 0.3,
    ) -> List[Skill]:
        """Select skills above threshold."""
        return [skill for skill, score in scored_skills if score >= threshold]

    def _order_by_dependency(self, skills: List[Skill]) -> List[Skill]:
        """Order skills by dependency constraints."""
        ordered = []
        remaining = skills.copy()

        while remaining:
            # Find skills with no unsatisfied dependencies
            ready = []
            for skill in remaining:
                deps = skill.metadata.dependencies
                if all(d in [s.metadata.name for s in ordered] for d in deps):
                    ready.append(skill)

            if not ready:
                # Circular dependency or missing dependency
                # Add remaining skills in priority order
                ready = sorted(remaining, key=lambda s: s.metadata.priority.value, reverse=True)

            # Add highest priority ready skill
            ready.sort(key=lambda s: s.metadata.priority.value, reverse=True)
            ordered.append(ready[0])
            remaining.remove(ready[0])

        return ordered


class PatternMatchRouter(SkillRouter):
    """
    Router that uses pattern matching to select skills.

    This router matches query patterns against skill descriptions
    and selects the best matching skills.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config

    def route(
        self,
        query: str,
        context: Dict[str, Any],
        available_skills: List[Skill],
    ) -> List[Skill]:
        """Route using pattern matching."""
        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Score skills by keyword match
        scored = []
        for skill in available_skills:
            score = self._calculate_match_score(keywords, skill)
            if score > 0:
                scored.append((skill, score))

        # Sort by score and return top skills
        scored.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, _ in scored[:5]]

    def _extract_keywords(self, query: str) -> Set[str]:
        """Extract keywords from query."""
        # Tokenize and filter
        tokens = re.findall(r"\b\w+\b", query.lower())

        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = {t for t in tokens if t not in stop_words and len(t) > 2}

        return keywords

    def _calculate_match_score(self, keywords: Set[str], skill: Skill) -> float:
        """Calculate match score between keywords and skill."""
        # Check description
        desc_words = set(re.findall(r"\b\w+\b", skill.metadata.description.lower()))
        desc_match = len(keywords & desc_words) / max(len(keywords), 1)

        # Check name
        name_words = set(re.findall(r"\b\w+\b", skill.metadata.name.lower()))
        name_match = len(keywords & name_words) / max(len(keywords), 1)

        # Combine scores
        return desc_match * 0.7 + name_match * 0.3


class SkillRegistry:
    """
    Central registry for all skills in the system.

    Manages skill registration, resolution, and execution.
    """

    _instance: Optional["SkillRegistry"] = None

    def __new__(cls, config: Optional[Config] = None) -> "SkillRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, Skill] = {}
            cls._instance._config = config
        return cls._instance

    def __init__(self, config: Optional[Config] = None):
        """Initialize the skill registry (singleton pattern)."""
        if config is not None:
            self._config = config

    def register(self, skill: Skill) -> None:
        """Register a skill with the registry."""
        self._skills[skill.metadata.name] = skill
        logger.info(f"Registered skill: {skill.metadata.name}")

    def register_from_directory(self, directory: Path) -> int:
        """Register all skills from a directory."""
        count = 0
        for skill_file in directory.glob("*.md"):
            try:
                skill = FileBasedSkill(skill_file, self._config)
                self.register(skill)
                count += 1
            except Exception as e:
                logger.error(f"Failed to register skill from {skill_file}: {e}")

        logger.info(f"Registered {count} skills from {directory}")
        return count

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill by name."""
        if skill_name in self._skills:
            del self._skills[skill_name]
            logger.info(f"Unregistered skill: {skill_name}")
            return True
        return False

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(skill_name)

    def all_skills(self) -> Dict[str, Skill]:
        """Get all registered skills."""
        return self._skills.copy()

    def resolve(
        self,
        query: str,
        context: Dict[str, Any],
        router: Optional[SkillRouter] = None,
    ) -> List[Skill]:
        """Resolve skills for a query."""
        available = list(self._skills.values())

        # Filter enabled skills
        available = [s for s in available if s.metadata.enabled]

        # Use router if provided
        if router:
            return router.route(query, context, available)

        # Default: use chain-of-thought router
        cot_router = ChainOfThoughtRouter(self._config)
        return cot_router.route(query, context, available)

    def execute(
        self,
        skill_name: str,
        inputs: Union[SkillInput, Dict[str, Any]],
    ) -> SkillOutput:
        """Execute a skill by name."""
        skill = self.get_skill(skill_name)
        if not skill:
            return SkillOutput(
                success=False,
                errors=[f"Skill not found: {skill_name}"],
                metadata={"skill": skill_name, "not_found": True},
            )

        # Convert dict to SkillInput if needed
        if isinstance(inputs, dict):
            inputs = SkillInput(skill_name=skill_name, inputs=inputs)

        try:
            return skill.execute(inputs)
        except Exception as e:
            logger.error(f"Skill execution failed: {e}", exc_info=e)

            # Emit error hook
            hooks_registry = get_hooks(self._config)
            hooks_registry.emit(
                HookEvent.ON_ERROR,
                HookContext(
                    event=HookEvent.ON_ERROR,
                    config=self._config,
                    skill_name=skill_name,
                    errors=[e],
                ),
            )

            return SkillOutput(
                success=False,
                errors=[str(e)],
                metadata={"skill": skill_name, "exception": True},
            )


# Global skill registry instance
_registry: Optional[SkillRegistry] = None


def get_skill_registry(config: Optional[Config] = None) -> SkillRegistry:
    """Get the global skill registry instance."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry(config)
    return _registry
