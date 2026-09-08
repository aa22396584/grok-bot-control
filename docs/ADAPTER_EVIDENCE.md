# Optional adapter evidence — 2026-09-08

## Offline behavior

The plugin tests use synthetic targets and local subprocess fixtures. They cover a timeout after an actual mock dispatch, acknowledgement without readback, stale identical text, assistant echoes, wrong or ambiguous targets, persisted uncertainty, concurrent journal reservations, relative-path refusal, source mismatches, stdin handling, bounded child output and deadlines, and redacted errors. The existing UI decision cases remain unchanged and run separately. No real Grok or Telegram credentials are used by CI.

## Bounded macOS exercise

On macOS, Node 22.22.0 and Grok Bot 0.44.0 were used with the independent CLI at commit `70a3729e90f3f20c26f4f0fa1cb401cab99ebaa6`. The adapter verified its source pin, read the live Bot roster, matched the intended Bot by ID and name, and read a 50-message normalized tail. All entries in that observed tail had IDs.

One uniquely marked test asked the Bot only to echo its marker, with no tool, file, Telegram, or scheduler actions. The adapter reserved the journal before dispatch, sent once through stdin, then confirmed exactly one new outgoing user entry relative to the saved baseline. The native macOS app independently displayed that outgoing message and the exact echo in a Bot-authored bubble. There was no automatic resend or UI send fallback.

The raw API represents some Bot replies as a `send-message` event with a nested text payload rather than an explicit assistant role. Those entries remain `unknown` in the normalized contract. Seeing the exact reply text is insufficient to infer its author from that API alone; the native UI supplied the independent author check for this exercise.

The final pinned source is recorded in the packaged compatibility asset. The final CLI pin `60f571416aa9659b1a1b610001ac7384ab722b78` rejects conflicting text and ID fields and does not synthesize message text from non-text objects. A fresh normalized read on that pin found the same single outgoing test and exact reply text; no second test was sent.

## Limits

This proves one bounded exchange and the listed offline behaviors. It does not prove universal message ordering, a remote server identity/version, exactly-once delivery across computers, future App compatibility, or every CLI command. The journal applies only to callers sharing the same private absolute path and operation scope. Account IDs, real conversation text, and credentials are deliberately excluded from this report.

Local results: 98 plugin unit tests, 9 separate synthetic reviewer cases, and 71 CLI tests passed. Ruff, Mypy, source/private-data validation, and deterministic archive readback passed. The public CI runs those tests without live credentials.
