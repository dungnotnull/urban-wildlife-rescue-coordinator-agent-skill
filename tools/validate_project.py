"""
validate_project.py — Skill 223: urban-wildlife-rescue-coordinator
Production-grade 8-File Contract validator. Verifies physical file presence,
frontmatter correctness, section completeness, quality-gate coverage, knowledge
base integrity, test scenario coverage, and cross-file reference consistency.

Exit code 0 = all checks pass, non-zero = failures.
Usage: python tools/validate_project.py
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
TOOLS_DIR = ROOT / "tools"
TESTS_DIR = ROOT / "tests"

VERDICTS = [
    "Rescue Plan Ready",
    "Conditional (vet referral)",
    "Euthanasia/Referral Needed",
    "Inconclusive",
]

GATES_UNIVERSAL = ["U1", "U2", "U3", "U4", "U5", "U6"]
GATES_DOMAIN = [
    {"id": "G1", "check": "Species ID & triage performed", "fix": "Identify & triage"},
    {"id": "G2", "check": "Safe capture/handling with zoonosis precautions", "fix": "Add capture/zoonosis"},
    {"id": "G3", "check": "Rehab/release or coexistence decision", "fix": "Decide rehab/coexistence"},
    {"id": "G4", "check": "Coordination & permits considered", "fix": "Consider coordination"},
]
ALL_GATES = GATES_UNIVERSAL + [g["id"] for g in GATES_DOMAIN]

EIGHT_FILE_CONTRACT = [
    "CLAUDE.md",
    "PROJECT-detail.md",
    "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
    "README.md",
    "SECOND-KNOWLEDGE-BRAIN.md",
    "skills/main.md",
    "tools/knowledge_updater.py",
    "tools/test_knowledge_updater.py",
]

SUB_SKILL_REQUIRED = {
    "sub-gather-requirements",
    "sub-evidence-collector",
    "sub-core-analysis",
    "sub-knowledge-updater",
    "sub-advisor",
}

SUB_SKILL_SECTIONS = ["Role & Persona", "Workflow", "Output Format", "Quality Gates"]
MAIN_SECTIONS = [
    "Role & Persona",
    "Harness Execution Protocol",
    "Quality Gates",
    "Graceful Degradation",
    "Output Format",
]
KNOWLEDGE_SECTIONS = [
    "## 1. Core Concepts",
    "## 2. Key Research Papers",
    "## 3. State-of-the-Art",
    "## 4. Authoritative Data Sources",
    "## 5. Analytical Frameworks",
    "## 6. Self-Update Protocol",
    "## 7. Knowledge Update Log",
]


@dataclass
class ValidationReport:
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    failures: List[str] = field(default_factory=list)
    warn_msgs: List[str] = field(default_factory=list)


report = ValidationReport()


def _warn(msg: str) -> None:
    report.warnings += 1
    report.warn_msgs.append(msg)


def _ok() -> None:
    report.passed += 1


def _fail(label: str, detail: str = "") -> None:
    report.failed += 1
    report.failures.append(f"{label}: {detail}")


def require(cond: bool, label: str, detail: str = "") -> None:
    if cond:
        _ok()
    else:
        _fail(label, detail)


def read(p: Path) -> str:
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


def check_eight_file_contract() -> None:
    print("--- 1. 8-File Contract ---")
    for f in EIGHT_FILE_CONTRACT:
        require((ROOT / f).exists(), f"file present: {f}")


def check_supplementary_files() -> None:
    print("--- 2. Supplementary Files ---")
    supplementary = [
        "tools/run_test_scenarios.py",
        "tests/test-scenarios.md",
        "tests/TEST_RESULTS.md",
        "LICENSE",
        "pyproject.toml",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "CHANGELOG.md",
        ".editorconfig",
        ".github/workflows/ci.yml",
        "progression.json",
    ]
    for f in supplementary:
        p = ROOT / f
        require(p.exists(), f"supplementary file present: {f}")
        if not p.exists():
            _warn(f"Missing supplementary file: {f}")


def check_sub_skills() -> None:
    print("--- 3. Sub-Skills ---")
    sub_files = sorted(SKILLS_DIR.glob("sub-*.md"))
    sub_stems = {s.stem for s in sub_files}

    require(
        len(sub_files) >= 5,
        f"at least 5 sub-skills",
        f"found {len(sub_files)}",
    )
    require(
        sub_stems == SUB_SKILL_REQUIRED,
        "sub-skill set complete",
        f"missing={SUB_SKILL_REQUIRED - sub_stems}, extra={sub_stems - SUB_SKILL_REQUIRED}",
    )

    fm_re = re.compile(r"^---\s*\n(.*?\n)---", re.S)
    for s in sorted(sub_files):
        txt = read(s)
        m = fm_re.search(txt)
        require(bool(m), f"{s.name}: frontmatter present")
        if m:
            fm = m.group(1)
            require("name:" in fm and "description:" in fm, f"{s.name}: frontmatter has name+description")
        for sec in SUB_SKILL_SECTIONS:
            require(sec in txt, f"{s.name}: section '{sec}'")

    main_txt = read(SKILLS_DIR / "main.md")
    for sec in MAIN_SECTIONS:
        require(sec in main_txt, f"main.md: section '{sec}'")
    require("Pre-Flight" in main_txt, "main.md: pre-flight language detection")
    require(
        "limitation" in main_txt.lower(),
        "main.md: limitation/degradation banner",
    )


def check_quality_gates() -> None:
    print("--- 4. Quality Gates ---")
    main_txt = read(SKILLS_DIR / "main.md")
    for g in ALL_GATES:
        require(g in main_txt, f"main.md: gate {g}")
    require("Auto-Fix" in main_txt, "main.md: auto-fix column")

    adv_txt = read(SKILLS_DIR / "sub-advisor.md")
    combined = main_txt + "\n" + adv_txt
    for v in VERDICTS:
        require(v in combined, f"verdict '{v}' declared")


def check_knowledge_base() -> None:
    print("--- 5. Knowledge Base ---")
    brain = read(ROOT / "SECOND-KNOWLEDGE-BRAIN.md")
    require(len(brain) > 500, "brain: substantive content", f"length={len(brain)}")

    for i, sec in enumerate(KNOWLEDGE_SECTIONS):
        require(sec in brain, f"brain: section {i+1} '{sec}'")

    dois = re.findall(r"10\.\d{4,9}/[^\s|)\]]+", brain)
    require(len(dois) >= 4, f"brain: >=4 DOI-cited references", f"found {len(dois)}")

    require("Tier 1" in brain and "Tier 4" in brain, "brain: evidence hierarchy tiers 1-4")
    require(
        "IWRC" in brain or "IUCN" in brain,
        "brain: authoritative domain body referenced",
    )
    require("cron" in brain.lower() or "schedule" in brain.lower(), "brain: update schedule documented")


def check_test_coverage() -> None:
    print("--- 6. Test Coverage ---")
    sc = read(TESTS_DIR / "test-scenarios.md")
    require(
        "Scenario" in sc and sc.count("Scenario") >= 5,
        "test-scenarios: >=5 scenarios",
        f"found {sc.count('Scenario')}",
    )
    require("degraded" in sc.lower() or "missing" in sc.lower(), "test-scenarios: degraded case")
    require("conflict" in sc.lower() or "comparison" in sc.lower(), "test-scenarios: comparison/conflict case")

    for g in GATES_DOMAIN:
        require(g["id"] in sc, f"test-scenarios: gate {g['id']} referenced")

    results = read(TESTS_DIR / "TEST_RESULTS.md")
    require("PASS" in results or "pass" in results.lower(), "TEST_RESULTS: validation results present")
    require("PRODUCTION READY" in results, "TEST_RESULTS: production ready declared")


def check_python_tools() -> None:
    print("--- 7. Python Tools ---")
    ku = read(TOOLS_DIR / "knowledge_updater.py")
    checks = [
        ("KNOWLEDGE_CONFIG", "KNOWLEDGE_CONFIG block"),
        ("sha256", "SHA256 dedup"),
        ("score_entry", "scoring function"),
        ("fetch_with_retry", "retry logic"),
        ("--dry-run", "dry-run CLI flag"),
        ("append_to_brain", "append function"),
        ("logging" if "logging" in ku else "print(", "output mechanism"),
    ]
    for token, label in checks:
        require(token in ku, f"knowledge_updater.py: {label}")

    tu = read(TOOLS_DIR / "test_knowledge_updater.py")
    require("def test_hash" in tu, "test_knowledge_updater: hash test")
    require("def test_score" in tu, "test_knowledge_updater: score test")
    require("def test_format" in tu, "test_knowledge_updater: format test")

    rts = read(TOOLS_DIR / "run_test_scenarios.py")
    require("checks_passed" in rts, "run_test_scenarios: has pass/fail tracking")
    for label in ["G1", "G2", "G3", "G4", "U1", "U2", "U3"]:
        require(label in rts, f"run_test_scenarios: gate {label} checked")


def check_documentation() -> None:
    print("--- 8. Documentation ---")
    pdpt = read(ROOT / "PROJECT-DEVELOPMENT-PHASE-TRACKING.md")
    for phase in ["Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"]:
        require(phase in pdpt, f"PDPT: {phase}")
    require("100%" in pdpt, "PDPT: completion markers at 100%")
    require("PRODUCTION READY" in pdpt, "PDPT: production ready declared")

    claude = read(ROOT / "CLAUDE.md")
    require("Phase 5" in claude or "PRODUCTION READY" in claude, "CLAUDE.md: current phase updated")
    require("Harness Flow Summary" in claude, "CLAUDE.md: harness flow diagram")

    readme = read(ROOT / "README.md")
    require("## Usage" in readme or "## Installation" in readme, "README.md: usage or install section")
    require("MIT" in readme, "README.md: license mentioned")
    require("## Testing" in readme, "README.md: testing section")

    pd = read(ROOT / "PROJECT-detail.md")
    require("Harness Architecture" in pd, "PROJECT-detail: harness architecture diagram")
    require("Idea (Vietnamese)" in pd, "PROJECT-detail: Vietnamese idea section")
    require("E2E Execution Flow" in pd, "PROJECT-detail: E2E execution flow")

    changelog = read(ROOT / "CHANGELOG.md")
    require("1.0.0" in changelog, "CHANGELOG.md: version 1.0.0 entry")

    contributing = read(ROOT / "CONTRIBUTING.md")
    require("Getting Started" in contributing, "CONTRIBUTING.md: getting started")


def check_cross_references() -> None:
    print("--- 9. Cross-File References ---")
    main_txt = read(SKILLS_DIR / "main.md")
    for s in sorted(SUB_SKILL_REQUIRED):
        require(s in main_txt, f"main.md references sub-skill: {s}")

    claude = read(ROOT / "CLAUDE.md")
    for ref in ["PROJECT-detail.md", "PROJECT-DEVELOPMENT-PHASE-TRACKING.md", "SECOND-KNOWLEDGE-BRAIN.md"]:
        require(ref in claude, f"CLAUDE.md references: {ref}")

    readme = read(ROOT / "README.md")
    require("PROJECT-detail.md" in readme, "README.md references: PROJECT-detail.md")
    require("SECOND-KNOWLEDGE-BRAIN.md" in readme, "README.md references: knowledge base")


def check_file_sizes() -> None:
    print("--- 10. File Size Integrity ---")
    min_sizes = {
        "skills/main.md": 3000,
        "skills/sub-gather-requirements.md": 500,
        "skills/sub-evidence-collector.md": 500,
        "skills/sub-core-analysis.md": 500,
        "skills/sub-knowledge-updater.md": 500,
        "skills/sub-advisor.md": 500,
        "SECOND-KNOWLEDGE-BRAIN.md": 2000,
        "CLAUDE.md": 1500,
        "PROJECT-detail.md": 3000,
        "tools/knowledge_updater.py": 5000,
        "tests/test-scenarios.md": 1000,
    }
    for fname, min_bytes in min_sizes.items():
        p = ROOT / fname
        if p.exists():
            sz = len(read(p))
            require(
                sz >= min_bytes,
                f"{fname}: size >= {min_bytes}B",
                f"actual={sz}B",
            )


def main() -> None:
    print("=" * 60)
    print("  urban-wildlife-rescue-coordinator — Project Validator")
    print("=" * 60)

    check_eight_file_contract()
    check_supplementary_files()
    check_sub_skills()
    check_quality_gates()
    check_knowledge_base()
    check_test_coverage()
    check_python_tools()
    check_documentation()
    check_cross_references()
    check_file_sizes()

    print("\n" + "=" * 60)
    total = report.passed + report.failed
    print(f"  Results: {report.passed}/{total} passed"
          f"  |  {report.warnings} warnings")
    print("=" * 60)

    if report.warn_msgs:
        for w in report.warn_msgs:
            print(f"  [WARN]  {w}")

    if report.failures:
        print(f"\n  FAILURES ({report.failed}):")
        for f in report.failures:
            print(f"  [FAIL]  {f}")
        sys.exit(1)

    print("  [OK] All checks passed — PRODUCTION READY v1.0.0")
    sys.exit(0)


if __name__ == "__main__":
    main()
