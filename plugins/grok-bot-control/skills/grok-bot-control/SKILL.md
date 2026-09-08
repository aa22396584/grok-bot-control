---
name: grok-bot-control
description: Coordinate directly with an authorized Grok Bot conversation, send verified handoffs, read back outcomes, prevent duplicate sends after UI timeouts, and track bounded follow-ups. Use when the user asks Codex to work with or control Grok Bot. This skill supplies workflow knowledge only; it does not grant UI, account, credential, API, or scheduler access.
metadata:
  version: "1.0.0"
---

# Grok Bot control

Use the narrowest currently available surface. If the host exposes native computer control and the user selected the Mac Grok Bot app, follow [macOS CUA](references/macos-cua.md). If no supported surface exists, prepare a reviewable handoff and state the missing capability. Never invent a private endpoint or claim that this plugin includes an app, MCP server, login, or background service.

The third-party `grok-bot-cli` is an optional experimental path. Read [CLI audit](references/cli-experimental.md) before proposing or using it. Its source review does not authorize installation, Keychain access, live API calls, or message sends.

## Reliable coordination loop

1. Read the current task record, the target conversation, and the latest substantive reply. Confirm the requested conversation, authorized work, output, constraints, and stop condition. Do not switch conversations based on position in the sidebar.
2. Prepare only the next useful delta. Identify the current operator, exact files or artifact hashes, what changed, how to verify it, and which external actions remain outside scope.
3. Before sending, read the composer and target conversation. Preserve unrelated drafts. Paste the complete message with the current tool's documented text-paste method, then read it back.
4. Send once. After any timeout or ambiguous result, inspect the conversation and composer before retrying. A new matching message plus an empty composer means sent. A matching draft means do not paste again. If neither state can be established, record `uncertain_send` and stop retries.
5. Treat an acknowledgement, a claimed PASS, artifact receipt, hash confirmation, deployment, and long-running health as separate evidence. Verify the actual files and fresh outputs required by the task.
6. When waiting is authorized, follow [coordination and waiting](references/coordination.md). Nudge only after checking for new progress. Finish by recording the accepted result and disabling task-specific tracking.

For routine editing, file exchange, computer-target selection, and skill installation handoffs, read [supported workflows](references/workflows.md). For moving the plugin between hosts or publishing it, read [portability](references/portability.md).

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
  --operator codex \
  --message-sha256 "$MESSAGE_SHA256" \
  --observation matching-draft-only
```

Its output is advice such as `paste_once`, `send_once`, `mark_sent`, `inspect`, or `stop`. The caller still has to read the current UI and update state after a confirmed action.
