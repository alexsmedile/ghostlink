---
version: 1.0
updated: 2026-07-05
summary: "Operating principles for this project + runtime enforcement hooks"
related:
  - PRD.md
  - ARCHITECTURE.md
---

# ghostlink — Operating Principles

## 1. Context is the system
Load only what's needed, progressively, by task.

**How the skill enforces this:**
- <add hook>

## 2. Separate intent from truth
Strategic docs and operational docs are different files.

**How the skill enforces this:**
- <add hook>

## 3. Small files over giant documents
Prefer modular files; avoid monoliths.

**How the skill enforces this:**
- <add hook>

## 4. Humans and agents share the same workspace
Plain markdown, frontmatter as signal layer.

**How the skill enforces this:**
- <add hook>

## 5. Operational memory compounds
Preserve lessons across sessions and teams.

**How the skill enforces this:**
- <add hook>

## 6. Progressive disclosure
References load on demand, never upfront.

**How the skill enforces this:**
- <add hook>

## 7. Three layers: intent → execution → validation
Every unit of work passes through all three.

**How the skill enforces this:**
- <add hook>

## 8. Humans decide, agents propose
Irreversibles require confirmation.

**How the skill enforces this:**
- <add hook>

## 9. Feedback ≠ verification ≠ benchmark
Verification ('did we ship what PLAN said?'), feedback ('was it the right thing?'), and benchmark (quantitative grading) are distinct — never conflate them.

**How the skill enforces this:**
- <add hook>

## 10. Build the smallest verified slice, full scope in mind
Default to the minimum high-impact slice now — verify, learn, extend. Build less, but as a finished block, not a stub. Hold full scope in mind so today's slice stays future-proof. Over-engineering (speculative generality, features without a current need) is the failure mode.

**How the skill enforces this:**
- @Planning policy `scope-down` (warn) asks for the smallest high-impact slice before milestones are fixed
- Deferred scope goes to ROADMAP as explicit `v2+`; non-goals are a first-class slot
