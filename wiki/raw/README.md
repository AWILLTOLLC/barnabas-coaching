# wiki/raw/ — Raw Sources

Immutable ground-truth documents: fetched pages, PDFs, transcripts, exports.

Rules:
- **The LLM reads but NEVER edits anything in `wiki/raw/`** (except appending to `LOG.md`).
- One file per source.
- Naming: `YYYY-MM-DD-slug.ext` (date = date fetched/received).
- Text files carry metadata at top as YAML frontmatter:

  ```
  ---
  source: <url or origin>
  fetched: YYYY-MM-DD
  type: website|pdf|transcript|export
  ---
  ```

Conventions for compiling these into the memory wiki live in `wiki/SCHEMA.md`.
Ingests are logged append-only in `LOG.md`.
