# OpenAI plugin listing draft

Submission type: **Skills only**. No MCP server is included.

## Public listing

- **Name:** Grok Bot Control
- **Publisher handle used in repository materials:** ImL1s
- **Category:** Productivity
- **Short description:** Coordinate authorized Grok Bot conversations with send-once checks, evidence handoffs, and bounded follow-ups.

### Long description

Grok Bot Control is a portable, skills-only workflow plugin for reliable coordination with an authorized Grok Bot conversation from Codex, Claude Code, or Grok Build. It guides host capability assessment, exact target verification, preservation of unrelated drafts, reconciliation of uncertain sends before retrying, versioned evidence exchange, and bounded progress nudges. When callers provide a capability snapshot and run identifier, the optional capability preflight binds fresh tool evidence to the current run, target, and intent digest. The three Python helpers are deterministic, read-only advisory tools; they do not enforce a host runtime gate.

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

Version 0.2.0 shares one portable skill across Codex, Claude Code, and Grok Build. It adds an optional host capability preflight that, when supplied, binds fresh evidence to the run, target, and intent digest; keeps the single-writer, duplicate-send reconciliation, evidence handoff, and bounded nudge workflow; and supplies three read-only advisory helpers with reviewer-runnable synthetic cases. Platform packaging and release automation are included. Live use requires host-provided control tools and an authorized Grok Bot conversation; neither is bundled.

## Submission readiness gates

The repository prepares the materials that can be reviewed before portal submission. The publisher completes account-specific choices and attestations in the portal:

- **Developer identity:** select the eligible identity shown by OpenAI Platform; the GitHub handle alone does not establish eligibility.
- **Apps Management permission:** confirm the publishing organization permits the submission.
- **Logo:** prepared at `plugins/grok-bot-control/assets/logo.png` (512×512 PNG).
- **URLs:** proposed paths are listed above; they must be deployed and checked publicly.
- **Availability:** countries and regions remain a publisher decision after support and legal readiness are confirmed.
- **Policy attestations:** review and complete them in the portal for the final submitted package.

The structured version of this draft is [`listing-draft.json`](listing-draft.json). Test cases and their proof boundary are documented in [`TEST_CASES.md`](TEST_CASES.md).
