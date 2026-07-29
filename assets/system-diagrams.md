---
title: System Architecture Diagrams
description: Visual representations of the urban-wildlife-rescue-coordinator system architecture
version: 1.0.0
last_updated: 2026-07-27
---

# System Architecture Diagrams

## Overview

This directory contains visual assets and diagrams that document the urban-wildlife-rescue-coordinator system architecture, data flow, and component relationships.

## Available Diagrams

### 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  Claude Code / CLI                           ││
│  │            (User invokes /urban-wildlife-rescue-coordinator) ││
│  └─────────────────────────────────────────────────────────────┘│
│                                │                                  │
└────────────────────────────────┼──────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SKILL REGISTRY LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Skill Resolution │─▶│  Skill Router    │─▶│ Skill Execution │ │
│  │                  │  │ (CoT/Pattern)   │  │                 │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Skill Registry (config/skills.py)               ││
│  │  • Main skill: urban-wildlife-rescue-coordinator             ││
│  │  • Sub-skills: gather-requirements, evidence-collector,       ││
│  │                core-analysis, knowledge-updater, advisor      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        HOOKS LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Hook Registry (config/hooks.py)                 ││
│  │  • Pre-execution hooks                                      ││
│  │  • Post-execution hooks                                     ││
│  │  • Error recovery hooks                                      ││
│  │  • Gate check hooks                                          ││
│  │  • Degradation hooks                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QUALITY GATE LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │            Gate Checker (config/gates.py)                    ││
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   ││
│  │  │   U1     │   U2     │   U3     │   U4     │   U5     │   ││
│  │  │ Sources  │ Disclos. │ Evidence │ Language │ Template │   ││
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘   ││
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   ││
│  │  │   U6     │   G1     │   G2     │   G3     │   G4     │   ││
│  │  │ Claims   │ Species  │ Capture  │ Rehab    │ Coord.   │   ││
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │        Degradation Manager (5 levels: 0-4)                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │   Live Sources   │  │  Knowledge Base  │  │  Local Cache    ││
│  │  • WebSearch     │  │  SECOND-KNOWLEDGE│  │  SimpleCache    ││
│  │  • WebFetch      │  │  -BRAIN.md       │  │                 ││
│  │  • ArXiv API     │  │  (9 DOI refs)    │  │                 ││
│  │  • Semantic Sch  │  │                  │  │                 ││
│  └──────────────────┘  └──────────────────┘  └─────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPPORTING INFRASTRUCTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │ Configuration    │  │   Logging        │  │   Error         ││
│  │ (config/*.py)    │  │ (logging_config) │  │   Handling      ││
│  │ • Environment    │  │ • Structured     │  │   (utils.py)    ││
│  │ • LLM Config     │  │   JSON logs     │  │ • Retry logic   ││
│  │ • Feature Flags  │  │ • Performance    │  │ • Correlation   ││
│  └──────────────────┘  └──────────────────┘  └─────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2. End-to-End Execution Flow

```
USER REQUEST
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  1. LANGUAGE DETECTION (Pre-Flight)                        │
│     Detect en/vi from input characters                     │
│     Store LANG for output translation                        │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. REQUIREMENTS GATHERING (Step 1)                         │
│     Skill: sub-gather-requirements                          │
│     Output: {object, scope, timeframe, inputs, audience}   │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. EVIDENCE COLLECTION (Step 2)                            │
│     Skill: sub-evidence-collector                            │
│     Output: {current_data, authoritative_docs, news}        │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  4. CORE ANALYSIS (Step 3)                                   │
│     Skill: sub-core-analysis                                 │
│     Output: {triage, capture, handling, rehab_decision}      │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  5. KNOWLEDGE UPDATE (Step 4)                                │
│     Skill: sub-knowledge-updater                             │
│     Output: {citations, evidence_tiers, coverage}             │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  6. ADVISOR SYNTHESIS (Step 5)                               │
│     Skill: sub-advisor                                       │
│     Output: {verdict, scenarios, risks, evidence_chain}      │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  7. QUALITY GATE REVIEW (Step 6)                             │
│     Check all 10 gates (U1-U6, G1-G4)                       │
│     Apply auto-fix where possible                            │
│     Retry failed gates (max 2 attempts)                       │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  8. FINAL OUTPUT                                             │
│     Structured report with:                                  │
│     • Executive Summary                                       │
│     • Inputs & Scope                                         │
│     • Evidence Collected                                     │
│     • Analysis / Scorecard                                   │
│     • Academic Evidence                                       │
│     • Disclosure / Limitations                               │
│     • Recommendation / Conclusion                            │
└─────────────────────────────────────────────────────────────┘
```

### 3. Graceful Degradation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DEGRADATION LEVEL 0                       │
│  All primary sources reachable                               │
│  Full evidenced analysis                                      │
└─────────────────────────────────────────────────────────────┘
      │ (Some sources fail)
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DEGRADATION LEVEL 1                       │
│  Some primary sources fail                                   │
│  Use secondary/aggregate sources                             │
│  Flag each substituted source                                 │
└─────────────────────────────────────────────────────────────┘
      │ (Most sources fail)
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DEGRADATION LEVEL 2                       │
│  Most live sources fail                                      │
│  Use SECOND-KNOWLEDGE-BRAIN.md only                           │
│  Flag "historical context as of [date]"                      │
└─────────────────────────────────────────────────────────────┘
      │ (Required input missing)
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DEGRADATION LEVEL 3                       │
│  Required input variable missing/stale                       │
│  Proceed with available variables                             │
│  Mark missing as "DATA UNAVAILABLE"                          │
└─────────────────────────────────────────────────────────────┘
      │ (All sources fail)
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DEGRADATION LEVEL 4                       │
│  All sources AND knowledge base fail                         │
│  Emit "DATA UNAVAILABLE" notice                              │
│  Do NOT fabricate output                                     │
└─────────────────────────────────────────────────────────────┘
```

### 4. Knowledge Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KNOWLEDGE UPDATE PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            Schedule (Cron)                             │  │
│  │  • Weekly academic (Mon 08:00)                         │  │
│  │  • Daily news (07:00)                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         knowledge_updater.py                            │  │
│  │  • ArXiv API fetch                                     │  │
│  │  • Semantic Scholar API fetch                          │  │
│  │  • RSS feed parsing                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              SHA256 Deduplication                      │  │
│  │  • Compute hash from DOI/URL                          │  │
│  │  • Check against existing hashes                       │  │
│  │  • Skip already-present entries                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            Composite Scoring                           │  │
│  │  • Recency (40%): 1 - (days/730)                     │  │
│  │  • Relevance (40%): keyword matches                    │  │
│  │  • Citations (20%): log(citations)/log(1000)          │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Append to Knowledge Base                  │  │
│  │  SECOND-KNOWLEDGE-BRAIN.md                            │  │
│  │  • Section 7: Knowledge Update Log                    │  │
│  │  • Format: Date, Title, Authors, DOI/URL, Score       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Schemas

### Input Schema (Standard Skill Input)

```json
{
  "skill_name": "urban-wildlife-rescue-coordinator",
  "inputs": {
    "query": "User's wildlife rescue request",
    "species": "Identified or suspected species",
    "condition": "Observed condition/injury",
    "location": "Geographic location",
    "urgency": "emergency/urgent/non-urgent"
  },
  "context": {
    "language": "en",
    "user_id": "optional_user_id",
    "session_id": "optional_session_id",
    "timestamp": "2026-07-27T00:00:00Z"
  },
  "options": {
    "dry_run": false,
    "debug": false,
    "timeout_ms": 120000
  }
}
```

### Output Schema (Standard Skill Output)

```json
{
  "success": true,
  "outputs": {
    "verdict": "Rescue Plan Ready",
    "content": "Full report text...",
    "species_identified": "Red-tailed Hawk",
    "triage_performed": true,
    "recommendations": ["Action 1", "Action 2"],
    "coordination_contacts": ["org1", "org2"]
  },
  "errors": [],
  "metadata": {
    "execution_time_ms": 8500,
    "tokens_used": 12000,
    "degradation_level": 0
  },
  "quality_checks": {
    "U1": {"passed": true, "message": "3 sources cited"},
    "U2": {"passed": true, "message": "Disclosure present"},
    "G1": {"passed": true, "message": "Species identified"},
    "G2": {"passed": true, "message": "Capture protocol included"}
  }
}
```

## Component Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                  COMPONENT DEPENDENCY GRAPH                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  config/__init__.py (Configuration)                         │
│       │                                                       │
│       ├─── hooks.py (Hooks System)                           │
│       │         │                                            │
│       │         └─── skills.py (Skill Architecture)           │
│       │                   │                                  │
│       │                   └─── gates.py (Quality Gates)       │
│       │                                                         │
│       └─── tools/                                              │
│             ├─── logging_config.py (Logging)                   │
│             ├─── utils.py (Utilities)                          │
│             ├─── knowledge_updater.py (Knowledge Pipeline)      │
│             └─── run_test_scenarios.py (Testing)               │
│                                                                   │
│  SECOND-KNOWLEDGE-BRAIN.md (Knowledge Base)                       │
│       │                                                           │
│       └─── knowledge_updater.py (Updates)                        │
│                                                                   │
│  skills/*.md (Skill Definitions)                                  │
│       │                                                           │
│       └─── skills.py (Runtime execution)                         │
│                                                                   │
└─────────────────────────────────────────────────────────────┘
```

## Usage

These diagrams are referenced throughout the system documentation:
- `README.md`: High-level overview for users
- `CLAUDE.md`: System architecture for developers
- `PROJECT-detail.md`: Technical specification
- `config/SKILL.md`: Skill registry documentation

## Maintenance

- **Update frequency**: When architecture changes
- **Version tracking**: Tag with system version
- **Format consistency**: Use ASCII art for compatibility
- **Clarity优先**: Keep diagrams simple and clear

---

**Version**: 1.0.0
**Last Updated**: 2026-07-27
**Maintained By**: 972026 Skill Library
