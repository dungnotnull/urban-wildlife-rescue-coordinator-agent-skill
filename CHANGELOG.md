# Changelog

All notable changes to urban-wildlife-rescue-coordinator will be documented here.

## [1.0.0] — 2026-07-10

### Added
- Complete 5-sub-skill harness architecture (gather-requirements, evidence-collector, core-analysis, knowledge-updater, advisor)
- 10 quality gates (U1–U6 universal + G1–G4 domain-specific) with auto-fix and 2-retry enforcement
- 5-level graceful degradation protocol with explicit LIMITATION banners
- Bilingual English/Vietnamese language detection with translation table
- SECOND-KNOWLEDGE-BRAIN.md living knowledge base with 7 sections
- Automated knowledge crawl pipeline (ArXiv + Semantic Scholar + RSS) with SHA256 dedup and composite scoring
- Production-grade test suite: unit tests + structural validator + 5 E2E test scenarios
- 8-File Contract compliance (CLAUDE.md, PROJECT-detail.md, PDPT.md, README.md, SKB.md, main.md, knowledge_updater.py, test suite)
- Cron scheduling for weekly academic and daily news updates
- MIT license, open-source infrastructure (pyproject.toml, pre-commit, CI)

### Fixed
- CLAUDE.md phase label updated from Phase 0 to Phase 5
- Missing LICENSE file created
- Missing validate_project.py created
- Missing progression.json created

### Documentation
- CONTRIBUTING.md with development workflow and sub-skill addition guide
- CODE_OF_CONDUCT.md (Contributor Covenant 2.1)
- CHANGELOG.md (this file)
- README.md updated with complete install/usage/testing documentation
