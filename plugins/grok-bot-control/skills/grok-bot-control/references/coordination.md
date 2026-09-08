# Coordination, handoff, and waiting

Keep one stable `coordination.json` for a long-running task. It is a handoff record, not a lock or authorization token. Before taking over, inspect the latest conversation and confirm the previous sender is no longer writing.

## Handoff content

A useful handoff identifies:

- the real operator and bounded objective;
- completed and unchanged work;
- the exact next change;
- artifact location, version, and SHA-256 when files are exchanged;
- validation commands and expected evidence;
- actions inside and outside current authorization;
- the required reply or output location.

Send the smallest delta that lets the other agent proceed. Do not paste the whole conversation history. When receiving an archive, validate member paths and links before extraction, unpack into an isolated directory, compare hashes, and inspect commands for side effects before running them.

## Follow-up policy

Only enable nudges when the user requested progress follow-up. Before each nudge, read the latest conversation and artifact location.

The included template defaults to a first check after 20 minutes, repeats no sooner than 30 minutes, and caps a stalled segment at two nudges. These are editable preferences, not Grok Bot platform rules. A substantive reply, new artifact, or concrete test progress resets the progress clock. A spinner or repeated “working” status does not.

Respect an explicit longer ETA. After the nudge cap, notify the user once and stop. A safe nudge asks only for current progress, blocker, or missing input; it does not repeat the task, restart work, expand scope, or trigger external actions.

The helper's `nudge_due` result is timing advice only. Refresh the UI, build the exact nudge, hash it, and pass that digest plus the fresh UI observation through `assess_send.py` before any paste or send. The wait helper is neither a sender nor a cross-process lock. `inspect` means the snapshot is missing or inconsistent and requires manual state reconciliation.

Schedulers are host capabilities, not part of this plugin. If the host supports scheduling and the user requested continued monitoring, use one task-specific schedule and stop it when the task completes or is cancelled. Without a scheduler, do not promise work after the current run ends.

## Synthetic notification tests

Before any canary that can reach a real user, state the planned time, sender/receiver role, a unique test marker, and that it does not represent a real work item. A production-looking reminder sent from a synthetic record can be mistaken for genuine pending work. Prefer an explicit test template when the implementation supports one. If it does not, disclose the exact production-looking text and timing before sending; do not claim the canary is clearly labeled when the program cannot label it.

After the test, record API acceptance, automatic cancellation behavior, and the user's device observation separately. A sent canary does not prove the full production trigger path.
