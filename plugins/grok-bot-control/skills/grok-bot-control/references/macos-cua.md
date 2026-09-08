# Verified macOS CUA workflow

Observed with the native Grok Bot macOS application on 2026-09-08. This is a platform adapter for the shared [host capability contract](host-adapters.md), not a bundled driver. Product UI and tool APIs can change; the documentation returned by the current CUA tool takes priority.

## Initialize and identify the target

On the first CUA call, follow the tool's single-entry-call rule. When the app is known, select it by the verified bundle identifier and read the returned UI state:

```javascript
let grokApp = await cua.getApp("com.anysphere.sand");
```

The plugin does not provide `cua`, `grokApp`, or access to the application. They exist only when the current host exposes the corresponding computer-use tool and the user has authorized the app interaction.

After a REPL reset, initialize again. Never reuse accessibility indices from an earlier snapshot. Read a fresh accessibility state and confirm the selected Bot, conversation title, recent messages, composer, and send button. Preserve unrelated drafts before switching conversations.

## Send one message reliably

1. Call the documented accessibility-state method and locate the current composer.
2. Click the composer. If it has text, identify whether it is the exact draft from this operation. Do not overwrite unrelated text.
3. Prefer the documented `paste(text, {format: "text"})` method for long or non-Latin text. Read the composer again and compare the complete draft.
4. Locate the send button in the fresh snapshot and activate it once.
5. Read state again. Record success only when the matching new message is visible and the composer is empty.

Accessibility indices change after replies, scrolling, focus changes, and window movement. Discover them again for each action.

## Timeout and duplicate-send matrix

The CUA runtime has returned a clipboard-read timeout even when the full draft reached the composer. Use state, not the exception alone:

| Readback | Action |
| --- | --- |
| Complete matching draft, no sent copy | Send once |
| Matching new sent message, empty composer | Mark sent; do not retry |
| No draft and no matching sent message | Reconfirm focus and target, then retry input once |
| Partial or mismatched draft | Preserve or repair only the operation-owned draft; do not send |
| State cannot distinguish sent from unsent | Record `uncertain_send`; stop automatic retries |

`typeText` has dropped non-Latin characters, and `setValue` or selection APIs have sometimes produced no visible result. Every input and update requires readback. If an operation-owned draft must be replaced, focus it, select all, paste the complete replacement, and read it back. Never apply that sequence to an unrelated user draft.

If the app reports no windows, one observed recovery was moving the visible window to the built-in display through the Window menu. This is a dated fallback, not a platform guarantee. Inspect current state before attempting it and avoid repeated window moves.

## Completion evidence

Separate these states in the task record:

- draft verified;
- message visibly sent;
- Bot replied;
- artifact received;
- artifact hash and tests verified;
- external effect completed.

Do not use a working indicator, timeout, acknowledgement, or truncated message node as a substitute for the required state.
