## Description:

Audit the whole repo for over-engineering. A ranked list of what to delete, simplify, or replace with stdlib or native features.

This skill is ready for commercial/non-commercial use.

## Publisher:

[dietrichgebert](https://clawhub.ai/user/dietrichgebert)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and engineers use this skill to audit an entire repository for unnecessary complexity, ranked by the largest opportunities to delete, simplify, or replace code with standard library or native platform features.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: A full-repository audit can place private source code into the agent's working context.

Mitigation: Use this skill only in repositories whose contents may be inspected by the agent, and review the ranked findings before acting on them.

## Reference(s):

- [Project homepage](https://github.com/DietrichGebert/ponytail)

## Skill Output:

**Output Type(s):** [Text, Markdown, Guidance]

**Output Format:** [Markdown text with ranked one-line findings and a summary line]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Read-only audit output; lists findings and does not apply changes.]

## Skill Version(s):

4.9.0 (source: server release metadata)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
