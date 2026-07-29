---
title: Urban Wildlife Rescue & Rehabilitation Domain Knowledge
description: Authoritative domain knowledge base for the urban-wildlife-rescue-coordinator system
version: 1.0.0
last_updated: 2026-07-27
---

# Urban Wildlife Rescue & Rehabilitation — Domain Knowledge

## Purpose

This directory contains domain-specific knowledge, reference materials, and authoritative sources used by the urban-wildlife-rescue-coordinator system. These references provide the foundational knowledge for evidence-backed analysis and recommendations.

## Structure

```
references/
├── domain-knowledge.md        # This file — domain overview
├── species-taxonomy.md         # Species classification and identification
├── triage-protocols.md         # Wildlife triage decision trees
├── capture-handling.md         # Safe capture and handling techniques
├── rehabilitation.md           # Rehabilitation protocols and criteria
├── zoonosis-risks.md           # Zoonotic disease risks and precautions
├── release-criteria.md         # Release assessment criteria
├── coordination-networks.md     # Wildlife rescue coordination networks
└── legal-permits.md            # Legal requirements and permit processes
```

## Core Concepts

### 1. Urban Wildlife Ecology

Urban wildlife refers to wild animals living in urban and suburban environments. Common species include:
- **Birds**: Pigeons, sparrows, starlings, hawks, owls, waterfowl
- **Mammals**: Squirrels, raccoons, opossums, deer, foxes, coyotes, bats
- **Reptiles**: Snakes, turtles (in warmer climates)
- **Amphibians**: Frogs, salamanders (near water sources)

### 2. Human-Wildlife Conflict Types

- **Habituation**: Animals losing natural fear of humans
- **Food conditioning**: Animals associating humans with food
- **Property damage**: Nests in structures, garden damage
- **Public safety**: Aggressive behavior, disease transmission
- **Injury/Orphaning**: Vehicle collisions, window strikes, pet attacks

### 3. Rescue Triage Categories

| Category | Description | Immediate Action |
|----------|-------------|------------------|
| Emergency | Life-threatening injury or danger | Immediate rescue + transport to rehab |
| Urgent | Serious injury but stable | Rescue within 2-4 hours |
| Non-urgent | Minor injury or orphaned | Rescue within 24 hours |
| Observation | No intervention needed | Monitor only |
| Euthanasia | Non-recoverable suffering | Humane euthanasia required |

## Authoritative Sources

### International Bodies

1. **IWRC (International Wildlife Rehabilitation Council)**
   - Minimum Standards for Wildlife Rehabilitation
   - Wildlife Rehabilitation Code of Ethics
   - [www.iwrc-online.org](https://www.iwrc-online.org)

2. **IUCN/SSC (Species Survival Commission)**
   - Species conservation status assessments
   - Best practice guidelines
   - [www.iucn.org](https://www.iucn.org)

3. **OIE/WHO**
   - Wildlife health and zoonosis guidelines
   - Disease reporting protocols
   - [www.oie.int](https://www.oie.int)

### Regional Resources

4. **Local wildlife rehabilitation centers**
   - Species-specific care protocols
   - Local permitting requirements
   - Volunteer networks

5. **Veterinary wildlife medicine references**
   - Fowler's Zoo and Wild Animal Medicine
   - Wildlife Rehabilitation: A Comprehensive Approach
   - Journal of Zoo and Wildlife Medicine

### Academic Sources

6. **Peer-reviewed journals**
   - Journal of Wildlife Management
   - PLOS ONE (wildlife & conservation)
   - Animals (MDPI)
   - Frontiers in Veterinary Science
   - Urban Ecosystems

## Evidence-Based Protocols

### Triage Decision Framework

```
┌─────────────────────────────────────────────────────────────┐
│                    TRIAGE DECISION TREE                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. IS THE ANIMAL IN IMMEDIATE DANGER?                      │
│     • Yes → EMERGENCY rescue                                 │
│     • No → Continue to 2                                     │
│                                                               │
│  2. DOES THE ANIMAL HAVE OBVIOUS INJURIES?                  │
│     • Yes → ASSESS severity                                  │
│       - Severe → URGENT rescue                               │
│       - Mild → NON-URGENT rescue                             │
│     • No → Continue to 3                                     │
│                                                               │
│  3. IS THE ANIMAL ORPHANED (KNOW OR MOTHER DEAD)?          │
│     • Yes → ASSESS age/condition                            │
│       - Too young → NON-URGENT rescue                        │
│       - Independent → OBSERVATION only                       │
│     • No → Continue to 4                                    │
│                                                               │
│  4. IS THE ANIMAL IN APPROPRIATE HABITAT?                  │
│     • Yes → OBSERVATION only                                │
│     • No → CONSIDER relocation vs. coexistence               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Zoonosis Risk Matrix

| Species | High Risk | Medium Risk | Low Risk |
|---------|-----------|-------------|----------|
| Bats | ✓ (rabies, histoplasmosis) | | |
| Raccoons | ✓ (rabies, baylisascaris) | | |
| Skunks | ✓ (rabies) | | |
| Foxes | ✓ (rabies) | | |
| Coyotes | ✓ (rabies) | | |
| Squirrels | | ✓ (tularemia) | |
| Opossums | | ✓ (various) | |
| Deer | | ✓ (Lyme disease vectors) | |
| Birds (general) | | | ✓ |
| Reptiles | | Salmonella | |

### Safe Capture Techniques

1. **Never attempt capture without proper training and equipment**
2. **Use species-appropriate capture methods**
3. **Minimize stress and handling time**
4. **Protect yourself from bites, scratches, and disease**
5. **Secure in appropriate container for transport**

### Rehabilitation Criteria

**Suitable for Rehabilitation:**
- Injuries that are treatable with reasonable time/resources
- Young animals with appropriate care protocols
- Conditions that don't compromise long-term survival
- Animals with good prognosis for release

**Not Suitable for Rehabilitation:**
- Severe injuries with poor prognosis
- Chronic conditions affecting survival
- Habituated animals that can't be safely released
- Non-native/invasive species (legal restrictions)

## Knowledge Updates

This reference directory is updated through the automated knowledge crawl pipeline (`tools/knowledge_updater.py`) which:
1. Fetches latest research from ArXiv and Semantic Scholar
2. Monitors RSS feeds for domain news
3. Applies SHA256 deduplication
4. Scores entries by recency, relevance, and citations
5. Appends new entries to SECOND-KNOWLEDGE-BRAIN.md

## Usage in Skills

Skills reference these materials through:
- **Direct citation**: Authoritative sources for claims
- **Protocol guidance**: Step-by-step decision frameworks
- **Species information**: Taxonomy, natural history, risks
- **Coordination networks**: Local and regional contacts

## Maintenance

- **Review cycle**: Quarterly review of all references
- **Update sources**: Annual refresh of source URLs
- **Archive outdated**: Preserve superseded protocols
- **Version control**: Track changes with dates

---

**Version**: 1.0.0
**Last Updated**: 2026-07-27
**Maintained By**: 972026 Skill Library
