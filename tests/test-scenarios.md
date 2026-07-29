# test-scenarios.md — Skill 223: urban-wildlife-rescue-coordinator

Five concrete end-to-end scenarios with real-world inputs, expected outputs, and quality gate maps. Each scenario exercises all universal gates U1–U6 and the domain gates G1, G2, G3, G4, plus all verdict categories.

---

## Scenario 1: Standard Injured Raptor Rescue (Verdict: Rescue Plan Ready)

**Input (English):**
> "We have a report of an injured red-tailed hawk (Buteo jamaicensis) found near Central Park, NYC. The bird cannot fly, wing droops on the right side, but is alert and responsive. Reported by a jogger at 7:30 AM. The hawk is on the ground near a footpath. We have one trained raptor handler available. Please coordinate rescue."

**Expected Steps:**
- sub-gather-requirements: Object = red-tailed hawk rescue, Scope = capture + transport, Timeframe = immediate, Language = en.
- sub-evidence-collector: Fetch IWRC raptor handling standards, local wildlife rehab center contacts, weather conditions for NYC, red-tailed hawk biology refs.
- sub-core-analysis: Species ID confirmed (Buteo jamaicensis, not endangered). Right wing droop → probable fracture or soft tissue injury → veterinary referral. Raptor capture protocol: thick gloves, towel/blanket, secure feet first. Transport: ventilated carrier, dark, warm.
- sub-knowledge-updater: Surface IWRC standards, avian triage protocols (Dubé & Duerr, 2017), stress physiology in captured wildlife (Dickens & Romero, 2013).
- sub-advisor: Verdict = Rescue Plan Ready. Risk: handler scratch from talons (moderate probability, low impact). Mitigation: puncture-resistant gloves, eye protection.
- Quality gate: U1–U6 + G1, G2, G3, G4 all pass.

**Gates Exercised:** U1, U2, U3, U4, U5, U6, G1 (species ID + triage ✓), G2 (safe capture with zoonosis ✓), G3 (rehab/release — vet referral for injury ✓), G4 (coordination ✓).

**Verdict Target:** Rescue Plan Ready

---

## Scenario 2: Minimal-Input Orphaned Fawn (Verdict: Conditional)

**Input (English):**
> "Found a baby deer. What do I do?"

**Expected Steps:**
- sub-gather-requirements: Clarify location, fawn condition (lying curled vs wandering crying), maternal observation time. Apply defaults for unknown fields with explicit assumption statement.
- sub-evidence-collector: Fetch local deer biology (white-tailed deer common in urban North America), maternal behavior (does leave fawns for hours), "kidnapping" prevention guidance.
- sub-core-analysis: Critical finding: healthy fawns are often left alone by does while foraging. If fawn is lying quietly curled, ears not curled from dehydration → DO NOT intervene, monitor from distance. If fawn is wandering, vocalizing continuously, visibly injured → contact licensed rehabber.
- sub-knowledge-updater: Surface relevant urban deer management references, fawn rehabilitation outcome studies.
- sub-advisor: Verdict = Conditional (vet referral if injured, otherwise in-situ monitoring). Risk: uninformed intervention causing unnecessary "rescue" of healthy fawn (high probability, high impact — fawn mortality increases in captivity).
- Quality gate: All gates pass with explicit assumption declaration.

**Gates Exercised:** U1, U2 (disclosure ✓), U3, U4, U5, U6, G1 (species ID defaults applied ✓), G2, G3 (rehab vs coexistence decision: in-situ preferred ✓), G4.

**Verdict Target:** Conditional (vet referral)

---

## Scenario 3: Comparison — Two Simultaneous Rescue Calls (Verdict: Rescue Plan Ready + Euthanasia/Referral)

**Input (English):**
> "We have two simultaneous rescue reports: (A) Adult raccoon with distemper-like symptoms (disoriented, no fear of humans, walking in circles) in a residential backyard in Toronto. (B) Juvenile eastern gray squirrel fallen from nest, no visible injuries, mother observed nearby in tree. We can send one rescue team. Prioritize."

**Expected Steps:**
- sub-gather-requirements: Two objects, comparison mode, prioritize resource allocation.
- sub-evidence-collector: Fetch raccoon distemper epidemiology, squirrel natural history, local rehabber availability.
- sub-core-analysis:
  - (A) Raccoon with neurologic signs: likely canine distemper virus or rabies. High zoonosis risk. Humane euthanasia recommended (distemper is fatal, rabies testing required). PPE: full rabies precautions.
  - (B) Juvenile squirrel: mother present → monitor 2–4 hours. If mother retrieves → no intervention. If abandoned → rehab.
  - Priority: (A) is public health risk → send team for safe removal, rabies testing. (B) is low urgency → monitor.
- sub-knowledge-updater: Surface rabies epidemiology (Hampson et al., 2015), distemper in urban raccoons, squirrel rehabilitation outcomes.
- sub-advisor: Dual verdict: (A) Euthanasia/Referral Needed (public health grounds) + (B) Conditional (monitor before intervention). Side-by-side scorecard with evidence-based prioritization.
- Quality gate: All gates pass for both cases.

**Gates Exercised:** U1, U2 (dual disclosure ✓), U3 (evidence hierarchy for both ✓), U4, U5, U6, G1 (dual species ID ✓), G2 (zoonosis precautions for raccoon ✓), G3 (euthanasia vs rehab decisions ✓), G4 (coordination priority ✓).

