# Portability and publishing

The canonical workflow is `skills/grok-bot-control/`. Keep one copy of its instructions, references, scripts, tests, and assets. Platform manifests and marketplace catalogs should point to that same self-contained skill directory; do not maintain rewritten Codex, Claude, and Grok copies.

Codex uses its Codex plugin manifest and marketplace catalog. Claude Code uses a Claude plugin manifest and may distribute the same skill through a marketplace. Grok Build supports native plugins and Claude-compatible plugin discovery. Other Agent Skills hosts may load the skill directory directly. Packaging compatibility only makes the instructions discoverable: it does not provide CUA, MCP, terminal, account, network, or scheduler capabilities.

## Before packaging

1. Validate every platform manifest and the canonical skill.
2. Run all offline helper tests with bytecode generation disabled.
3. Scan for secrets and machine-specific data.
4. Search for absolute home/workspace paths, account or Bot identifiers, private conversation names, tokens, emails, phone numbers, and copied message text.
5. Generate a deterministic file manifest with relative paths and SHA-256 values.
6. Create each archive from a self-contained plugin root and inspect its member paths before publication. Do not use links that escape the package.

## Host adaptation

- macOS CUA is the currently exercised UI path. Every host must satisfy the [capability contract](host-adapters.md) and revalidate target selection, draft readback, send confirmation, and timeout behavior.
- The helper scripts use Python's standard library and do not need Grok credentials.
- Schedulers, file-transfer channels, Keychain, notification delivery, and third-party CLI authentication are external dependencies.
- Do not copy a personal marketplace entry into another user's configuration. The recipient installs from their own marketplace or repository source.
- Platform metadata can differ, but the skill name, release version, license, description, and bundled file hashes should be checked for consistency in CI.

## Versioning

Keep one human release version in release metadata and generate or validate platform versions from it. Host-specific development cache suffixes are local installation details and must not become the public skill version.

Publishing a ZIP, repository, marketplace entry, or announcement is a separate external action. Validate and prepare first; publish only through the destination and visibility authorized by the user. Acceptance by one platform does not imply acceptance or functional validation on another.
