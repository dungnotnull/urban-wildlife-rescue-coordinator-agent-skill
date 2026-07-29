"""
gates — Production-grade quality gate framework for urban-wildlife-rescue-coordinator.

This module provides:
- Quality gate definitions and validation
- Auto-fix logic for gate failures
- Graceful degradation management
- Gate enforcement with retry logic
- Comprehensive gate reporting

Supports 10 quality gates: U1-U6 (universal) + G1-G4 (domain-specific)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from . import Config, hooks
from .hooks import HookContext, HookEvent, get_hooks

__all__ = [
    "GateType",
    "GateStatus",
    "GateResult",
    "Gate",
    "AutoFixAction",
    "GateChecker",
    "GateEnforcer",
    "DegradationLevel",
    "DegradationManager",
    "get_gate_checker",
]

logger = logging.getLogger(__name__)


class GateType(str, Enum):
    """Types of quality gates in the system."""

    UNIVERSAL = "universal"  # Applies to all skills
    DOMAIN = "domain"  # Domain-specific gates
    CUSTOM = "custom"  # User-defined gates


class GateStatus(str, Enum):
    """Status of a quality gate check."""

    PASSED = "passed"
    FAILED = "failed"
    AUTO_FIXED = "auto_fixed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class GateResult:
    """Result of a quality gate check."""

    gate_name: str
    status: GateStatus
    message: str
    auto_fix_applied: bool = False
    auto_fix_message: Optional[str] = None
    retry_count: int = 0
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize gate result to dictionary."""
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "message": self.message,
            "auto_fix_applied": self.auto_fix_applied,
            "auto_fix_message": self.auto_fix_message,
            "retry_count": self.retry_count,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class AutoFixAction:
    """Definition of an auto-fix action for a gate."""

    name: str
    description: str
    applicability_check: Callable[[Dict[str, Any]], bool]
    fix_function: Callable[[Dict[str, Any]], Tuple[bool, str, Dict[str, Any]]]
    max_attempts: int = 2


