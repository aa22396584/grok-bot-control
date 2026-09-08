# OpenAI plugin listing draft

Submission type: **Skills only**. No MCP server is included.

## Public listing

- **Name:** Grok Bot Control
- **Publisher handle used in repository materials:** ImL1s
- **Category:** Productivity
- **Short description:** Coordinate authorized Grok Bot conversations with send-once checks, evidence handoffs, and bounded follow-ups.

### Long description

Grok Bot Control is a skills-only workflow plugin for reliable coordination with an authorized Grok Bot conversation. It guides exact target verification, preserves unrelated drafts, reconciles uncertain sends before retrying, exchanges versioned evidence, and applies bounded progress nudges. Included Python helpers provide deterministic, read-only advice from synthetic or user-maintained coordination state.

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

Initial skills-only submission. Adds a documented single-writer coordination workflow, duplicate-send reconciliation, evidence-based handoffs, bounded nudge guidance, two read-only offline helpers, and reviewer-runnable synthetic cases. Live use requires a host-provided computer-use surface and the reviewer's already signed-in Grok Bot account; neither is bundled.

## Submission readiness gates

The repository is intentionally honest about fields that cannot be completed locally:

- **Developer identity:** UNKNOWN. Select an identity that OpenAI Platform shows as verified; the GitHub handle alone does not establish this.
- **Apps Management permission:** must be verified in the publishing organization.
- **Logo:** prepared at `plugins/grok-bot-control/assets/logo.png` (512×512 PNG).
- **URLs:** proposed paths are listed above; they must be deployed and checked publicly.
- **Availability:** countries and regions remain a publisher decision after support and legal readiness are confirmed.
- **Policy attestations:** intentionally incomplete; the publisher must review and attest in the portal.

The structured version of this draft is [`listing-draft.json`](listing-draft.json). Test cases and their proof boundary are documented in [`TEST_CASES.md`](TEST_CASES.md).
