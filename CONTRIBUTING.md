# Contributing

Contributions should preserve the plugin's narrow role: portable coordination guidance, offline decisions, and a thin optional adapter to a separately maintained CLI.

## Change requirements

1. Keep credentials, identifiers, private transcripts, real Bot names, employee paths, and machine-specific absolute paths out of fixtures and documentation.
2. Mark each workflow as exercised, offline-tested, documented-only, or unverified. Do not turn a product capability into a plugin claim.
3. Add regression tests before changing send, timeout, operator, or duplicate-handling behavior.
4. Keep assessment helpers standard-library-only and side-effect-free. The explicit delivery journal may persist local reservations. Only `grok_cli.py` may invoke the pinned external CLI, with live/send opt-ins and a durable reservation before a send. Tests must use synthetic backends and must not invoke real accounts.
5. For optional third-party CLI changes, pin the audited source, document credential access and undocumented-route dependence, and keep patches separate from this plugin.

## Validation

Run from the repository root:

```sh
python3 -m unittest discover -s plugins/grok-bot-control/skills/grok-bot-control/tests -v
python3 -m unittest discover -s tests -v
python3 scripts/sync_metadata.py --check
python3 scripts/check_private_data.py
python3 scripts/run_review_cases.py
python3 scripts/validate_release.py
python3 scripts/build_release.py --output dist
```

Then run the native validators for the hosts available in your environment, verify Markdown links, and inspect the final archive members. See [compatibility evidence](docs/COMPATIBILITY.md). A live UI or CLI test requires a separate authorized test conversation and must use an announced synthetic marker.

## Pull requests

Describe the concrete failure or workflow gap, the resulting behavior, proof level, tests run, and any capability that remains unverified. Keep unrelated formatting or refactors out of the change.
