# Release procedure

## Source and validation

The shared skill is maintained once in `plugins/grok-bot-control/skills/grok-bot-control/`. `release.json` owns plugin identity, public descriptions, and the release version. The root `CHANGELOG.md` is copied into the plugin by the metadata generator. Run:

```sh
python3 scripts/sync_metadata.py
python3 scripts/sync_metadata.py --check
python3 -m unittest discover -s plugins/grok-bot-control/skills/grok-bot-control/tests -v
python3 -m unittest discover -s tests -v
python3 scripts/run_review_cases.py
python3 scripts/validate_release.py
python3 scripts/build_release.py --output dist
ruff check scripts tests plugins/grok-bot-control/skills/grok-bot-control/scripts plugins/grok-bot-control/skills/grok-bot-control/tests
mypy scripts plugins/grok-bot-control/skills/grok-bot-control/scripts
```

Commit the generated files with the changelog and submit a pull request. Require the `Required checks` result before merging. Keep permissions limited to what each workflow job needs. CI uses synthetic fixtures; no account credentials or interactive Grok Bot session is required.

## Publish

After the release commit is merged and checks pass, create a `v<version>` tag on that commit and push the tag. The release workflow checks that the tag matches `release.json`, runs the same reusable checks, builds archives, and creates a GitHub Release. It fails rather than replacing an existing release. Version tags and published archive bytes are immutable: fix mistakes with a new version.

The release contains a marketplace ZIP for all three hosts, a plugin-root ZIP for direct plugin loading, a skills-only ZIP for Agent Skills consumers, `SHA256SUMS`, and `PACKAGE_VERIFICATION.json`. Artifacts come from the checked commit. Hash/readback validation proves archive integrity, not live UI compatibility.

Pages runs the check suite on its own checked-out commit before deploying `site/`; a passing check for a different commit cannot authorize deployment.

## Installation smoke and official directories

Before widening compatibility claims, run each target host's manifest validator and install/discovery smoke in a disposable configuration directory. Record host versions and results in [COMPATIBILITY.md](COMPATIBILITY.md). Tool availability and live readback require separate evidence.

GitHub publication does not update every official directory automatically. Follow [submission procedures](../submission/README.md). Grok's catalog pins a source commit and requires a PR for an update. OpenAI and Anthropic have their own review workflows. Keep private deployment configuration and runtime state in their own private project.
