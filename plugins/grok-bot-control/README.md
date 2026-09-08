# Grok Bot Control

A portable Agent Skills workflow for reliable, reviewable coordination with a Grok Bot conversation. It captures a macOS computer-use procedure exercised in practice and supplies the same core rules to Codex, Claude Code, Grok Build, and compatible skill hosts: identify the exact conversation, preserve unrelated drafts, read back pasted text, send once, and reconcile timeouts before retrying.

This plugin contains instructions and offline state helpers. It does not bundle Grok Bot, a computer-use driver, an MCP server, account credentials, or an unofficial API client.

## What it helps with

| Plugin capability | Requirement | Evidence level |
| --- | --- | --- |
| Operate a native Grok Bot conversation | Host-provided CUA or equivalent tool, signed-in app, user authorization | Exercised on macOS; other hosts require their own evidence |
| Prevent duplicate sends after UI timeouts | Fresh UI readback plus coordination state | Exercised workflow; offline decision tests included |
| Exchange versioned files and verify returned artifacts | A transfer path available to both operators | Workflow documented; transport is host-specific |
| Track progress and bounded nudges | Stable state file; optional host scheduler | Offline helper tested; scheduler is not included |
| Edit routines or installed skills | Current UI/tool support and explicit task scope | Documented workflow; verify each saved result in the target UI |
| Manage Bots, notification settings, taught tasks, connectors, or search/reply | Current Grok Bot UI/tool support and task-specific authorization | Documented workflow only; product actions are not implemented by this plugin |
| Use `grok-bot-cli` | Separately reviewed third-party CLI and credential authorization | Bounded live list/read/send proof is version-bound; see the experimental reference |

## Grok Bot product capabilities versus this plugin

Grok Bot itself supports direct Bot chats, multi-Bot groups, mentions and asynchronous Bot handoffs, attachments, shared cloud-computer state, skills, routines, and notifications. This plugin coordinates some of those features through tools already available to the current host; it does not reimplement or grant them.

| Grok Bot feature | What this plugin contributes |
| --- | --- |
| Direct and group conversations | Target verification, single-writer guidance, draft/readback rules |
| Attachments and shared workspace files | Version/hash handoff and archive-review procedure; no transport |
| Skills and routines | Save/reopen/verify workflow; no installer or scheduler |
| Computer and app access | Live-target verification and proof boundaries; no remote-control backend |
| Notifications | Delivery-proof checklist; no push provider |
| Bot/profile lifecycle, connectors, and taught tasks | Target, authorization, readback, and evidence gates; no lifecycle or login backend |

Current official references: [work](https://cursor.com/docs/grok-bot/work), [settings](https://cursor.com/docs/grok-bot/settings), [security](https://cursor.com/docs/grok-bot/security), and [plugins](https://cursor.com/docs/plugins).

## Requirements

- Agent Skills or a supported Codex, Claude Code, or Grok Build plugin loader.
- A host tool that can reach the selected Grok Bot surface. The verified path uses a macOS CUA tool and an already signed-in Grok Bot app.
- Explicit authorization for the target conversation and requested external effects.
- A stable task directory for `coordination.json` when work spans turns or operators.

Installing this plugin grants no Grok Bot access. The current host still controls app permissions, account access, scheduling, filesystem access, and external writes.

## Install

The release keeps one canonical `skills/grok-bot-control` directory. Platform manifests make that skill discoverable but do not change its capabilities.

### Codex

Install the public repository marketplace:

```sh
codex plugin marketplace add ImL1s/grok-bot-control
codex plugin add grok-bot-control@grok-bot-control-local
```

For a downloaded marketplace ZIP, extract it and use its directory instead of the GitHub repository in the first command.

Start a new Codex thread after installation or update. Local developers should use Codex's plugin scaffold/cachebuster workflow instead of editing an installed cache.

### Claude Code and Grok Build

Install the repository through the host's supported plugin or marketplace command. Claude Code uses the Claude plugin manifest; Grok Build can use its native plugin discovery or Claude-compatible form. Inspect the installed skill and run its offline tests after installation. Current command syntax and trust prompts come from the host's documentation, not this workflow.

For a host that implements Agent Skills without plugin marketplaces, install the self-contained `skills/grok-bot-control` directory in that host's documented skill location.

## Use

Ask the current agent to use `$grok-bot-control` and name the authorized Bot/conversation and desired result. Examples:

- “Use `$grok-bot-control` to send this reviewed handoff and verify that it appears once.”
- “Check the latest reply, validate the returned archive and tests, then continue the same task.”
- “Use the coordination state to decide whether a progress nudge is due.”

For a long-running task, copy the state template:

```sh
cp skills/grok-bot-control/assets/coordination-state.json /path/to/task/coordination.json
```

The offline helpers never operate the UI. Run them from the skill directory so their relative paths resolve:

```sh
cd skills/grok-bot-control
python3 scripts/assess_wait.py /path/to/task/coordination.json
python3 scripts/assess_capabilities.py /path/to/task/capabilities.json \
  --run-id "$RUN_ID" --operator current-agent \
  --conversation "$CONVERSATION_ALIAS" --message-sha256 "$MESSAGE_SHA256"
python3 scripts/assess_send.py /path/to/task/coordination.json \
  --operator current-agent --message-sha256 "$MESSAGE_SHA256" \
  --observation matching-draft-only \
  --capabilities /path/to/task/capabilities.json --run-id "$RUN_ID"
```

Replace `current-agent` with the same non-secret operator label recorded in the task state. See [the capability contract](skills/grok-bot-control/references/host-adapters.md) for the current, intent-scoped preflight snapshot shape. A snapshot expires after five minutes and never grants authorization. The capability arguments remain optional for legacy use, which requires the equivalent current UI checks to be performed manually.

## Safety model

- One recorded operator writes to a conversation at a time. The state file detects mismatches but is not a distributed lock.
- A timeout is reconciled against fresh UI state. Unknown send state blocks automatic retry.
- Target conversation, message digest, artifact digest, and evidence level remain distinct.
- Destructive commands, purchases, deployments, credential access, and third-party messages require their own authorization.
- No account IDs, conversation text, tokens, private paths, or credentials belong in the plugin.

## Platform and publishing limits

The native CUA procedure was exercised on macOS. Other agent hosts, desktop platforms, browser variants, CLI auth methods, and schedulers require their own current tools and verification. Accessibility indices and UI layouts are dynamic. The offline capability helper evaluates a supplied snapshot; it does not probe a host or prove its claims.

This can be shared as a **portable coordination workflow with an exercised Codex/macOS CUA adapter**. It is not an official Grok API, a universal Grok controller, or a background resident service. Installation or marketplace acceptance on one host does not prove that another host has the required tools or that its live adapter works.

See the skill references for exact readback rules, workflows, portability, and the third-party CLI audit.
