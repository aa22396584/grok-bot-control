# Host capability contract

This skill uses host-provided tools. Codex, Claude Code, Grok Build, and other Agent Skills hosts may expose different tool names and permission models. Do not translate a tool name by guesswork or treat skill installation as tool access.

## Required observations

Before a live send, establish all of these from the current run:

| Capability | Minimum evidence |
| --- | --- |
| Read the current conversation | Fresh state readback |
| Read the current composer | Fresh state readback |
| Write the composer | Current tool documentation |
| Activate send once | Current tool documentation |
| Read sent messages | Fresh state readback |
| Identify the selected conversation | Fresh target readback matching the user's target |

Also record the current operator and the user's authorization for the target and message. Authorization is not a tool capability, and the offline helper cannot verify it.

If reading works but any write or send capability is absent, use the host for review and prepare a handoff for an authorized operator. If target identity or fresh readback is unavailable, stop at inspection. A filesystem, terminal, browser, MCP, or CUA tool can only support the operations described by its current documentation.

## Offline preflight

Copy this shape into a task-local file; do not put account identifiers or private conversation text in it:

```json
{
  "schema_version": 1,
  "observed_at": "<CURRENT_TIME_WITH_TIMEZONE>",
  "run_id": "<CURRENT_RUN_ID>",
  "intent": {
    "operator": "<CURRENT_AGENT>",
    "conversation": "<REVIEW_SAFE_CONVERSATION_ALIAS>",
    "message_sha256": "<LOWERCASE_SHA256_OF_EXACT_MESSAGE>"
  },
  "target_identity": {
    "confirmed": true,
    "evidence": "fresh_target_readback"
  },
  "send_authorized": true,
  "capabilities": {
    "read_conversation": {"available": true, "evidence": "fresh_state_readback"},
    "read_composer": {"available": true, "evidence": "fresh_state_readback"},
    "write_composer": {"available": true, "evidence": "current_tool_docs"},
    "activate_send": {"available": true, "evidence": "current_tool_docs"},
    "read_sent_state": {"available": true, "evidence": "fresh_state_readback"}
  }
}
```

Replace every angle-bracket value with a current, non-secret value. `observed_at` expires after five minutes and future timestamps are rejected. `send_authorized` records the caller's understanding of authorization for that exact operator, conversation, and message digest; it does not grant rights or prove authorization.

Run the preflight with the same current scope:

```sh
python3 scripts/assess_capabilities.py capabilities.json \
  --run-id "$RUN_ID" \
  --operator "$CURRENT_AGENT" \
  --conversation "$CONVERSATION_ALIAS" \
  --message-sha256 "$MESSAGE_SHA256"
```

Its result is a deterministic decision over the supplied snapshot, not a live probe. Available capabilities with `unknown` evidence are not accepted. After a ready result, bind the same snapshot and run ID into `assess_send.py`; that helper rechecks the operator, conversation, and message digest before returning any send action.

## Platform adapters

- **Codex:** use its installed skill/plugin discovery and whatever CUA, browser, terminal, or connector tools are actually present. `agents/openai.yaml` only controls Codex-facing presentation and invocation.
- **Claude Code:** use the same `skills/grok-bot-control` directory through a Claude plugin or Agent Skills discovery. Re-evaluate tool names, permissions, and UI methods from the current Claude Code environment.
- **Grok Build:** load the skill through its native or Claude-compatible plugin discovery. Grok Build documents that skill fields do not grant tools; inspect the current tool set before choosing an adapter.
- **Other hosts:** Agent Skills compatibility can make the instructions discoverable. It does not establish Grok Bot access, UI parity, or permission parity.

The detailed [macOS CUA workflow](macos-cua.md) is one exercised adapter. The [experimental CLI path](cli-experimental.md) remains a separate, version-bound option rather than a universal adapter.

## Optional CLI capability

The [CLI adapter](cli-adapter.md) is available only when the current host has the separately reviewed source at its pinned hashes, an explicit absolute Node path, the validated macOS Grok Bot app bundle, and current authorization for any live operation. The pure offline `check` proves only listed source-file hashes and that the supplied Node path is an absolute existing file; it does not execute that runtime. Live access additionally checks the pinned Node major, `/Applications/Grok Bot.app`, bundle ID `com.anysphere.sand`, and the pinned app version before the external CLI can use the app session. These local checks are not runtime or remote gateway attestation.

For CLI and UI sends to the same target, capability readiness also requires access to one private local delivery journal. Inspect it before composing or sending, reserve the exact target/scope/message digest before Send, and confirm only from fresh unambiguous outgoing UI readback compared with the pre-send snapshot. UI baseline IDs are optional because native surfaces may not expose them; without them, CLI reconciliation stays uncertain and the original UI operator must confirm visually. Reuse the same unique operation scope during reconciliation. The CLI baseline/new-ID check assumes stable IDs and a newest-message tail; it does not independently prove chronology. Any `uncertain` record blocks both transports; UI is not an automatic retry path.
