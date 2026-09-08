# Changelog

All notable changes to this plugin are documented here.

## 0.1.0 - 2026-09-08

- Add public-facing usage, installation, platform, capability, and product-boundary documentation.
- Add workflows for routines, file handoffs, computer targeting, and skill installation.
- Add bounded workflows for Bot lifecycle, notifications, taught tasks, connectors, and search/reply.
- Add portability and privacy checks for sharing the plugin.
- Add a read-only send-state guard with operator, uncertain-send, duplicate-send, and draft-recovery tests.
- Make due-nudge results timing-only and require the normal send gate before any nudge is pasted or sent.
- Record bounded third-party CLI list, JSON read, and single authorized send evidence without claiming retry idempotency or broad command support.

- Add the verified macOS CUA conversation workflow.
- Add clipboard-timeout reconciliation and duplicate-send safeguards.
- Add versioned artifact handoff and bounded progress-follow-up guidance.
- Add a read-only waiting-state helper and tests.
- Document the experimental `grok-bot-cli` path and its version-bound live evidence.

- Publish the MIT source, static website, policies, synthetic reviewer cases, and reproducible packages.
