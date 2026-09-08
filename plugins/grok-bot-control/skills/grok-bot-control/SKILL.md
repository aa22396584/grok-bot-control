---
name: grok-bot-control
description: Coordinate directly with an authorized Grok Bot conversation, send verified handoffs, read back outcomes, prevent duplicate sends after UI timeouts, and track bounded follow-ups. Use when the user asks an agent to work with or control Grok Bot. This skill supplies workflow knowledge only; it does not grant UI, account, credential, API, or scheduler access.
metadata:
  version: "0.2.0"
---

# Grok Bot control

Use the narrowest currently available surface. Start with the [host capability contract](references/host-adapters.md): identify the host, inspect its current tools, and verify the selected conversation from fresh state. A skill can describe a workflow but cannot grant tools. If the host exposes native computer control and the user selected the Mac Grok Bot app, follow [macOS CUA](references/macos-cua.md). If no supported surface exists, prepare a reviewable handoff and state the missing capability. Never invent a private endpoint or claim that this plugin includes an app, MCP server, login, or background service.

The third-party `grok-bot-cli` is an optional experimental path. Read [CLI audit](references/cli-experimental.md) before proposing or using it. Its source review does not authorize installation, Keychain access, live API calls, or message sends.

## Reliable coordination loop

1. Read the current task record, the target conversation, and the latest substantive reply. Confirm the requested conversation, authorized work, output, constraints, and stop condition. Do not switch conversations based on position in the sidebar.
2. Prepare only the next useful delta. Identify the current operator, exact files or artifact hashes, what changed, how to verify it, and which external actions remain outside scope. Use the operator name supplied by the current host; do not assume `codex`, `claude`, or `grok` from the skill package.
3. Before sending, read the composer and target conversation. Preserve unrelated drafts. Paste the complete message with the current tool's documented text-paste method, then read it back.
4. Send once. After any timeout or ambiguous result, inspect the conversation and composer before retrying. A new matching message plus an empty composer means sent. A matching draft means do not paste again. If neither state can be established, record `uncertain_send` and stop retries.
5. Treat an acknowledgement, a claimed PASS, artifact receipt, hash confirmation, deployment, and long-running health as separate evidence. Verify the actual files and fresh outputs required by the task.
6. When waiting is authorized, follow [coordination and waiting](references/coordination.md). Nudge only after checking for new progress. Finish by recording the accepted result and disabling task-specific tracking.

For routine editing, file exchange, computer-target selection, and skill installation handoffs, read [supported workflows](references/workflows.md). For installing or publishing across Codex, Claude Code, Grok Build, or another Agent Skills host, read [portability](references/portability.md).

## Boundaries

- Conversation-control authorization applies only to the user-selected conversation and task. It does not approve purchases, destructive changes, credential access, third-party messages, deployments, or other proposed actions.
- Never store access tokens, login descriptors, Keychain values, raw private chats, account identifiers, one-time codes, host identifiers, or user-specific absolute paths in this plugin or ordinary handoff bundles.
- A tool error is not evidence that an action failed. A status label is not evidence that it succeeded. Read back the visible or file state.
- Keep one active sender for a coordination thread. State files document ownership but do not implement distributed locking.
- Use only APIs documented by the tool available in the current run. Reinitialize after a CUA session reset and rediscover dynamic accessibility indices every time.

## Included helper

Copy [coordination-state.json](assets/coordination-state.json) into a stable task directory. The helper is read-only:

```sh
python3 scripts/assess_wait.py /path/to/coordination.json
```

`nudge_due` is timing advice only. Before pasting or sending the nudge, hash its exact text and run it through the same `assess_send.py` UI-readback gate below.

It returns timing advice only. It never opens Grok Bot, sends a message, edits state, or creates a schedule.

Before a UI send, the second read-only helper checks the recorded operator, message digest, uncertain-send state, and current observation:

```sh
python3 scripts/assess_send.py /path/to/coordination.json \
  --operator current-agent \
  --message-sha256 "$MESSAGE_SHA256" \
  --observation matching-draft-only \
  --capabilities /path/to/capabilities.json \
  --run-id "$RUN_ID"
```

Its output is advice such as `paste_once`, `send_once`, `mark_sent`, `inspect`, or `stop`. The caller still has to read the current UI and update state after a confirmed action.
Replace `current-agent` with the non-secret operator label recorded in the task state.

Before using either helper, the optional capability preflight can evaluate a caller-recorded snapshot:

```sh
python3 scripts/assess_capabilities.py /path/to/capabilities.json \
  --run-id "$RUN_ID" \
  --operator current-agent \
  --conversation "$CONVERSATION_ALIAS" \
  --message-sha256 "$MESSAGE_SHA256"
```

Pass the current run ID, operator, conversation alias, and exact message SHA-256 as described in [the capability contract](references/host-adapters.md). It does not discover tools. `ready_for_send_gate` means the recorded capabilities and fresh target evidence are sufficient to continue to `assess_send.py`; it is not proof that a send occurred, that the supplied snapshot is truthful, or that authorization exists.

The capability file is optional for backward-compatible use. When it is omitted, perform and record the same current target, tool, draft, and sent-state checks manually before using a send action.
