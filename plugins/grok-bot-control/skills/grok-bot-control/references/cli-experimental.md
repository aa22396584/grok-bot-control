# Experimental `grok-bot-cli` path

Source reviewed on 2026-09-08 at commit `7f2c4987673d19770d557b6f82df4e0c43deb6e4` (package 0.2.2):

- https://github.com/ScriptedAlchemy/grok-bot-cli
- https://www.npmjs.com/package/grok-bot-cli

## What it could improve

The CLI exposes structured commands to list, create, update, and delete Bots and groups; send prompts; and read transcript tails or threads. If its live gateway remains compatible, `bots list`, `thread`, and `send` could replace fragile accessibility indices and offer cleaner read-before-send automation.

## How it authenticates

On macOS it reads `~/Library/Application Support/Grok Bot/gateway-descriptor.json`, calls `/usr/bin/security find-generic-password` for the `Grok Bot Safe Storage` Keychain item, decrypts the Electron Safe Storage payload, and uses its gateway URL, bearer token, and routing headers. Alternative environment variables accept gateway or Cursor access tokens. It then calls Cursor/Grok Bot gateway routes such as `/api/listAgents`, `/api/sendPrompt`, `/api/getAgentTranscriptTail`, and `/api/getAgentThread`; the access-token path calls `https://api2.cursor.sh/aiserver.v1.GrokBotService/EnsureSandBox` by default.

This is sensitive credential access and depends on internal, undocumented service routes. The repository is third-party and MIT licensed; it is not an official Grok Bot or Cursor API client. Compatibility, credential format, routing headers, rate limits, idempotency, and account safety are not covered by a public stability guarantee.

## Historical live proof

The repository was cloned read-only and its 24 offline Node tests passed. The source was inspected for commands, storage, authentication, and endpoint behavior. It was not installed globally.

On 2026-09-08, a separate operator ran the cloned CLI on macOS with Grok Bot 0.44.0 and Node 22.22.0. The operator used a restricted environment, captured results without echoing raw stderr or transcript text, and bounded each call. The unmodified upstream CLI successfully listed Bots, resolved one target, and returned six JSON thread entries in about one second. The patched fork at the commit below then sent exactly one uniquely tagged test message to an authorized conversation in about one second; the visible app showed it in the correct conversation, and Grok Bot replied 47 seconds later. Patched JSON and plain-text readback plus the app each showed one test message and the exact Bot reply. No target name, identifier, transcript, token, routing header, or test marker is retained here.

This historical run is **bounded live validation** for list, JSON thread read, and one authorized send on that exact version and account. It does not establish exactly-once delivery, retry idempotency, ambiguous-timeout safety, long-running compatibility, CRUD, groups, attachments, routines, connectors, or other CLI commands. The upstream plain formatter did not render the observed nested `message.content` schema correctly.

An optional patch was maintained in the `ImL1s/grok-bot-cli` fork at commit `379852d8037b71fe6835dfe8086b299a5b2610ed` and draft pull request [#1](https://github.com/ImL1s/grok-bot-cli/pull/1). At that historical commit it added bounded request/body handling, safe error reporting, and nested-message plain formatting; 43 offline tests passed. Current adapter compatibility is defined separately by `assets/cli-compatibility.json`, including the exact source commit and hashes. The fork is not bundled with this plugin and does not turn undocumented gateway routes into a supported public API.

## Current integration boundary

The included adapter calls only a separately reviewed, pinned source tree and exposes `check`, `bots`, `thread`, `send`, and `reconcile`. Its new integration tests are synthetic and offline until a current live roster/read/send evaluation is recorded. The validated environment remains macOS, Grok Bot 0.44.0, and Node 22. Offline `check` does not execute Node; the Node major, canonical app path, bundle identity, and app version are checked only after explicit live opt-in. Source hashes, bounded subprocess output, normalized transcript validation, stdin message transfer, and a shared delivery journal reduce known risks; they do not attest the running process or remote gateway and do not guarantee exactly-once delivery.

The baseline/new-ID reconciliation assumes stable IDs and a newest-message tail from the pinned endpoint. Normalized output does not independently prove chronology or ordering. Any new live smoke therefore establishes compatibility only for the specifically checked target, operation, versions, and observation window.

Use the CLI for only the operations and versions listed in [CLI adapter](cli-adapter.md). Keep UI available for unsupported operations, pre-send inspection, and independent readback. A CLI uncertainty record blocks UI retry. Absence from a bounded tail is not proof of non-delivery.

Before live adoption, perform a separate authorized evaluation in this order:

1. Pin a reviewed commit or package integrity value; do not install an unpinned moving target.
2. Review any source changes since the audited commit.
3. Run only offline help/tests first. A live `doctor` may access the app descriptor and Keychain, so treat it as credential access.
4. Reproduce roster discovery and JSON thread read with a restricted environment and captured output after any app or CLI update.
5. For any newly authorized send test, use one unique marker, one shared journal scope, and confirm it through both normalized readback and the visible app. Never retry an ambiguous send merely because the command timed out.
6. Keep the macOS CUA workflow available for unsupported operations and independent verification until version changes have their own evidence.

Do not add automatic send hooks or wrap these routes in an MCP server until that separate scope has been deliberately reviewed and tested.
