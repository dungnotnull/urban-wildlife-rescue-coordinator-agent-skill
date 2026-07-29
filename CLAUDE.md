# CLAUDE.md — Skill 223: urban-wildlife-rescue-coordinator

## Skill Identity
- **Skill Name:** `urban-wildlife-rescue-coordinator`
- **Tagline:** Urban Wildlife Rescue Coordination Advisor — evidence-backed analysis & decision-support harness for urban wildlife rescue and rehabilitation.
- **Current Phase:** Phase 5 — Integration & Polish (PRODUCTION READY v1.0.0)
- **Folder:** `D:\972026\223-urban-wildlife-rescue-coordinator\`
- **Version:** 1.0.0
- **License:** MIT

---

## Problem This Skill Solves

Urban Wildlife Rescue & Rehabilitation practitioners face three structural gaps:
1. **Data fragmentation** — authoritative data scattered across sources (IWRC, IUCN, veterinary refs, local orgs, academic journals).
2. **Methodology gaps** — most advice lacks systematic, evidence-graded methods for triage, capture, handling, and release decisions.
3. **No self-improvement** — static tools don't learn from new research or adapt to emerging zoonosis threats and rehabilitation protocols.

This skill addresses all three via real-time aggregation, professional frameworks, and a continuously-updated knowledge crawl pipeline. It transforms Claude into a domain expert that delivers structured, risk-disclosed outputs grounded in wildlife-vet science.

---

## Harness Flow Summary

```
/urban-wildlife-rescue-coordinator invoked
│
├─ Pre-Flight: Language detection (en/vi)
│
├─ Step 1: sub-gather-requirements   → Clarify object of analysis, constraints, timeframe, inputs, audience, language.
├─ Step 2: sub-evidence-collector     → Fetch authoritative real-time and reference data from domain and academic sources.
├─ Step 3: sub-core-analysis          → Triage rescue reports, propose safe capture/handling/transport, recommend rehab or coexistence.
├─ Step 4: sub-knowledge-updater      → Query knowledge base for academic evidence; surface citations with tier labels.
├─ Step 5: sub-advisor                → Synthesize into risk-disclosed conclusion with full evidence chain.
└─ Step 6: Quality Gate Review        → U1–U6 + G1–G4 gates, auto-fix, 2-retry max, degradation if needed.
```

---

## Sub-Skills

| `skills/sub-gather-requirements.md` | Intake specialist — clarify object, scope, timeframe, inputs, audience, language before any data fetching. |
| `skills/sub-evidence-collector.md` | Data librarian — fetch real-time data, authoritative docs, recent news, and reference benchmarks. |
| `skills/sub-core-analysis.md` | Rescue coordinator — triage, safe capture/handling/transport, rehab vs coexistence, release criteria, logistics. |
| `skills/sub-knowledge-updater.md` | Research librarian — query knowledge base, surface 3–5 citations with tier labels, flag gaps for crawl pipeline. |
| `skills/sub-advisor.md` | Senior advisor — synthesize full report with risk-disclosed conclusion and evidence chain. |

---

## Quality Gates

### Universal Gates (U1–U6)
| Gate | Check | Auto-Fix |
|------|-------|----------|
| U1 | ≥3 sources cited, ≥1 academic/authoritative | Fetch from KB / evidence collector |
| U2 | Disclosure/limitations before recommendation | Prepend standard disclosure |
| U3 | Evidence hierarchy stated per source (Tier 1–4) | Annotate source tiers |
| U4 | Language matches user preference | Translate output |
| U5 | Output uses declared template (all sections) | Reformat to template |
| U6 | Every claim traceable to ≥1 source or flagged | Mark each claim with source or [analyst judgment] |

### Domain Gates (G1–G4)
| Gate | Check | Auto-Fix |
|------|-------|----------|
| G1 | Species ID & triage performed | Identify & triage |
| G2 | Safe capture/handling with zoonosis precautions | Add capture/zoonosis |
| G3 | Rehab/release or coexistence decision | Decide rehab/coexistence |
| G4 | Coordination & permits considered | Consider coordination |

---

## Graceful Degradation

| Level | Condition | Behavior |
|-------|-----------|----------|
| 0 | All primary sources reachable | Full evidenced analysis |
| 1 | Some primary sources fail | Use secondary/aggregate sources; flag each substituted source |
| 2 | Most live sources fail | SECOND-KNOWLEDGE-BRAIN.md only; flag "historical context as of [date]" |
| 3 | Required input variable missing/stale | Proceed with available variables; mark "DATA UNAVAILABLE" |
| 4 | All sources AND knowledge base fail | Emit "DATA UNAVAILABLE" notice; do NOT fabricate output |

---

## Tools Required

- **WebSearch** — live domain news, reports, standards updates
- **WebFetch** — scrape authoritative sources (IWRC, IUCN, academic journals)
- **Read / Write** — read SECOND-KNOWLEDGE-BRAIN.md; append knowledge entries
- **Bash** — run `tools/knowledge_updater.py` for periodic crawl
- **Skill** — invoke sub-skills sequentially through the harness

---

## Knowledge Sources

### Domain Authoritative Sources
- IWRC (International Wildlife Rehabilitation Council) — minimum standards for wildlife rehabilitation
- IUCN/SSC (Species Survival Commission) — conservation status, best practices
- OIE/WHO — wildlife health and zoonosis guidelines
- Local wildlife rescue organizations and wildlife rehabilitation centers
- Veterinary wildlife medicine references (Fowler's Zoo and Wild Animal Medicine)
- Animal handling and transport standards (IATA Live Animals Regulations)

### Academic & Research Sources
- Journal of Wildlife Management — Wiley
- PLOS ONE (wildlife & conservation)
- Animals (MDPI)
- Frontiers in Veterinary Science
- Urban Ecosystems — Springer
- Journal of Zoo and Wildlife Medicine
- Conservation Biology — Wiley
- Biological Conservation — Elsevier

### Academic Crawl Targets
- Semantic Scholar / ArXiv for "urban wildlife rescue", "wildlife triage rehabilitation", "human-wildlife conflict coexistence" keyword clusters
- Domain preprint servers where applicable
- Standards bodies and professional associations (IWRC, IUCN/SSC, OIE)

---

## Supporting Python Tools

| File | Purpose |
|------|---------|
| `tools/knowledge_updater.py` | Crawl pipeline: ArXiv + Semantic Scholar + RSS → SHA256 dedup → composite scoring → append to knowledge base |
| `tools/test_knowledge_updater.py` | Unit tests: hash dedup, composite scoring, entry formatting |
| `tools/validate_project.py` | 8-File Contract validator: file presence, sections, gates, cross-references |
| `tools/run_test_scenarios.py` | Structural & content validator covering all quality gates and verdict categories |
| `tools/config.py` | Shared configuration: sources, tiers, verdicts, degradation levels |
| `tools/utils.py` | Shared utilities: logging, hashing, progression tracking, retry logic |

---

## Automated Knowledge Update Schedule

```cron
# Weekly academic update (Mondays 8:00 AM)
0 8 * * 1 python D:/972026/223-urban-wildlife-rescue-coordinator/tools/knowledge_updater.py >> logs/knowledge_update.log 2>&1

