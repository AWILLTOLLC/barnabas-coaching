---
name: search-first
description: Research-before-coding workflow. Search for existing tools, libraries, packages, and patterns before writing custom code. Use when starting a new feature, adding a dependency, or before building a new utility or abstraction.
origin: ECC (adapted for OpenClaw)
---

# Search First — Research Before You Code

Don't write custom code for problems that are already solved. Search first.

## When to Use

- Starting a new feature that likely has existing solutions
- Adding a dependency or integration
- When asked to "add X functionality" and about to write code
- Before creating a new utility, helper, or abstraction

## Workflow

```
1. NEED ANALYSIS
   Define what functionality is needed
   Identify language/framework constraints

2. SEARCH (parallel where possible)
   - Package registries: npm, PyPI, crates.io, etc.
   - Web search for battle-tested solutions
   - GitHub for maintained OSS
   - Check if an MCP server already provides this capability

3. EVALUATE candidates
   Score on: functionality, maintenance, community, docs, license, dependency weight

4. DECIDE
   - Adopt as-is    → exact match, well-maintained, permissive license
   - Extend/wrap    → partial match, good foundation
   - Compose        → combine 2-3 small packages
   - Build custom   → nothing suitable found (but informed by research)

5. IMPLEMENT
   Install package / configure integration / write minimal custom code
```

## Decision Matrix

| Signal | Action |
|--------|--------|
| Exact match, well-maintained, MIT/Apache | **Adopt** — install and use directly |
| Partial match, good foundation | **Extend** — install + write thin wrapper |
| Multiple weak matches | **Compose** — combine 2-3 small packages |
| Nothing suitable found | **Build** — write custom, but informed by research |

## Quick Mode (before writing any utility)

Run through this checklist mentally:
1. Does this already exist in the repo? Search existing code first.
2. Is this a common problem? Check npm/PyPI/etc.
3. Is there an OpenClaw skill or MCP tool for this? Check `~/.openclaw/workspace/skills/` and installed MCP servers (via mcporter).
4. Is there a maintained GitHub implementation? Search before writing net-new.

## Full Mode (for non-trivial decisions)

For significant architectural choices, spawn a subagent to research in parallel:

```
sessions_spawn(task="Research existing tools for: [DESCRIPTION]
Language/framework: [LANG]
Constraints: [ANY]

Search: package registries, GitHub, OpenClaw skills, MCP servers
Return: Structured comparison with recommendation")
```

## Search Shortcuts by Category

### Development Tooling
- Linting → `eslint`, `ruff`, `textlint`, `markdownlint`
- Formatting → `prettier`, `black`, `gofmt`
- Testing → `jest`, `pytest`, `go test`

### AI/LLM Integration
- Check MCP servers first (mcporter list)
- Document processing → `unstructured`, `pdfplumber`, `mammoth`

### Data & APIs
- HTTP clients → `httpx` (Python), `ky`/`got` (Node)
- Validation → `zod` (TS), `pydantic` (Python)
- Database → check for existing MCP servers first

### Content & Publishing
- Markdown processing → `remark`, `unified`, `markdown-it`
- Image optimization → `sharp`, `imagemin`

## Anti-Patterns

- **Jumping to code:** Writing a utility without checking if one exists
- **Ignoring MCP:** Not checking if an installed MCP server already provides the capability
- **Over-customizing:** Wrapping a library so heavily it loses its benefits
- **Dependency bloat:** Installing a massive package for one small feature
- **Not checking the repo first:** Reimplementing something that's already in the codebase
