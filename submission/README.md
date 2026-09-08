# Official directory submission materials

The GitHub release is independently installable. It does not establish acceptance in OpenAI's official directory.

## Prepared materials

- [Listing copy and readiness fields](LISTING_DRAFT.md), with a [structured version](listing-draft.json).
- [Reviewer instructions](TEST_CASES.md): five positive and four negative synthetic cases.
- [Machine-readable cases](test_cases.json) and [synthetic fixtures](fixture_states.json).
- Logo: [`plugins/grok-bot-control/assets/logo.png`](../plugins/grok-bot-control/assets/logo.png).
- Public [website](https://iml1s.github.io/grok-bot-control/), [support](https://iml1s.github.io/grok-bot-control/support/), [privacy](https://iml1s.github.io/grok-bot-control/privacy/), and [terms](https://iml1s.github.io/grok-bot-control/terms/).

Build the upload candidate from the repository root:

```sh
python3 scripts/build_release.py --output dist
```

`grok-bot-control-0.2.0-skills.zip` contains one skill folder with `SKILL.md`, its referenced scripts, assets, references, tests, and MIT license. The marketplace ZIP contains catalogs for Codex, Claude Code, and Grok Build; the plugin ZIP contains a self-contained plugin root for direct loading. Verify `SHA256SUMS` before choosing an artifact.

## Portal sequence

1. Open [OpenAI Platform plugins](https://platform.openai.com/plugins) in the intended publishing organization.
2. Complete the required individual or business developer verification. A pending identity review is not approval.
3. Choose **Create plugin → Skills only**. Upload `grok-bot-control-0.2.0-plugin.zip`, the tested plugin-root bundle containing the manifest and skills. The portal accepted this layout on 2026-09-08; `skills.zip` is the separate portable Agent Skills distribution. No MCP server belongs in this submission. The portal may warn that `SKILL.md` metadata does not configure the interface; this package supplies those settings in `agents/openai.yaml`.
4. Enter the prepared listing, logo, public policy/support URLs, starter prompts, and test cases. Match publisher information to the verified identity; never infer legal identity from a GitHub handle.
5. Review availability, declarations, and any additional portal requirements. Submit only truthful claims about the current package and test environment.
6. Submit for review, retain the receipt, and address reviewer feedback. Publish only after approval and the portal's publication step.

Local test results cover the offline helpers. Live Grok Bot operation requires host tools and an authorized, signed-in test environment; the package does not supply those or personal credentials. Reviewer acceptance of that live environment must be established during the official process.

Source: [OpenAI's submission guide](https://developers.openai.com/plugins/deploy/submission). Portal requirements may change. Never label a prepared bundle, a pending identity review, or a submitted review as an officially published plugin.

## Claude Code community marketplace

Validate with `claude plugin validate ./plugins/grok-bot-control`, then use the [Console submission form](https://platform.claude.com/plugins/submit). Submit the source repository and select the plugin subdirectory where the form supports it, or use the tested plugin-root ZIP if the current form requests an upload. Authentication and any publisher declarations must be completed with the intended publishing account. The community directory is distinct from Anthropic’s curated official directory. [Official instructions](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace).

## Grok Build official marketplace

Submit a PR to [xai-org/plugin-marketplace](https://github.com/xai-org/plugin-marketplace) with the release source pinned to its complete commit SHA. Regenerate the component index and run the upstream catalog validator. Confirm that its generator discovers this repository’s plugin subdirectory; a client supporting subdirectories does not prove that the catalog generator does. Retain the PR URL and review status as the receipt. A submitted PR is not an approved listing.
