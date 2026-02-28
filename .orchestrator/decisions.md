# Architectural Decisions

Automatically maintained by AI Orchestrator and the project-memory skill.
Tracks key design decisions using Architectural Decision Records (ADRs).

### ADR-001: [Pasted text #1 — 143 lines]: do everything required in this (2026-02-28)

**Context:**
Task: [Pasted text #1 — 143 lines]:
do everything required in this pasted text: # Conut AI Engineering Hackathon

## 12-Hour Chief of Operations Agent Challenge

### Course
AI Engineering (focus on AI systems, full MLOps pipeline, and business feasibility)

---

## Overview
You are working with real opera

**Decision:**
Good, I've seen the data structure. Now here's my review:

---

**CHANGES_NEEDED**

### Issues found:

1. **Data path mismatch.** The plan copies data into `data/raw/Conut bakery Scaled Data/` but the files already live at repo root under `Conut bakery Scaled Data/`. The plan should read from the existing path (or symlink/copy via a Make target), not assume a `data/raw/` layout that doesn't exist.

**Consequences:**
Outcome: APPROVED
