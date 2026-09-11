# Wiki Schema — raw sources → compiled wiki → index

Grafted onto the existing memory system (nothing moved, nothing migrated).

## Layers

1. **`wiki/raw/`** — immutable ground-truth sources (fetched pages, PDFs, transcripts, exports). LLM reads, never edits. Naming + metadata: see `wiki/raw/README.md`.
2. **`memory/topics/*.md`** — compiled wiki pages (already exists). Built *from* raw sources.
3. **`memory/MEMORY-L0.md` + `MEMORY.md`** — index (already exists).

## Ingest operation

1. Save the source to `wiki/raw/YYYY-MM-DD-slug.ext` (never edit it after).
2. Read it.
3. Create/update the relevant `memory/topics/*.md` page(s), citing the raw file path.
4. New topic → add a line to the `MEMORY-L0` index.
5. Append one line to `wiki/raw/LOG.md`:

   ```
   ## [YYYY-MM-DD] ingest | <slug> | <one-line description>
   ```

   `LOG.md` is append-only and greppable.

## Query rule

Any claim in a topic page that depends on a source document must cite its `wiki/raw/` path. If a factual claim about a document/site has no raw source behind it, either mark it `(unverified)` or fetch + file the source, then cite it.

## Lint (manual, passive)

Periodically — or when asked — check topic pages for:
- claims whose raw sources are missing,
- contradictions between pages,
- stale entries marked superseded.

No tooling for this yet; it's a documented manual practice. Build a linter only when it actually hurts.
