# urban-wildlife-rescue-coordinator

**Urban Wildlife Rescue Coordination Advisor**

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-blue)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/urban-wildlife-rescue-coordinator/urban-wildlife-rescue-coordinator/actions/workflows/ci.yml/badge.svg)](https://github.com/urban-wildlife-rescue-coordinator/urban-wildlife-rescue-coordinator/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](CHANGELOG.md)

A professional-grade Claude Code harness for **Urban Wildlife Rescue & Rehabilitation** — gathers real-time authoritative data, applies recognized domain methods, integrates academic research, and delivers evidence-backed, risk-disclosed outputs with a continuously self-improving knowledge pipeline.

---

## Features

| Feature | Description |
|---------|-------------|
| 🏥 **Rescue Coordination** | Species ID, triage (injured/orphaned/conflict), safe capture/handling/transport, zoonosis risk assessment |
| 📊 **Evidence-Backed Analysis** | 10 quality gates (U1–U6 + G1–G4) enforce source citation, disclosure, evidence hierarchy, and claim traceability |
| 🔬 **Academic Integration** | Auto-updating knowledge base (9+ DOI-cited references) with ArXiv + Semantic Scholar + RSS crawl pipeline |
| 🌐 **Bilingual Support** | Full English/Vietnamese with automatic language detection and translation table |
| 🛡️ **Graceful Degradation** | 5 levels (0–4) with explicit LIMITATION banners — never fabricates data |
| 🧪 **Comprehensive Testing** | 5 concrete real-world test scenarios, 3 validators, 7 unit tests |
| 📦 **Production-Grade** | MIT licensed, CI/CD ready, pre-commit hooks, editorconfig, full documentation |

---

## Quick Start

### Installation
```bash
git clone <repo-url>
cd urban-wildlife-rescue-coordinator
pip install -r requirements.txt
```

### Usage (Claude Code)
```bash
/urban-wildlife-rescue-coordinator "Injured red-tailed hawk found in Central Park, can't fly"
```

The harness automatically:
1. Detects language (English/Vietnamese)
2. Clarifies requirements (species, condition, location, constraints)
3. Fetches authoritative data from IWRC, IUCN, and academic sources
4. Performs core analysis (triage → capture → rehab/release → coordination)
5. Surfaces academic evidence from the knowledge base
6. Synthesizes a risk-disclosed conclusion with full evidence chain
7. Validates through 10 quality gates before delivery

---

## Architecture

```
USER INPUT → Pre-Flight (language detection)
│
├─ Step 1: sub-gather-requirements   → Structured requirements
├─ Step 2: sub-evidence-collector    → Evidence bundle (real-time + reference data)
├─ Step 3: sub-core-analysis         → Rescue coordination (triage, capture, rehab, logistics)
├─ Step 4: sub-knowledge-updater     → Academic citations with tier labels
├─ Step 5: sub-advisor               → Risk-disclosed conclusion + evidence chain
└─ Step 6: Quality Gate Review       → U1–U6 + G1–G4 gates, auto-fix, 2-retry max
```

Full architecture diagram in [`PROJECT-detail.md`](PROJECT-detail.md).

---

## Quality Gates

### Universal Gates (U1–U6)
| Gate | Description |
|------|-------------|
| U1 | ≥3 sources cited, ≥1 academic/authoritative |
| U2 | Disclosure/limitations before recommendation |
| U3 | Evidence hierarchy stated per source (Tier 1–4) |
| U4 | Language matches user preference |
| U5 | Output uses declared template (all sections) |
| U6 | Every claim traceable to ≥1 source or flagged |

### Domain Gates (G1–G4)
| Gate | Description |
|------|-------------|
| G1 | Species ID & triage performed |
| G2 | Safe capture/handling with zoonosis precautions |
| G3 | Rehab/release or coexistence decision |
| G4 | Coordination & permits considered |

---

## Knowledge Pipeline

The `SECOND-KNOWLEDGE-BRAIN.md` is a living knowledge base auto-updated by `tools/knowledge_updater.py`:

- **Sources**: ArXiv API, Semantic Scholar API, RSS feeds
- **Dedup**: SHA256 of DOI/URL
- **Scoring**: recency (0.4) + keyword relevance (0.4) + citation count (0.2) → 0–10 composite
- **Schedule**: Weekly academic (Mondays 08:00) + Daily news (07:00)

```bash
# Manual update (dry-run preview)
python -m tools.knowledge_updater --dry-run

# News-only update
python -m tools.knowledge_updater --news-only

# Custom keyword search
python -m tools.knowledge_updater --keywords "avian influenza" "wildlife disease"
```

---

## Testing

```bash
# Knowledge updater unit tests (7 tests: hash, scoring, formatting, state)
python tools/test_knowledge_updater.py

# Structural & content validator (quality gates, scenarios, documentation)
python tools/run_test_scenarios.py

# 8-File Contract validator (10 check categories)
python tools/validate_project.py
```

### Test Scenarios
| # | Scenario | Species | Verdict |
|---|----------|---------|---------|
| 1 | Injured raptor rescue | Red-tailed Hawk | Rescue Plan Ready |
| 2 | Minimal-input orphan | White-tailed Deer | Conditional (vet referral) |
| 3 | Comparison: two rescues | Raccoon + Gray Squirrel | Euthanasia/Referral + Conditional |
| 4 | Conflict: coyote near school | Coyote | Conditional (vet referral) |
| 5 | Degraded: unknown in drain | Unknown | Inconclusive |

All 10 quality gates and all 4 verdict categories exercised across scenarios. See [`tests/test-scenarios.md`](tests/test-scenarios.md) for full details.

---

## Data Sources

### Domain Authoritative
- IWRC (International Wildlife Rehabilitation Council) — minimum standards
- IUCN/SSC (Species Survival Commission) — conservation status
- OIE/WHO — wildlife health and zoonosis guidelines
- NWRA, RSPCA Wildlife, WIRES — regional rehabilitation standards
- IATA Live Animals Regulations — transport standards

### Academic
- Journal of Wildlife Management — Wiley
- PLOS ONE (wildlife & conservation)
- Animals (MDPI)
- Frontiers in Veterinary Science
- Urban Ecosystems — Springer
- Journal of Zoo and Wildlife Medicine
- Conservation Biology — Wiley
- Biological Conservation — Elsevier

---

## Project Structure

```
urban-wildlife-rescue-coordinator/
├── skills/                          # Claude Code skill files
│   ├── main.md                      # Harness entry point (6-step orchestration)
│   ├── sub-gather-requirements.md   # Step 1: intake & clarification
│   ├── sub-evidence-collector.md    # Step 2: data aggregation
│   ├── sub-core-analysis.md         # Step 3: rescue coordination
│   ├── sub-knowledge-updater.md     # Step 4: academic evidence
│   └── sub-advisor.md              # Step 5: synthesis & conclusion
├── tools/                           # Python tooling
│   ├── knowledge_updater.py         # Crawl pipeline (ArXiv + Semantic Scholar + RSS)
│   ├── test_knowledge_updater.py    # Unit tests (7 tests)
│   ├── validate_project.py          # 8-File Contract validator (10 categories)
│   ├── run_test_scenarios.py        # Structural & content validator
│   ├── config.py                    # Shared configuration
│   ├── utils.py                     # Shared utilities
│   └── __init__.py
├── tests/                           # Test artifacts
│   ├── test-scenarios.md            # 5 concrete E2E scenarios
│   └── TEST_RESULTS.md              # Validation results & coverage matrix
├── .github/workflows/ci.yml         # CI pipeline (validate + crawl dry-run)
├── SECOND-KNOWLEDGE-BRAIN.md        # Living knowledge base (7 sections)
├── CLAUDE.md                        # Skill identity & metadata
├── PROJECT-detail.md                # Full technical specification
├── PROJECT-DEVELOPMENT-PHASE-TRACKING.md  # 6-phase build roadmap
├── LICENSE                          # MIT License
├── pyproject.toml                   # Python packaging
├── CONTRIBUTING.md                  # Development guide
├── CODE_OF_CONDUCT.md               # Contributor Covenant
├── CHANGELOG.md                     # Version history
└── README.md                        # This file
```

---

## Roadmap

- [x] Phase 0: Research & Skill Architecture
- [x] Phase 1: Core Sub-Skills (5 production-grade .md files)
- [x] Phase 2: Main Harness + 10 Quality Gates + Graceful Degradation + Bilingual
- [x] Phase 3: Knowledge Pipeline (crawl, dedup, scoring, cron)
- [x] Phase 4: Testing & Validation (5 scenarios, 3 validators, all gates exercised)
- [x] Phase 5: Integration & Polish (open-source infra, CI, full docs)

**Status: PRODUCTION READY v1.0.0 — All 6 phases at 100% completion.**

---

## License

MIT — see [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{urban-wildlife-rescue-coordinator,
  title = {urban-wildlife-rescue-coordinator: Urban Wildlife Rescue Coordination Advisor},
  author = {Urban Wildlife Rescue Coordinator Contributors},
  year = {2026},
  version = {1.0.0},
  url = {https://github.com/urban-wildlife-rescue-coordinator/urban-wildlife-rescue-coordinator}
}
```
