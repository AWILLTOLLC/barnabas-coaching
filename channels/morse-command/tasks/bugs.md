# Morse Code Defense — Bug Tracker

> Status values: `[ ] Open` · `[~] In Progress` · `[x] Fixed` · `[-] Won't Fix` · `[?] Needs Repro`

---

## Open

### B-001 — Word Entity Captures Single-Letter Inputs
**Status:** [ ] Open  
**Added:** 2026-03-20  
**Severity:** High  
**Description:** When a word entity appears on screen, it captures all single-letter entity inputs. This breaks the player's ability to shoot individual letter entities while a word entity is active.  
**Steps to Reproduce:**
1. Play until a word entity spawns
2. While the word entity is present, attempt to shoot a single-letter entity by typing its letter
3. Input is consumed by the word entity instead of firing at the letter entity  
**Expected:** Single-letter inputs should target letter entities; word entity should only consume inputs that are part of its word sequence.  
**Notes:** —

---

## In Progress

_Nothing here yet._

---

## Fixed

_Nothing here yet._
