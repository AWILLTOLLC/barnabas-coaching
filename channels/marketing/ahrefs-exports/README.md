# Ahrefs Export Intake

Drop any Ahrefs CSV export here. Maven will auto-detect the type and generate a `.report.md` file alongside it.

## How to Export from Ahrefs

### Keyword Explorer (keyword ideas)
1. Ahrefs → Keyword Explorer → enter seed keyword
2. Choose: Matching terms / Related terms / Questions
3. Apply filters if needed (e.g., KD max 30)
4. Top right → **Export** → CSV
5. Drop file here

### Site Explorer → Organic Keywords (what a domain ranks for)
1. Ahrefs → Site Explorer → enter domain (e.g., `barnabas.coach` or a competitor)
2. Left nav → **Organic search** → **Organic keywords**
3. Export → CSV

### Content Gap (what competitors rank for that you don't)
1. Ahrefs → Site Explorer → enter YOUR domain
2. Left nav → **Competitive analysis** → **Content gap**
3. Add competitor domains
4. Export → CSV

---

## Processing

```bash
# Process latest file
python3 scripts/ahrefs_process.py --latest

# Process specific file (optionally tag business for context)
python3 scripts/ahrefs_process.py ahrefs-exports/keywords.csv --business barnabas

# Business options: barnabas | glimmer | morse | blackraven

# Process all unprocessed files
python3 scripts/ahrefs_process.py --all
```

Reports are saved as `<filename>.report.md` in this same folder.

---

## File Naming (optional but helpful)

Suggest naming exports like:
- `barnabas-keyword-explorer-2026-03.csv`
- `barnabas-organic-keywords-2026-03.csv`
- `morse-content-gap-2026-03.csv`
