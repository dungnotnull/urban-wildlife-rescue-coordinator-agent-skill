"""
config.py — Shared configuration for urban-wildlife-rescue-coordinator tools.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

BRAIN_PATH = ROOT_DIR / "SECOND-KNOWLEDGE-BRAIN.md"
SKILLS_DIR = ROOT_DIR / "skills"
TOOLS_DIR = ROOT_DIR / "tools"
TESTS_DIR = ROOT_DIR / "tests"
LOGS_DIR = ROOT_DIR / "logs"

LOGS_DIR.mkdir(exist_ok=True)

EVIDENCE_TIERS = {
    "Tier 1": "Systematic review / meta-analysis / official standard",
    "Tier 2": "Peer-reviewed academic paper / RCT",
    "Tier 3": "Industry report / professional association guideline",
    "Tier 4": "News / blog / vendor material",
}

ANALYSIS_VERDICTS = [
    "Rescue Plan Ready",
    "Conditional (vet referral)",
    "Euthanasia/Referral Needed",
    "Inconclusive",
]

DOMAIN_AUTHORITATIVE_SOURCES = [
    "IWRC (International Wildlife Rehabilitation Council)",
    "IUCN/SSC (Species Survival Commission)",
    "OIE/WHO wildlife health guidelines",
    "Local wildlife rescue organizations",
    "Veterinary wildlife medicine references",
    "Animal handling and transport standards",
]

ACADEMIC_SOURCES = [
    "Journal of Wildlife Management — Wiley",
    "PLOS ONE (wildlife & conservation)",
    "Animals (MDPI)",
    "Frontiers in Veterinary Science",
    "Urban Ecosystems — Springer",
    "Journal of Zoo and Wildlife Medicine",
]

DEGRADATION_LEVELS = {
    0: "All primary sources reachable — full evidenced analysis",
    1: "Some primary sources fail — use secondary/aggregate sources; flag each substituted source",
    2: "Most live sources fail — SECOND-KNOWLEDGE-BRAIN.md only; flag historical context as of date",
    3: "Required input variable missing/stale — proceed with available variables; mark DATA UNAVAILABLE",
    4: "All sources AND knowledge base fail — emit DATA UNAVAILABLE notice; do NOT fabricate output",
}