# Daily news update (Daily 7:00 AM)
0 7 * * * python D:/972026/223-urban-wildlife-rescue-coordinator/tools/knowledge_updater.py --news-only >> logs/knowledge_news.log 2>&1
```

Manual invocation: `python tools/knowledge_updater.py --dry-run` | `--keywords "..."` | `--news-only`

---

## Active Development Tasks

- [x] Phase 0: Architecture & source map (CLAUDE.md, PROJECT-detail.md, PDPT.md)
- [x] Phase 1: Core sub-skills (5 production-grade .md files)
- [x] Phase 2: Main harness + 10 quality gates + graceful degradation + bilingual support
- [x] Phase 3: Knowledge pipeline + unit tests + cron scheduling
- [x] Phase 4: Testing & validation — 5 test scenarios, structural validator, all gates exercised
- [x] Phase 5: Integration & polish — open-source infrastructure, CI/CD, full documentation

**Status: PRODUCTION READY v1.0.0 — All 6 phases at 100% completion.**

---

## References

- `PROJECT-detail.md` — full technical specification with architecture diagram and E2E flow
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — 6-phase build roadmap with task tracking
- `SECOND-KNOWLEDGE-BRAIN.md` — self-improving living knowledge base
- `progression.json` — machine-readable progression state
- `D:\972026\SKILL-STANDARD.md` — library-wide skill standard
- Reference implementation: `D:\vn-finance-analysis-hd-skill`
