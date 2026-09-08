# Portability and publishing

The shareable unit is the plugin root containing `.codex-plugin/plugin.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, and `skills/`. Do not package the personal marketplace file, installed cache, task state, transcripts, credentials, or machine-specific launch configuration.

## Before packaging

1. Validate the plugin manifest and every skill.
2. Run all offline helper tests with bytecode generation disabled.
3. Scan for secrets and machine-specific data.
4. Search for absolute home/workspace paths, account or Bot identifiers, private conversation names, tokens, emails, phone numbers, and copied message text.
5. Generate a deterministic file manifest with relative paths and SHA-256 values.
6. Create the archive from the plugin root and inspect its member paths before publication.

## Host adaptation

- macOS CUA is the currently exercised UI path. Other hosts must provide a supported surface and revalidate target selection, draft readback, send confirmation, and timeout behavior.
- The helper scripts use Python's standard library and do not need Grok credentials.
- Schedulers, file-transfer channels, Keychain, notification delivery, and third-party CLI authentication are external dependencies.
- Do not copy a personal marketplace entry into another user's configuration. The recipient installs from their own marketplace or repository source.

## Versioning

Keep a human release version in the changelog. During local Codex iteration, use the plugin creator's single cachebuster suffix and reinstall from the existing marketplace. Replace the old suffix instead of stacking suffixes. Create one final cachebuster after release content and CLI evidence are frozen.

Publishing a ZIP, repository, marketplace entry, or announcement is a separate external action. Validate and prepare first; publish only through the destination and visibility authorized by the user. Cursor marketplace publication has its own review and organization policy, and this Codex plugin should not be presented as already accepted there.
