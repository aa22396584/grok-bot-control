# Contributing

Contributions should preserve the plugin's narrow role: portable agent coordination guidance plus offline, read-only decision helpers.

## Change requirements

1. Keep credentials, identifiers, private transcripts, real Bot names, employee paths, and machine-specific absolute paths out of fixtures and documentation.
2. Mark each workflow as exercised, offline-tested, documented-only, or unverified. Do not turn a product capability into a plugin claim.
3. Add regression tests before changing send, timeout, operator, or duplicate-handling behavior.
4. Keep helper scripts standard-library-only and side-effect-free. They may advise; they must not open apps, send messages, mutate state, or schedule work.
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
