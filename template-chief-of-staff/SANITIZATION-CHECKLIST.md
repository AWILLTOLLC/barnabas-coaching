# SANITIZATION-CHECKLIST.md — Template Build Verification

_Run from the directory containing `template-chief-of-staff/` before every package release. Every command must return zero matches (exit 1 from grep = clean)._

## Forbidden names and identifiers

```bash
cd template-chief-of-staff

# People
grep -rniE 'dru|aaron|williams|lily' . && echo "FAIL: people"

# Projects and businesses
grep -rniE 'barnabas|black raven|glimmer|biotech|morse|safeharbor|creel|buzz' . && echo "FAIL: businesses"

# Wizard persona
grep -rniE 'wizard|🧙|spirit animal|magic' . && echo "FAIL: wizard"

# Domains and hosts
grep -rniE 'kaw\.cc|tailb4a099|100\.65\.203\.16|apollo' . && echo "FAIL: hosts/domains"

# Personal places
grep -rniE 'fremont|phinney|seattle|mukilteo|lynwood|98103' . && echo "FAIL: places"

# Internal artifacts
grep -rniE 'hermes_quickguide|orchestration-log|MEMORY-L0\.md → |vantage|littlejohn|fern' . && echo "FAIL: internal artifacts"
```

## No real content

```bash
# No log or session files
find . -name '*.jsonl' -o -name '*.log' -o -name '*transcript*' -o -name '*session*' && echo "FAIL: logs/sessions"

# Memory dir must not exist in the template package (scaffolds live inside FULLINSTRUCTIONS.md as instructions only)
find . -path '*memory*' -type f && echo "FAIL: memory files in package"
```

Note: memory path *references* inside the instruction text (e.g. "memory/MEMORY-L0.md") are expected. The grep above finds actual files; the internal-artifact grep catches leaked references.

## Scaffolds only

- [ ] DECISIONS.md / ERRORS.md mentioned in instructions are format descriptions with example entries clearly marked as examples, no real decisions or mistakes
- [ ] USER.md is a scaffold with placeholders, no real person's data
- [ ] No dates from real sessions used as anything but format examples (YYYY-MM-DD)
- [ ] All example text reads as generic, not as thinly renamed reality

## Final pass

```bash
# Visual scan of every example entry
grep -rn '\*\*Evidence:\|\*\*Decision:\|\*\*What happened:' .

# Line counts for the report
wc -l *.md
```

Ship only when every grep above exits clean and the manual checks pass.
