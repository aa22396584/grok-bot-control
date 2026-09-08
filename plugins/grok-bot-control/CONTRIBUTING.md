# Contributing

Contributions should preserve the plugin's narrow role: Codex-hosted coordination guidance plus offline, read-only decision helpers.

## Change requirements

1. Keep credentials, identifiers, private transcripts, real Bot names, employee paths, and machine-specific absolute paths out of fixtures and documentation.
2. Mark each workflow as exercised, offline-tested, documented-only, or unverified. Do not turn a product capability into a plugin claim.
3. Add regression tests before changing send, timeout, operator, or duplicate-handling behavior.
4. Keep helper scripts standard-library-only and side-effect-free. They may advise; they must not open apps, send messages, mutate state, or schedule work.
5. For optional third-party CLI changes, pin the audited source, document credential access and undocumented-route dependence, and keep patches separate from this plugin.

## Validation

Run from the plugin root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 skills/grok-bot-control/tests/test_assess_wait.py
PYTHONDONTWRITEBYTECODE=1 python3 skills/grok-bot-control/tests/test_assess_send.py
```

Then run the Codex skill and plugin validators used by your installation, scan for secrets and private paths, verify Markdown links, and inspect the final archive members. A live UI or CLI test requires a separate authorized test conversation and must use an announced synthetic marker.

## Pull requests

Describe the concrete failure or workflow gap, the resulting behavior, proof level, tests run, and any capability that remains unverified. Keep unrelated formatting or refactors out of the change.
