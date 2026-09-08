# OpenAI plugin listing draft

Submission type: **Skills only**. No MCP server is included.

## Public listing

- **Name:** Grok Bot Control
- **Publisher handle used in repository materials:** ImL1s
- **Category:** Productivity
- **Short description:** Coordinate authorized Grok Bot conversations with send-once checks, evidence handoffs, and bounded follow-ups.

### Long description

Grok Bot Control is a portable workflow plugin for authorized Grok Bot coordination from Codex, Claude Code, or Grok Build. It provides target and draft verification, uncertainty reconciliation, evidence handoffs, bounded follow-ups, three read-only assessment helpers, a local delivery journal, and an optional source-pinned CLI adapter. Live reads and sends require explicit opt-in and a separately installed compatible CLI with an authorized app session. The adapter keeps message text out of argv and never retries an ambiguous send or switches to UI to resend. The journal protects callers using the same local file and logical operation scope; it is not a distributed lock. Authentication and Gateway parsing stay in the independent CLI. No Grok Bot app, credentials, MCP server, computer-use backend, scheduler, or background service is bundled.

The plugin does not include Grok Bot, credentials, an MCP server, a computer-use backend, a scheduler, or a background service.

## Proposed public URLs

- Website: <https://iml1s.github.io/grok-bot-control/>
- Support: <https://iml1s.github.io/grok-bot-control/support/>
- Privacy: <https://iml1s.github.io/grok-bot-control/privacy/>
- Terms: <https://iml1s.github.io/grok-bot-control/terms/>

All four URLs must be publicly reachable and match the selected verified publisher identity before submission.

## Starter prompts

1. Use Grok Bot Control to send this reviewed handoff to my authorized Bot and verify it appears once.
2. A send timed out. Inspect the conversation and composer before deciding whether any retry is safe.
3. Review the latest Bot reply and returned evidence, then check whether a follow-up is due.

## Release notes

Version 0.3.0 adds an optional thin CLI adapter for Bot roster, normalized transcript reads, explicit stdin sends, and readback reconciliation. A shared SQLite delivery journal reserves before dispatch and blocks uncertain repeats across CLI and UI workflows. Source files and tested versions are pinned; CLI subprocess time and output are bounded. Offline fault tests cover stale and uncertain readback, concurrent reservation, crash persistence, input handling, and child termination. Live compatibility evidence is stated separately in the repository.

## Submission readiness gates

The repository prepares the materials that can be reviewed before portal submission. The publisher completes account-specific choices and attestations in the portal:

- **Developer identity:** select the eligible identity shown by OpenAI Platform; the GitHub handle alone does not establish eligibility.
- **Apps Management permission:** confirm the publishing organization permits the submission.
- **Logo:** prepared at `plugins/grok-bot-control/assets/logo.png` (512×512 PNG).
- **URLs:** proposed paths are listed above; they must be deployed and checked publicly.
- **Availability:** countries and regions remain a publisher decision after support and legal readiness are confirmed.
- **Policy attestations:** review and complete them in the portal for the final submitted package.

The structured version of this draft is [`listing-draft.json`](listing-draft.json). Test cases and their proof boundary are documented in [`TEST_CASES.md`](TEST_CASES.md).
