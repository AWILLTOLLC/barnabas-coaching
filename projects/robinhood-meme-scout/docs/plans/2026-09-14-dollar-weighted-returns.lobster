name: build-runner
description: Execute a prose build plan via Lobster with managed Task Flow
args:
  plan_path:
    type: string
    description: Absolute path to the prose build plan markdown file
steps:
  - id: stage-1
    command: python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/2026-09-14-dollar-weighted-returns.md 1

  - id: stage-2
    command: python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/2026-09-14-dollar-weighted-returns.md 2

  - id: preview-3
    command: 'echo "Side effect stage - see plan for action details"'

  - id: stage-3
    command: python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/2026-09-14-dollar-weighted-returns.md 3
    approval: required

  - id: stage-4
    command: python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/projects/robinhood-meme-scout/docs/plans/2026-09-14-dollar-weighted-returns.md 4
    condition: $stage-3.approved

  - id: complete
    command: 'echo "Build complete - all stages passed"'
    condition: $stage-3.approved