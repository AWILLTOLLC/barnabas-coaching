## Description:

Review a diff for over-engineering. Finds what to delete: reinvented stdlib, needless deps, speculative abstractions. One line per finding.

This skill is ready for commercial/non-commercial use.

## Publisher:

[dietrichgebert](https://clawhub.ai/user/dietrichgebert)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and engineers use this skill to review code diffs for unnecessary complexity and identify concise deletion or simplification opportunities.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: The skill intentionally excludes correctness, security, and performance review.

Mitigation: Use it only for over-engineering review and route correctness, security, and performance concerns to a normal review pass.

Risk: The skill produces review guidance but does not apply or verify code changes.

Mitigation: Have a reviewer validate each proposed deletion or simplification before making changes.

## Reference(s):

- [ClawHub skill page](https://clawhub.ai/dietrichgebert/skills/ponytail-review)
- [Project homepage](https://github.com/DietrichGebert/ponytail)

## Skill Output:

**Output Type(s):** [Analysis, Guidance, Markdown]

**Output Format:** [Markdown text with one-line findings and an optional net line count summary]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Does not apply fixes; limits review scope to over-engineering and complexity.]

## Skill Version(s):

4.9.0 (source: server release metadata)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
