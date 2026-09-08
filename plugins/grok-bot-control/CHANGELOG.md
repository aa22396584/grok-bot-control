# Changelog

## 0.3.0

- Add an optional adapter for an independently installed, source-pinned Grok Bot CLI: offline compatibility check, live Bot roster and normalized transcript reads, explicit stdin send, and reconciliation.
- Reserve a shared local SQLite delivery record before dispatch; an uncertain result blocks a repeated CLI or journal-aware UI send. Confirm only new outgoing readback relative to the persisted baseline.
- Keep authentication and Gateway parsing in the CLI fork; do not bundle it, install it silently, or fall back to another send path.
- Bound child execution time and output, pass message text through stdin, remove credential and runtime-injection environment overrides, and redact child errors.
- Add synthetic transport, crash, concurrency, stale-readback, and subprocess fault tests. Publish the precise platform and live-evidence limits.

## 0.2.0

- Share one Agent Skill across Codex, Claude Code, and Grok Build with explicit host capability prerequisites.
- Generate platform manifests, catalogs, and matching skill versions from one release metadata file.
- Add an offline capability assessment and regression cases without connecting to live accounts.
- Check portable helpers and packages on Linux, macOS, and Windows; validate metadata, privacy boundaries, and release contents.
- Gate website deployments and tagged releases on the check suite, and build marketplace, plugin-root, and skills ZIPs with checksums.
- Document host installation evidence separately from live conversation-control evidence and official directory review.

## 0.1.0

- Initial Codex plugin, standalone skill bundle, static website, and synthetic reviewer cases.
- Add read-only send-state and bounded follow-up decision helpers.
