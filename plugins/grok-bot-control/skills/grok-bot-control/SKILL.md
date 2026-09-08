---
name: grok-bot-control
description: Coordinate with an authorized Grok Bot conversation through host UI tools or an optional pinned CLI adapter, read back handoffs, reconcile uncertain sends, and track bounded follow-ups. Use when the user asks an agent to work with or control Grok Bot. Installation does not grant account access or supply the external CLI or scheduler.
metadata:
  version: "0.3.0"
---

# Grok Bot control

Use the narrowest currently available surface. Start with the [host capability contract](references/host-adapters.md): identify the host, inspect its current tools, and verify the selected conversation from fresh state. A skill can describe a workflow but cannot grant tools. If the host exposes native computer control and the user selected the Mac Grok Bot app, follow [macOS CUA](references/macos-cua.md). If no supported surface exists, prepare a reviewable handoff and state the missing capability. Never invent a private endpoint or claim that this plugin includes an app, MCP server, login, or background service.

The third-party `grok-bot-cli` is an optional external backend. Read [CLI adapter](references/cli-adapter.md) and [CLI audit](references/cli-experimental.md) before use. The plugin includes only a thin subprocess adapter, never authentication or gateway code. Prefer it for the supported roster/read/send operations only after its pin and current target checks pass; retain UI for unsupported operations and independent verification. Installation, credentials, and sends must remain within the user's authorized scope.

For tasks that may use both CLI and UI, use one private `delivery.sqlite3`, one task scope, and the exact target ID and message digest across both paths. Read the journal before any UI send, reserve before activating Send, and confirm only from fresh outgoing-message readback. CLI uncertainty blocks UI retry even if a matching draft remains. The legacy UI-only state helper without journal arguments remains advisory and does not protect a separate CLI process.

## Reliable coordination loop

1. Read the current task record, the target conversation, and the latest substantive reply. Confirm the requested conversation, authorized work, output, constraints, and stop condition. Do not switch conversations based on position in the sidebar.
2. Prepare only the next useful delta. Identify the current operator, exact files or artifact hashes, what changed, how to verify it, and which external actions remain outside scope. Use the operator name supplied by the current host; do not assume `codex`, `claude`, or `grok` from the skill package.
3. Select one send path. For CLI, follow its pin, target, fresh baseline, and journal checks. For UI, read the composer and target conversation, preserve unrelated drafts, paste the complete message through the current tool's documented method, and read it back. Both paths reserve the shared journal before dispatch.
4. Send once. A CLI acknowledgement alone is insufficient; reconcile against fresh outgoing readback. For UI, a new matching outgoing message relative to the pre-send view plus an empty composer supports delivery. A matching draft does not override an uncertain journal record. If delivery remains ambiguous, record uncertainty and stop retries on both paths.
5. Treat an acknowledgement, a claimed PASS, artifact receipt, hash confirmation, deployment, and long-running health as separate evidence. Verify the actual files and fresh outputs required by the task.
6. When waiting is authorized, follow [coordination and waiting](references/coordination.md). Nudge only after checking for new progress. Finish by recording the accepted result and disabling task-specific tracking.

For routine editing, file exchange, computer-target selection, and skill installation handoffs, read [supported workflows](references/workflows.md). For installing or publishing across Codex, Claude Code, Grok Build, or another Agent Skills host, read [portability](references/portability.md).

## Boundaries

- Conversation-control authorization applies only to the user-selected conversation and task. It does not approve purchases, destructive changes, credential access, third-party messages, deployments, or other proposed actions.
- Reuse existing authorization for the same delegated task and target; do not ask again for routine progress reads, handoffs, or already-authorized follow-ups. Ask only when the next action lacks that scope or requires a new decision.
- Never store access tokens, login descriptors, Keychain values, raw private chats, account identifiers, one-time codes, host identifiers, or user-specific absolute paths in this plugin or ordinary handoff bundles.
- A tool error is not evidence that an action failed. A status label is not evidence that it succeeded. Read back the visible or file state.
- Keep one active sender for a coordination thread. State files document ownership but do not implement distributed locking.
- Use only APIs documented by the tool available in the current run. Reinitialize after a CUA session reset and rediscover dynamic accessibility indices every time.

## Included helper

Copy [coordination-state.json](assets/coordination-state.json) into a stable task directory. The helper is read-only:

```sh
python3 scripts/assess_wait.py /path/to/coordination.json
```

`nudge_due` is timing advice only. Hash its exact text and use the selected path's send gate and shared journal: the CLI adapter, or the `assess_send.py` UI-readback gate below.

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