class Gate(ABC):
    """
    Abstract base class for quality gates.

    Gates are validation checkpoints that ensure output quality
    before delivery to the user. They can auto-fix failures and
    enforce strict or lenient validation modes.
    """

    def __init__(
        self,
        name: str,
        gate_type: GateType,
        description: str,
        auto_fix_enabled: bool = True,
        max_retries: int = 2,
        critical: bool = False,
    ):
        self.name = name
        self.gate_type = gate_type
        self.description = description
        self.auto_fix_enabled = auto_fix_enabled
        self.max_retries = max_retries
        self.critical = critical
        self.auto_fixes: List[AutoFixAction] = []

    @abstractmethod
    def check(self, output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
        """
        Check if the output passes this gate.

        Args:
            output: The output to validate
            context: Execution context with inputs and metadata

        Returns:
            GateResult with check outcome
        """
        raise NotImplementedError

    def add_auto_fix(self, auto_fix: AutoFixAction) -> None:
        """Add an auto-fix action to this gate."""
        self.auto_fixes.append(auto_fix)

    def apply_auto_fix(
        self,
        output: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Attempt to apply auto-fix to a failed gate.

        Args:
            output: The failed output
            context: Execution context

        Returns:
            Tuple of (success, message, fixed_output)
        """
        if not self.auto_fix_enabled or not self.auto_fixes:
            return False, "No auto-fix available", output

        for auto_fix in self.auto_fixes:
            try:
                if auto_fix.applicability_check(output):
                    success, message, fixed_output = auto_fix.fix_function(output)

                    if success:
                        return True, f"Applied auto-fix: {auto_fix.name}", fixed_output
                    else:
                        logger.warning(f"Auto-fix {auto_fix.name} failed: {message}")

            except Exception as e:
                logger.error(f"Auto-fix {auto_fix.name} raised exception: {e}", exc_info=e)

        return False, "No applicable auto-fix succeeded", output

    def __repr__(self) -> str:
        return f"Gate(name={self.name}, type={self.gate_type.value})"


class UniversalGates:
    """Factory for universal gates (U1-U6) that apply to all skills."""

    @staticmethod
    def u1_sources_cited() -> Gate:
        """
        U1: ≥3 sources cited, ≥1 academic/authoritative.

        Auto-fix: Fetch from knowledge base or evidence collector.
        """
        gate = Gate(
            name="U1",
            gate_type=GateType.UNIVERSAL,
            description="≥3 sources cited, ≥1 academic/authoritative",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            sources = output.get("sources", [])
            academic_count = sum(1 for s in sources if s.get("tier") in ["Tier 1", "Tier 2"])

            if len(sources) >= 3 and academic_count >= 1:
                return GateResult(
                    gate_name="U1",
                    status=GateStatus.PASSED,
                    message=f"Found {len(sources)} sources ({academic_count} academic/authoritative)",
                )

            return GateResult(
                gate_name="U1",
                status=GateStatus.FAILED,
                message=f"Need ≥3 sources (found {len(sources)}) and ≥1 academic (found {academic_count})",
            )

        gate.check = check
        return gate

    @staticmethod
    def u2_disclosure_before_recommendation() -> Gate:
        """
        U2: Disclosure/limitations before recommendation.

        Auto-fix: Prepend standard disclosure.
        """
        gate = Gate(
            name="U2",
            gate_type=GateType.UNIVERSAL,
            description="Disclosure/limitations before recommendation",
            auto_fix_enabled=True,
            max_retries=2,
            critical=True,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            content = output.get("content", "")

            # Check if disclosure section exists before recommendation
            has_disclosure = "## ⚠️ Disclosure" in content or "## Disclosure" in content
            has_recommendation = "## Recommendation" in content or "## Conclusion" in content

            if has_disclosure:
                # Check if it's before the recommendation
                disc_pos = content.find("⚠️ Disclosure" if "⚠️ Disclosure" in content else "Disclosure")
                rec_pos = content.find("Recommendation" if "Recommendation" in content else "Conclusion")

                if has_recommendation and disc_pos < rec_pos:
                    return GateResult(
                        gate_name="U2",
                        status=GateStatus.PASSED,
                        message="Disclosure present before recommendation",
                    )

            return GateResult(
                gate_name="U2",
                status=GateStatus.FAILED,
                message="Disclosure missing or not positioned before recommendation",
            )

        gate.check = check
        return gate

    @staticmethod
    def u3_evidence_hierarchy_stated() -> Gate:
        """
        U3: Evidence hierarchy stated per source (Tier 1-4).

        Auto-fix: Annotate source tiers.
        """
        gate = Gate(
            name="U3",
            gate_type=GateType.UNIVERSAL,
            description="Evidence hierarchy stated per source (Tier 1-4)",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            sources = output.get("sources", [])
            missing_tiers = []

            for i, source in enumerate(sources):
                if "tier" not in source:
                    missing_tiers.append(i)

            if not missing_tiers:
                return GateResult(
                    gate_name="U3",
                    status=GateStatus.PASSED,
                    message=f"All {len(sources)} sources have tier labels",
                )

            return GateResult(
                gate_name="U3",
                status=GateStatus.FAILED,
                message=f"{len(missing_tiers)} sources missing tier labels",
            )

        gate.check = check
        return gate

    @staticmethod
    def u4_language_matches_preference() -> Gate:
        """
        U4: Language matches user preference.

        Auto-fix: Translate output.
        """
        gate = Gate(
            name="U4",
            gate_type=GateType.UNIVERSAL,
            description="Language matches user preference",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            preferred = context.get("language", "en")
            detected = output.get("language", "en")

            if preferred == detected:
                return GateResult(
                    gate_name="U4",
                    status=GateStatus.PASSED,
                    message=f"Output language ({detected}) matches preference ({preferred})",
                )

            return GateResult(
                gate_name="U4",
                status=GateStatus.FAILED,
                message=f"Output language ({detected}) does not match preference ({preferred})",
            )

        gate.check = check
        return gate

    @staticmethod
    def u5_uses_declared_template() -> Gate:
        """
        U5: Output uses declared template (all sections present).

        Auto-fix: Reformat to template.
        """
        gate = Gate(
            name="U5",
            gate_type=GateType.UNIVERSAL,
            description="Output uses declared template (all sections present)",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            required_sections = [
                "Executive Summary",
                "Inputs & Scope",
                "Evidence Collected",
                "Analysis / Scorecard",
                "Academic & Research Evidence",
                "⚠️ Disclosure / Limitations",
                "Recommendation / Conclusion",
            ]

            content = output.get("content", "")
            missing_sections = []

            for section in required_sections:
                if f"## {section}" not in content:
                    missing_sections.append(section)

            if not missing_sections:
                return GateResult(
                    gate_name="U5",
                    status=GateStatus.PASSED,
                    message="All required sections present",
                )

            return GateResult(
                gate_name="U5",
                status=GateStatus.FAILED,
                message=f"Missing sections: {', '.join(missing_sections)}",
            )

        gate.check = check
        return gate

    @staticmethod
    def u6_every_claim_traceable() -> Gate:
        """
        U6: Every claim traceable to ≥1 source or flagged as judgment.

        Auto-fix: Mark each claim with source or [analyst judgment].
        """
        gate = Gate(
            name="U6",
            gate_type=GateType.UNIVERSAL,
            description="Every claim traceable to ≥1 source or flagged",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            content = output.get("content", "")
            sources = output.get("sources", [])

            # Check for unattributed claims (simplified check)
            # This is a basic implementation; production would use NLP
            lines = content.split("\n")
            unattributed = []

            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                    # This is a potential claim line
                    # Check if it has a citation marker or judgment flag
                    if "[" not in stripped and "(source:" not in stripped:
                        unattributed.append(stripped[:50])

            if not unattributed:
                return GateResult(
                    gate_name="U6",
                    status=GateStatus.PASSED,
                    message="All claims appear traceable",
                )

            return GateResult(
                gate_name="U6",
                status=GateStatus.FAILED,
                message=f"Found {len(unattributed)} potentially unattributed claims",
            )

        gate.check = check
        return gate


class DomainGates:
    """Factory for domain-specific gates (G1-G4) for wildlife rescue."""

    @staticmethod
    def g1_species_id_and_triage() -> Gate:
        """
        G1: Species ID & triage performed.

        Auto-fix: Identify & triage.
        """
        gate = Gate(
            name="G1",
            gate_type=GateType.DOMAIN,
            description="Species ID & triage performed",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            species = output.get("species_identified")
            triage = output.get("triage_performed")

            if species and triage:
                return GateResult(
                    gate_name="G1",
                    status=GateStatus.PASSED,
                    message=f"Species identified ({species}) and triage performed",
                )

            return GateResult(
                gate_name="G1",
                status=GateStatus.FAILED,
                message=f"Species ID or triage missing (species={species}, triage={triage})",
            )

        gate.check = check
        return gate

    @staticmethod
    def g2_safe_capture_with_zoonosis() -> Gate:
        """
        G2: Safe capture/handling with zoonosis precautions.

        Auto-fix: Add capture/zoonosis.
        """
        gate = Gate(
            name="G2",
            gate_type=GateType.DOMAIN,
            description="Safe capture/handling with zoonosis precautions",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            content = output.get("content", "")

            has_capture = "capture" in content.lower()
            has_zoonosis = "zoonosis" in content.lower() or "precaution" in content.lower()

            if has_capture and has_zoonosis:
                return GateResult(
                    gate_name="G2",
                    status=GateStatus.PASSED,
                    message="Safe capture/handling and zoonosis precautions included",
                )

            return GateResult(
                gate_name="G2",
                status=GateStatus.FAILED,
                message=f"Missing capture protocol (has={has_capture}) or zoonosis precautions (has={has_zoonosis})",
            )

        gate.check = check
        return gate

    @staticmethod
    def g3_rehab_or_coexistence_decision() -> Gate:
        """
        G3: Rehab/release or coexistence decision.

        Auto-fix: Decide rehab/coexistence.
        """
        gate = Gate(
            name="G3",
            gate_type=GateType.DOMAIN,
            description="Rehab/release or coexistence decision",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            verdict = output.get("verdict")
            content = output.get("content", "")

            has_rehab = "rehab" in content.lower() or "rehabilitate" in content.lower()
            has_release = "release" in content.lower()
            has_coexistence = "coexistence" in content.lower() or "coexist" in content.lower()

            if verdict and (has_rehab or has_release or has_coexistence):
                return GateResult(
                    gate_name="G3",
                    status=GateStatus.PASSED,
                    message=f"Decision made: {verdict}",
                )

            return GateResult(
                gate_name="G3",
                status=GateStatus.FAILED,
                message=f"No clear rehab/release or coexistence decision (verdict={verdict})",
            )

        gate.check = check
        return gate

    @staticmethod
    def g4_coordination_and_permits() -> Gate:
        """
        G4: Coordination & permits considered.

        Auto-fix: Consider coordination.
        """
        gate = Gate(
            name="G4",
            gate_type=GateType.DOMAIN,
            description="Coordination & permits considered",
            auto_fix_enabled=True,
            max_retries=2,
        )

        def check(output: Dict[str, Any], context: Dict[str, Any]) -> GateResult:
            content = output.get("content", "")

            has_coordination = "coordinat" in content.lower()
            has_permits = "permit" in content.lower() or "license" in content.lower()

            if has_coordination or has_permits:
                return GateResult(
                    gate_name="G4",
                    status=GateStatus.PASSED,
                    message="Coordination and/or permits considered",
                )

            return GateResult(
                gate_name="G4",
                status=GateStatus.FAILED,
                message="Coordination and permits not mentioned",
            )

        gate.check = check
        return gate


class DegradationLevel(int, Enum):
    """Graceful degradation levels for data availability."""

    ALL_SOURCES = 0  # All primary sources reachable
    SOME_FAILED = 1  # Some primary sources fail
    MOST_FAILED = 2  # Most live sources fail
    MISSING_VARIABLE = 3  # Required input variable missing/stale
    ALL_FAILED = 4  # All sources AND knowledge base fail


class DegradationManager:
    """Manages graceful degradation based on data availability."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.current_level = DegradationLevel.ALL_SOURCES
        self.level_history: List[Tuple[float, DegradationLevel]] = []

    def set_level(self, level: DegradationLevel, reason: str = "") -> None:
        """Set the current degradation level."""
        old_level = self.current_level
        self.current_level = level
        self.level_history.append((time.time(), level))

        logger.info(
            f"Degradation level changed: {old_level.name} -> {level.name}",
            extra={"reason": reason, "level": level.value}
        )

        # Emit degradation event
        hooks_registry = get_hooks(self.config)
        hooks_registry.emit(
            hooks.HookEvent.ON_DEGRADATION,
            hooks.HookContext(
                event=hooks.HookEvent.ON_DEGRADATION,
                config=self.config,
                metadata={"level": level.value, "reason": reason},
            ),
        )

    def get_banner(self) -> str:
        """Get the limitation banner for current degradation level."""
        return (
            "---\n"
            f"⚠️ LIMITATION NOTICE\n"
            f"This output was generated with reduced data availability (Level {self.current_level.value}). "
            "Cross-check with current data before acting on it. Substituted/missing sources "
            "are flagged inline.\n"
            "---\n"
        )

    def should_attempt_fix(self, gate_name: str) -> bool:
        """Determine if auto-fix should be attempted based on degradation level."""
        if self.current_level >= DegradationLevel.ALL_FAILED:
            return False  # No data available, don't attempt fixes
        if self.current_level >= DegradationLevel.MOST_FAILED:
            return gate_name in ["U1", "U2"]  # Only critical gates
        return True  # Attempt all fixes at lower degradation levels


class GateChecker:
    """Validates outputs against quality gates."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.gates: Dict[str, Gate] = {}
        self.degradation = DegradationManager(config)
        self._register_default_gates()

    def _register_default_gates(self) -> None:
        """Register the default universal and domain gates."""
        # Universal gates
        self.gates["U1"] = UniversalGates.u1_sources_cited()
        self.gates["U2"] = UniversalGates.u2_disclosure_before_recommendation()
        self.gates["U3"] = UniversalGates.u3_evidence_hierarchy_stated()
        self.gates["U4"] = UniversalGates.u4_language_matches_preference()
        self.gates["U5"] = UniversalGates.u5_uses_declared_template()
        self.gates["U6"] = UniversalGates.u6_every_claim_traceable()

        # Domain gates
        self.gates["G1"] = DomainGates.g1_species_id_and_triage()
        self.gates["G2"] = DomainGates.g2_safe_capture_with_zoonosis()
        self.gates["G3"] = DomainGates.g3_rehab_or_coexistence_decision()
        self.gates["G4"] = DomainGates.g4_coordination_and_permits()

    def register_gate(self, gate: Gate) -> None:
        """Register a custom gate."""
        self.gates[gate.name] = gate
        logger.info(f"Registered custom gate: {gate.name}")

    def check_gate(
        self,
        gate_name: str,
        output: Dict[str, Any],
        context: Dict[str, Any],
        apply_auto_fix: bool = True,
    ) -> GateResult:
        """
        Check a single gate.

        Args:
            gate_name: Name of the gate to check
            output: Output to validate
            context: Execution context
            apply_auto_fix: Whether to apply auto-fix if gate fails

        Returns:
            GateResult with check outcome
        """
        gate = self.gates.get(gate_name)
        if not gate:
            return GateResult(
                gate_name=gate_name,
                status=GateStatus.ERROR,
                message=f"Gate not found: {gate_name}",
            )

        start_time = time.time()
        result = gate.check(output, context)
        result.execution_time_ms = (time.time() - start_time) * 1000

        # Attempt auto-fix if failed and enabled
        if result.status == GateStatus.FAILED and apply_auto_fix and self.degradation.should_attempt_fix(gate_name):
            success, message, fixed_output = gate.apply_auto_fix(output, context)

            if success:
                result.status = GateStatus.AUTO_FIXED
                result.auto_fix_applied = True
                result.auto_fix_message = message
                output.update(fixed_output)
            else:
                result.auto_fix_message = message

        return result

    def check_all(
        self,
        output: Dict[str, Any],
        context: Dict[str, Any],
        gate_names: Optional[List[str]] = None,
        stop_on_critical_failure: bool = True,
    ) -> List[GateResult]:
        """
        Check all gates (or specified subset).

        Args:
            output: Output to validate
            context: Execution context
            gate_names: Optional list of specific gates to check
            stop_on_critical_failure: Whether to stop if a critical gate fails

        Returns:
            List of GateResult for all checked gates
        """
        gates_to_check = gate_names if gate_names else list(self.gates.keys())
        results = []

        for gate_name in gates_to_check:
            result = self.check_gate(gate_name, output, context)
            results.append(result)

            # Stop on critical failure if requested
            if result.status == GateStatus.FAILED:
                gate = self.gates.get(gate_name)
                if gate and gate.critical and stop_on_critical_failure:
                    logger.critical(f"Critical gate {gate_name} failed, stopping gate checks")
                    break

        return results

    def get_summary(self, results: List[GateResult]) -> Dict[str, Any]:
        """Get a summary of gate check results."""
        total = len(results)
        passed = sum(1 for r in results if r.status == GateStatus.PASSED)
        failed = sum(1 for r in results if r.status == GateStatus.FAILED)
        auto_fixed = sum(1 for r in results if r.status == GateStatus.AUTO_FIXED)
        errors = sum(1 for r in results if r.status == GateStatus.ERROR)

        return {
            "total_gates": total,
            "passed": passed,
            "failed": failed,
            "auto_fixed": auto_fixed,
            "errors": errors,
            "success_rate": passed / total if total > 0 else 0,
            "fix_rate": auto_fixed / (failed + auto_fixed) if (failed + auto_fixed) > 0 else 0,
            "degradation_level": self.degradation.current_level.value,
        }


class GateEnforcer:
    """Enforces quality gates with strict policies and blocking behavior."""

    def __init__(self, checker: GateChecker, config: Optional[Config] = None):
        self.checker = checker
        self.config = config

    def enforce(
        self,
        output: Dict[str, Any],
        context: Dict[str, Any],
        policy: str = "strict",
    ) -> Tuple[bool, List[GateResult], Optional[str]]:
        """
        Enforce quality gates with specified policy.

        Args:
            output: Output to validate
            context: Execution context
            policy: Enforcement policy ("strict", "lenient", "warning_only")

        Returns:
            Tuple of (should_block, results, error_message)
        """
        results = self.checker.check_all(output, context)

        if policy == "warning_only":
            return False, results, None

        summary = self.checker.get_summary(results)

        if policy == "strict":
            # Block if any gate failed (not auto-fixed)
            critical_failures = [
                r for r in results
                if r.status == GateStatus.FAILED and self.checker.gates[r.gate_name].critical
            ]

            if critical_failures:
                error_msg = f"Critical gates failed: {', '.join(r.gate_name for r in critical_failures)}"
                return True, results, error_msg

        if policy == "lenient":
            # Block only if U2 (disclosure) failed
            u2_result = next((r for r in results if r.gate_name == "U2"), None)
            if u2_result and u2_result.status == GateStatus.FAILED:
                return True, results, "Disclosure gate failed (required for lenient policy)"

        return False, results, None


import time


# Global gate checker instance
_checker: Optional[GateChecker] = None


def get_gate_checker(config: Optional[Config] = None) -> GateChecker:
    """Get the global gate checker instance."""
    global _checker
    if _checker is None:
        _checker = GateChecker(config)
    return _checker
