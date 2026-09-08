# Security policy

## Scope

This plugin contains workflow instructions and read-only offline helpers. It does not contain credentials, an API service, an MCP server, a scheduler, a computer-use driver, or the third-party `grok-bot-cli` client.

Security-sensitive behavior includes target selection, draft preservation, duplicate-send prevention, operator ownership, artifact extraction, and any optional use of a signed-in app or third-party CLI.

## Reporting

Use [GitHub private vulnerability reporting](https://github.com/ImL1s/grok-bot-control/security/advisories/new) for a suspected vulnerability. Include the plugin version, affected file, minimal reproduction, and expected versus observed behavior. Do not include access tokens, gateway descriptors, routing headers, Keychain output, passwords, one-time codes, private transcripts, account identifiers, or real customer data.

If no private maintainer channel is available, open a public issue containing only a redacted description and ask for a private reporting route.

## Operational rules

- Review plugin and optional CLI source before installation or update.
- Keep one sender for a conversation and reconcile uncertain sends before retrying.
- Treat local state as advisory; it is not a distributed lock.
- Keep credentials in the product or operating-system credential store.
- Use synthetic, announced tests and verify recipient-side effects independently.
- Do not depend on undocumented gateway routes for destructive or high-impact work.

Supported-version and disclosure timelines are not promised for this community plugin. Maintainers should acknowledge a complete private report before publishing details.