**Verdict Target:** Euthanasia/Referral Needed (Case A) + Conditional (Case B)

---

## Scenario 4: Conflict — Urban Coyote in School Zone (Verdict: Conditional)

**Input (English):**
> "Coyote (Canis latrans) spotted near an elementary school in suburban Denver during school hours (9:30 AM). Coyote appears healthy, no signs of mange or injury. School is in session. Local community divided: some demand lethal removal, others advocate coexistence. Police and animal control on scene."

**Expected Steps:**
- sub-gather-requirements: Object = coyote presence near school, Scope = conflict resolution + public safety, Timeframe = immediate, Language = en.
- sub-evidence-collector: Fetch coyote behavior (typically avoid humans, daytime presence may indicate habituation), Denver urban coyote management plan, legal framework (state wildlife agency), hazing protocols.
- sub-core-analysis: Coyote is healthy → hazing is first-line approach. Lethal removal contrary to evidence (disrupted pack structure increases conflicts). Recommendations: (1) Immediate: trained personnel haze coyote away from school using noise/visual deterrents. (2) Short-term: close school outdoor areas for 2 hours. (3) Long-term: community education on securing attractants (garbage, pet food), no-feeding ordinances. If coyote returns repeatedly with no fear response → relocation or euthanasia per state wildlife agency protocol. Zoonosis: coyote rabies risk low but non-zero, maintain distance.
- sub-advisor: Verdict = Conditional (vet referral not applicable, but conditional on hazing success and monitoring). Best case: coyote leaves, no return. Base case: coyote returns once, successful re-hazing. Worst case: coyote is food-conditioned and aggressive → escalated to wildlife agency for removal decision. Key risks: public panic, unauthorized lethal action, habituation.
- Quality gate: U2 (disclosure addresses both sides ✓).

**Gates Exercised:** U1, U2, U3, U4, U5, U6, G1 (species ID ✓), G2 (zoonosis ✓), G3 (coexistence decision ✓), G4 (coordination with police/animal control ✓).

**Verdict Target:** Conditional (vet referral)

---

## Scenario 5: Degraded Mode — Missing Key Input (Verdict: Inconclusive)

**Input (English):**
> "There's an animal stuck in a storm drain. Can't see it. Can hear scratching. Suburban area in Houston, TX."

**Expected Steps:**
- sub-gather-requirements: Object = unknown animal in storm drain, Scope = extraction, Timeframe = immediate (drowning risk if rain). Key missing: species, size, condition. Cannot confirm object → degradation Level 3.
- sub-evidence-collector: Fetch general storm drain rescue protocols, local Houston wildlife (possums, raccoons, armadillos, cats), municipal drain access procedures.
- sub-core-analysis: Cannot perform species-specific triage without ID → degradation. Recommendation: (1) DO NOT enter confined space without proper training and atmospheric monitoring (confined space entry regulations). (2) Contact municipal public works for drain access. (3) Have catch-pole, net, and carrier ready for unknown animal. (4) If rain forecasted → escalate urgency.
- sub-knowledge-updater: Surface general wildlife extraction references.
- sub-advisor: Verdict = Inconclusive — species cannot be identified. LIMITATION NOTICE (Level 3): "DATA UNAVAILABLE — species and condition unknown." Multi-scenario: Best (small animal, easy capture) / Base (raccoon/possum, standard extraction) / Worst (injured large animal or venomous snake requiring specialized team).
- Quality gate: U2 (limitation notice ✓), all gates flagged for incomplete data. No fabricated values.

**Gates Exercised:** U1, U2 (degradation limitation ✓), U3, U4, U5, U6, G1 (species ID flagged as unavailable ✓), G2, G3, G4.

**Verdict Target:** Inconclusive

---

### Gate Coverage Matrix

| Gate | S1 | S2 | S3 | S4 | S5 |
|------|----|----|----|----|-----|
| G1 (Species ID & triage) | ✓ | ✓ | ✓ | ✓ | ✓ (flagged unavailable) |
| G2 (Capture/handling + zoonosis) | ✓ | ✓ | ✓ | ✓ | ✓ |
| G3 (Rehab/release or coexistence) | ✓ | ✓ | ✓ | ✓ | ✓ |
| G4 (Coordination & permits) | ✓ | ✓ | ✓ | ✓ | ✓ |
| U1 (≥3 sources, ≥1 academic) | ✓ | ✓ | ✓ | ✓ | ✓ |
| U2 (Disclosure before recommendation) | ✓ | ✓ | ✓ | ✓ | ✓ |
| U3 (Evidence hierarchy) | ✓ | ✓ | ✓ | ✓ | ✓ |
| U4 (Language match) | ✓ | ✓ | ✓ | ✓ | ✓ |
| U5 (Output template) | ✓ | ✓ | ✓ | ✓ | ✓ |
| U6 (Traceable claims) | ✓ | ✓ | ✓ | ✓ | ✓ |

### Verdict Coverage
| Verdict | Covered By |
|--------|------------|
| Rescue Plan Ready | Scenario 1 (raptor rescue) |
| Conditional (vet referral) | Scenario 2 (fawn), Scenario 4 (coyote) |
| Euthanasia/Referral Needed | Scenario 3 (raccoon with distemper) |
| Inconclusive | Scenario 5 (unknown animal in drain) |
