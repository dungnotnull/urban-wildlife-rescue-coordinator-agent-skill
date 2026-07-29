"""
config — Type-safe configuration management for urban-wildlife-rescue-coordinator.

This module provides a hierarchical, validated configuration system with:
- Environment variable resolution with sensible defaults
- Type validation and coercion
- Feature flag management
- LLM parameter configuration
- System-wide settings with schema validation

All configuration is centralized here to enable runtime reconfiguration and testing.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from . import gates, hooks, settings, skills

__all__ = [
    "Config",
    "Environment",
    "LLMConfig",
    "FeatureFlags",
    "SourceConfig",
    "GateConfig",
    "get_config",
    "reload_config",
    "hooks",
    "skills",
    "gates",
]

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Runtime environment modes with different safety levels."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def from_env(cls) -> "Environment":
        """Detect environment from ENV_VAR or default to development."""
        env = os.getenv("UWRC_ENVIRONMENT", "development").lower()
        try:
            return cls(env)
        except ValueError:
            logger.warning(f"Invalid environment '{env}', defaulting to development")
            return cls.DEVELOPMENT

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self == Environment.DEVELOPMENT


@dataclass(frozen=True)
class LLMConfig:
    """LLM model parameters with production-grade defaults."""

    model: str = "claude-sonnet-4-6"
    temperature: float = 0.3
    max_tokens: int = 8192
    timeout_ms: int = 120000
    max_retries: int = 3
    retry_delay_ms: int = 1000
    enable_caching: bool = True
    enable_thinking: bool = False
    top_p: float = 0.95
    top_k: int = 0

    def validate(self) -> None:
        """Validate LLM configuration parameters."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError(f"top_p must be between 0 and 1, got {self.top_p}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        if self.timeout_ms < 1000:
            raise ValueError(f"timeout_ms must be at least 1000, got {self.timeout_ms}")


@dataclass(frozen=True)
class FeatureFlags:
    """Feature flag configuration for runtime behavior control."""

    enable_knowledge_crawl: bool = True
    enable_real_time_search: bool = True
    enable_multilingual: bool = True
    enable_auto_fix: bool = True
    enable_graceful_degradation: bool = True
    strict_mode: bool = False
    experimental_features: Set[str] = field(default_factory=set)
    disabled_skills: Set[str] = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """Create feature flags from environment variables."""
        experimental = set(os.getenv("UWRC_EXPERIMENTAL_FEATURES", "").split(",")) if os.getenv("UWRC_EXPERIMENTAL_FEATURES") else set()
        disabled = set(os.getenv("UWRC_DISABLED_SKILLS", "").split(",")) if os.getenv("UWRC_DISABLED_SKILLS") else set()
        return cls(
            enable_knowledge_crawl = os.getenv("UWRC_ENABLE_KNOWLEDGE_CRAWL", "true").lower() == "true",
            enable_real_time_search = os.getenv("UWRC_ENABLE_REAL_TIME_SEARCH", "true").lower() == "true",
            enable_multilingual = os.getenv("UWRC_ENABLE_MULTILINGUAL", "true").lower() == "true",
            enable_auto_fix = os.getenv("UWRC_ENABLE_AUTO_FIX", "true").lower() == "true",
            enable_graceful_degradation = os.getenv("UWRC_ENABLE_GRACEFUL_DEGRADATION", "true").lower() == "true",
            strict_mode = os.getenv("UWRC_STRICT_MODE", "false").lower() == "true",
            experimental_features = experimental,
            disabled_skills = disabled,
        )


@dataclass(frozen=True)
class SourceConfig:
    """Configuration for domain and academic data sources."""

    domain_authoritative_sources: List[str] = field(default_factory=list)
    academic_sources: List[str] = field(default_factory=list)
    arxiv_categories: List[str] = field(default_factory=lambda: ["q-bio.QM", "q-bio.PE", "stat.AP"])
    rss_feeds: List[str] = field(default_factory=list)
    request_timeout_seconds: int = 30
    max_retries: int = 3
    respect_rate_limit_wait_seconds: float = 1.0
    max_results_per_source: int = 10
    recency_window_days: int = 730


