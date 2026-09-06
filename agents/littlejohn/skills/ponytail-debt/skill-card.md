## Description:

Harvests ponytail shortcut comments into a debt ledger so deliberate deferrals stay visible instead of being forgotten.

This skill is ready for commercial/non-commercial use.

## Publisher:

[dietrichgebert](https://clawhub.ai/user/dietrichgebert)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and maintainers use this skill to scan a repository for `ponytail:` debt markers and turn matching comments into a concise ledger with file locations, ceilings, upgrade triggers, and no-trigger counts.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Repository comments may contain sensitive implementation details that appear in the generated ledger.

Mitigation: Run the skill only where showing matching source comments is acceptable, and review the report before sharing it.

Risk: Persisting the ledger writes a file when explicitly requested.

Mitigation: Confirm the destination and generated content before asking the agent to save a ledger file.

## Reference(s):

- [Project homepage](https://github.com/DietrichGebert/ponytail)
- [ClawHub skill page](https://clawhub.ai/dietrichgebert/skills/ponytail-debt)

## Skill Output:

**Output Type(s):** [text, markdown, shell commands, guidance]

**Output Format:** [Markdown-style ledger with file and line references]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [One-shot report; optional ledger file only when explicitly requested.]

## Skill Version(s):

4.9.0 (source: server release evidence)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
