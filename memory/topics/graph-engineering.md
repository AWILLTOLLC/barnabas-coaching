# Graph Engineering (codejunkie99/graph-engineering)

Saved 2026-09-08 (Aaron flagged: wants to revisit). MIT licensed, 486★. Repo: https://github.com/codejunkie99/graph-engineering

## What it is
"Graph engineering" = designing the *topology* AI agents work through, not prompts. Two halves:

1. **Knowledge graphs** — what agents remember. Nodes = entities/facts, edges = relationships with time + provenance. Ontology → extraction → fusion → serving.
2. **Task graphs** — how agents work. Nodes = jobs, edges = execution dependencies (parallel fan-out, separate verifiers, stop rule, human gate).

Framing: prompt engineers steered the model's words, loop engineers steered iterations, graph engineers steer topology.

## Contents
- `graph-engineering/` — the skill itself (Claude Code / any skill harness). Install: clone + `cp -r graph-engineering/graph-engineering ~/.claude/skills/`. Has a teaching mode (`/kg-tutor`) plus 8 single-purpose workflow prompts (`/kg-scope` → `/kg-rag`) in WORKFLOWS.md.
- `references/` — distilled English translation of Southeast University's graduate Knowledge Graph course (Prof. Peng Wang, original repo npubird/KnowledgeGraphCourse, 4.4K★, Chinese). Files: curriculum.md, modeling.md, extraction.md, fusion-and-llm.md, task-graphs.md.
- `dist/graph-engineering.skill` — packaged skill.

## The 9-stage KG pipeline
scope → representation → ontology → entities → relations → events → quality gate → fusion → serve to LLMs.
Key idea: model the domain before extracting, fuse before storing, verify at every stage. A KG is a product with a schema, not a pile of triples.

## Task-graph rules (the interesting half for our agent stack)
- **Delete fake edges** — an arrow is real only when work flows through it.
- **The diamond** — split → parallel workers → separate verifier contexts → one owned merge.
- **Stop rule** (DeepMind × MIT, "Towards a Science of Scaling Agent Systems", 180 configs): teams win ~80% on work that splits; every config loses on sequential work. The shape of the work decides whether to parallelize.
- **Human gate** — put approval where mistakes are expensive to undo.

## Relevance to us
- Validates/parallels our own Dru-orchestrator + subagent diamond pattern (fan-out, verify in separate contexts, one merge owner). The DeepMind/MIT finding is direct evidence for when to delegate vs do sequentially — could sharpen the orchestration bright-line rules.
- Potential skill install for me: could use the KG pipeline to structure cross-agent knowledge (agent map, business facts) into a real graph instead of markdown tiers.
- Open question for revisit: whether to install as a skill or just mine references/task-graphs.md.