@dataclass(frozen=True)
class GateConfig:
    """Quality gate configuration with enforcement levels."""

    universal_gates: List[str] = field(default_factory=lambda: ["U1", "U2", "U3", "U4", "U5", "U6"])
    domain_gates: List[str] = field(default_factory=lambda: ["G1", "G2", "G3", "G4"])
    max_retries_per_gate: int = 2
    auto_fix_enabled: bool = True
    strict_enforcement: bool = False
    gate_timeout_seconds: int = 60

    def all_gates(self) -> List[str]:
        """Return all configured gates."""
        return self.universal_gates + self.domain_gates


@dataclass(frozen=True)
class Config:
    """Root configuration container for the entire system."""

    environment: Environment = field(default_factory=Environment.from_env)
    llm: LLMConfig = field(default_factory=LLMConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags.from_env)
    sources: SourceConfig = field(default_factory=SourceConfig)
    gates: GateConfig = field(default_factory=GateConfig)

    # Project structure paths
    root_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    skills_dir: Path = field(init=False)
    tools_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    references_dir: Path = field(init=False)
    assets_dir: Path = field(init=False)
    scripts_dir: Path = field(init=False)
    tests_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    # Knowledge base configuration
    brain_path: Path = field(init=False)
    knowledge_state_path: Path = field(init=False)
    knowledge_config_path: Path = field(init=False)

    def __post_init__(self):
        """Initialize derived paths after dataclass creation."""
        root = self.root_dir
        object.__setattr__(self, "skills_dir", root / "skills")
        object.__setattr__(self, "tools_dir", root / "tools")
        object.__setattr__(self, "config_dir", root / "config")
        object.__setattr__(self, "references_dir", root / "references")
        object.__setattr__(self, "assets_dir", root / "assets")
        object.__setattr__(self, "scripts_dir", root / "scripts")
        object.__setattr__(self, "tests_dir", root / "tests")
        object.__setattr__(self, "logs_dir", root / "logs")

        object.__setattr__(self, "brain_path", root / "SECOND-KNOWLEDGE-BRAIN.md")
        object.__setattr__(self, "knowledge_state_path", root / ".knowledge_state.json")
        object.__setattr__(self, "knowledge_config_path", self.config_dir / "knowledge.json")

        # Ensure log directory exists
        self.logs_dir.mkdir(exist_ok=True)

    def validate(self) -> None:
        """Validate the entire configuration."""
        self.llm.validate()
        if not self.root_dir.exists():
            raise ValueError(f"Root directory does not exist: {self.root_dir}")
        if not self.skills_dir.exists():
            raise ValueError(f"Skills directory does not exist: {self.skills_dir}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to dictionary for inspection."""
        return {
            "environment": self.environment.value,
            "llm": {
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout_ms": self.llm.timeout_ms,
                "enable_caching": self.llm.enable_caching,
            },
            "features": {
                "enable_knowledge_crawl": self.features.enable_knowledge_crawl,
                "enable_real_time_search": self.features.enable_real_time_search,
                "enable_multilingual": self.features.enable_multilingual,
                "enable_auto_fix": self.features.enable_auto_fix,
                "strict_mode": self.features.strict_mode,
            },
            "paths": {
                "root_dir": str(self.root_dir),
                "skills_dir": str(self.skills_dir),
                "brain_path": str(self.brain_path),
            },
        }


# Global configuration singleton
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get the global configuration instance.

    Args:
        reload: If True, reload configuration from environment

    Returns:
        The current Config instance

    Example:
        >>> cfg = get_config()
        >>> print(cfg.environment.value)
        development
    """
    global _config
    if _config is None or reload:
        _config = Config()
        _config.validate()
        logger.info(f"Configuration loaded: environment={_config.environment.value}")
    return _config


def reload_config() -> Config:
    """
    Force reload the configuration from environment.

    Returns:
        The newly loaded Config instance
    """
    return get_config(reload=True)


def set_config(config: Config) -> None:
    """
    Set a custom configuration instance (for testing).

    Args:
        config: The Config instance to use
    """
    global _config
    _config = config
    logger.debug("Configuration overridden programmatically")
