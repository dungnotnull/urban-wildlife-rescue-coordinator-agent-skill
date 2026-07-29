# Contributing to urban-wildlife-rescue-coordinator

Thank you for contributing! This project follows standard open-source practices.

## Getting Started

```bash
git clone <repo-url>
cd urban-wildlife-rescue-coordinator
pip install -r requirements.txt
pip install -e ".[dev]"
pre-commit install
```

## Project Structure

```
├── skills/                  # Claude Code sub-skill markdown files
│   ├── main.md              # Harness entry point & quality gates
│   ├── sub-gather-requirements.md
│   ├── sub-evidence-collector.md
│   ├── sub-core-analysis.md
│   ├── sub-knowledge-updater.md
│   └── sub-advisor.md
├── tools/                   # Python tooling
│   ├── knowledge_updater.py # Knowledge crawl pipeline
│   ├── test_knowledge_updater.py
│   ├── run_test_scenarios.py
│   └── validate_project.py
├── tests/                   # Test artifacts
│   ├── test-scenarios.md
│   └── TEST_RESULTS.md
├── SECOND-KNOWLEDGE-BRAIN.md # Living knowledge base
├── CLAUDE.md                # Skill identity & metadata
├── PROJECT-detail.md        # Full technical specification
└── PROJECT-DEVELOPMENT-PHASE-TRACKING.md
```

## Development Workflow

1. Fork and branch from `main`
2. Make changes following existing patterns
3. Run validators: `python tools/test_knowledge_updater.py && python tools/validate_project.py`
4. Submit a PR with a clear description

## Quality Standards

- All sub-skills follow the format: `frontmatter → Role & Persona → Workflow → Tools → Output Format → Quality Gates`
- Every claim in skill outputs must be traceable to a cited source
- Knowledge base entries require DOI or authoritative URL
- Python code passes existing unit tests without regression

## Adding New Sub-Skills

1. Create `skills/sub-<name>.md` following the standard format
2. Register in `skills/main.md` under `Sub-skills Available`
3. Add to the harness flow in `skills/main.md`
4. Update `PROJECT-detail.md` sub-skill catalog
5. Add test scenarios covering the new sub-skill

## Domain Expertise

Contributions are welcome from:
- Wildlife rehabilitators and veterinarians
- Urban ecologists and conservation biologists
- Zoonosis and public health specialists
- AI/ML researchers working on species identification
- GIS and spatial ecology practitioners
