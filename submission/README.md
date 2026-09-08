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

`grok-bot-control-0.1.0-skills.zip` contains one skill folder with `SKILL.md`, its referenced scripts, assets, references, tests, and MIT license. The separate `marketplace.zip` is for Codex repository-marketplace installation. Verify `SHA256SUMS` before choosing an artifact.

## Portal sequence

1. Open [OpenAI Platform plugins](https://platform.openai.com/plugins) in the intended publishing organization.
2. Complete the required individual or business developer verification. A pending identity review is not approval.
3. Choose **Create plugin → Skills only**. Upload the final tested skills bundle using the current portal's accepted upload layout; no MCP server belongs in this submission.
4. Enter the prepared listing, logo, public policy/support URLs, starter prompts, and test cases. Match publisher information to the verified identity; never infer legal identity from a GitHub handle.
5. Review availability, declarations, and any additional portal requirements. Submit only truthful claims about the current package and test environment.
6. Submit for review, retain the receipt, and address reviewer feedback. Publish only after approval and the portal's publication step.

Local test results cover the offline helpers. Live Grok Bot operation requires host tools and an authorized, signed-in test environment; the package does not supply those or personal credentials. Reviewer acceptance of that live environment must be established during the official process.

Source: [OpenAI's submission guide](https://developers.openai.com/plugins/deploy/submission). Portal requirements may change. Never label a prepared bundle, a pending identity review, or a submitted review as an officially published plugin.
