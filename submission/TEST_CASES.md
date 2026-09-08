# Submission test cases

These reviewer-runnable cases support the **Skills only** submission. They follow OpenAI's requirement for at least five positive and three negative cases, with a user prompt, expected workflow, expected result shape, and reproducible fixture data.

The machine-readable source is [`test_cases.json`](test_cases.json). Synthetic state is in [`fixture_states.json`](fixture_states.json).

## Run locally

From the repository root:

```sh
python3 scripts/run_review_cases.py
```

The runner uses only the Python standard library. It imports the final plugin helpers from `plugins/grok-bot-control/skills/grok-bot-control/scripts`, performs no network or UI calls, and verifies that every fixture remains unchanged.

## Positive cases

| ID | Prompt intent | Expected behavior |
| --- | --- | --- |
| `positive-draft-paste-advice` | Prepare a reviewed handoff safely | Advise `paste_once` while the exact message is absent in a claimed drafting phase |
| `positive-visible-message-reconcile` | Reconcile a timed-out send | Advise `mark_sent` when the exact message is freshly visible, without retrying |
| `positive-progress-delays-nudge` | Respect recent Bot progress | Advise `wait` and return the next UTC check time |
| `positive-bounded-nudge-due` | Check a stalled Bot after the delay | Advise `nudge_due` while still below the configured cap |
| `positive-completed-task-stops` | Close completed coordination | Advise `stop` for the terminal phase |

## Negative cases

| ID | Unsafe or incomplete request | Expected safe fallback | Why it must not complete |
| --- | --- | --- | --- |
| `negative-wrong-operator` | Send while another operator owns the record | `stop` | A second writer could create conflicting or duplicate sends |
| `negative-different-uncertain-send` | Send new content before resolving a prior uncertain result | `inspect` | The earlier external effect remains unknown |
| `negative-already-acknowledged` | Resend an acknowledged digest | `stop` | The resend would duplicate an external message |
| `negative-blank-target` | Send without an exact conversation | `inspect` | The destination cannot be established |

## Evidence boundary

These cases prove deterministic offline advice and fixture immutability. They do **not** prove that Grok Bot is installed, that a user is authenticated, that a host exposes computer-use tooling, or that a message reached a live conversation.

The maintainer separately completed one bounded macOS check using an already signed-in account: list Bots, read one authorized conversation, send one uniquely tagged no-tool echo, and read back the marker and Bot reply. That evidence is environment-specific. It does not prove cross-platform UI compatibility, background operation, scheduling, or exactly-once delivery under every failure mode.

A reviewer who wants to exercise the live workflow needs:

- A supported host computer-use tool.
- The macOS Grok Bot app already signed in to the reviewer's own test account.
- An authorized test conversation with no unrelated draft.
- Permission to send one harmless, uniquely tagged echo.

No account, credentials, conversation identifiers, or private transcript are bundled.
