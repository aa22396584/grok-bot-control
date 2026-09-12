# Grok Bot Control

> **Development home:** https://github.com/ImL1s/grok-bot-control  
> Please open issues and pull requests there.  
> **Mirrors:** [Codeberg](https://codeberg.org/ImL1s/grok-bot-control) · [GitLab](https://gitlab.com/aa22396584/grok-bot-control)


**Reviewable Grok Bot handoffs for Codex, Claude Code, and Grok Build.** One shared Agent Skill identifies the right conversation, preserves drafts, reconciles uncertain sends, and verifies the work that comes back.

[Website](https://iml1s.github.io/grok-bot-control/) · [Releases](https://github.com/ImL1s/grok-bot-control/releases) · [Support](https://iml1s.github.io/grok-bot-control/support/) · [MIT license](LICENSE)

This is an independent community plugin by [ImL1s](https://github.com/ImL1s). It is not affiliated with or endorsed by OpenAI, Cursor, or xAI. Public availability here does not mean approval or listing in an official plugin directory.

## Install in Codex

```sh
codex plugin marketplace add ImL1s/grok-bot-control
codex plugin add grok-bot-control@grok-bot-control-local
```

Start a new Codex task, then ask:

> Use $grok-bot-control to coordinate with my authorized Grok Bot conversation. Read the latest response, check the returned evidence, and continue the handoff.

You need a host-provided computer-use tool or the [optional pinned CLI adapter](plugins/grok-bot-control/skills/grok-bot-control/references/cli-adapter.md), plus access to the target conversation. The native app procedure has been exercised on macOS. Installing this plugin does not grant account access or install either backend.

For an offline install, extract the marketplace ZIP from [Releases](https://github.com/ImL1s/grok-bot-control/releases), add that extracted folder with `codex plugin marketplace add /path/to/grok-bot-control-marketplace`, then run the second install command above.

## What is included

- A reusable conversation workflow: target, draft, readback, send, acknowledgement, and artifact review.
- Read-only Python helpers for host capability assessment, send-state decisions, and bounded follow-up timing.
- An optional CLI adapter for Bot roster, normalized transcript reads, and explicit sends; a shared local delivery journal blocks repeat dispatch after uncertain outcomes across CLI and UI workflows.
- Procedures for file handoffs, routines, skills, notifications, and other product surfaces, with their verification limits stated.
- Offline tests and synthetic reviewer cases that do not contact Grok or any real account.

There is no MCP server, bundled API client, background scheduler, push provider, or credential store. The external CLI owns authentication and protocol compatibility. The delivery journal is a local shared-file guard, not a distributed lock or exactly-once guarantee. A timed-out send must be reconciled; the adapter never automatically retries or switches to UI to send again.

See the [plugin guide](plugins/grok-bot-control/README.md) for the capability matrix and [skill](plugins/grok-bot-control/skills/grok-bot-control/SKILL.md) for the full workflow.

## Install in Claude Code or Grok Build

Claude Code:

```sh
claude plugin marketplace add ImL1s/grok-bot-control
claude plugin install grok-bot-control@grok-bot-control-local
```

In Claude Code, invoke `/grok-bot-control:grok-bot-control`. For local development, run `claude --plugin-dir ./plugins/grok-bot-control` from this checkout. Validate metadata without invoking a model using `claude plugin validate ./plugins/grok-bot-control`.

Grok Build:

```sh
grok plugin marketplace add ImL1s/grok-bot-control
grok plugin install grok-bot-control --trust
grok plugin details grok-bot-control
```

`--trust` trusts this reviewed plugin's files. Grok Build is the terminal agent; Grok Bot is the separate application this skill helps coordinate with. The native Grok catalog and Claude-compatible manifest point to the same skill directory. Use a current Grok Build version with plugin support.

Other agents can install the skills-only ZIP using their own Agent Skills discovery mechanism. Python helpers require Python 3.10+ and the standard library. Plugin installation provides instructions, offline helpers, and an optional CLI adapter; live coordination also requires a host-provided UI/browser tool or a separately configured CLI. See [compatibility and validation](docs/COMPATIBILITY.md) for tested versions and the difference between installation and live operation.

## Test locally

Python 3.10 or newer; no additional Python packages are required for these checks.

```sh
python3 -m unittest discover -s plugins/grok-bot-control/skills/grok-bot-control/tests -v
python3 -m unittest discover -s tests -v
python3 scripts/sync_metadata.py --check
python3 scripts/run_review_cases.py
python3 scripts/validate_release.py
python3 scripts/build_release.py --output dist
```

The automated cases prove offline decision behavior and packaging. They do not simulate delivery to a real Bot or prove that a future UI version works. Read [reviewer cases](submission/TEST_CASES.md) for those boundaries.

## Development and publication

Edit the shared skill under `plugins/grok-bot-control/skills/grok-bot-control`. `release.json` is the metadata source; run `python3 scripts/sync_metadata.py` after changing it. This generates platform manifests and Claude/Grok catalogs and updates the skill version. The existing Codex catalog retains its stable marketplace identity.

Pull requests run the same offline check suite as Pages and tagged releases. Pages deploys only after that commit passes checks. A version tag builds and publishes marketplace, plugin-root, and skills-only ZIPs with SHA-256 checksums after validation. See [release procedure](docs/RELEASING.md) and [changelog](CHANGELOG.md). Public CI uses synthetic state and does not connect to real Grok Bot or Telegram accounts.

Official directory submission is a separate review process. [Listing draft and reviewer material](submission/) are preparation assets, not evidence of acceptance.

## 繁體中文

這個開源 plugin 把與 Grok Bot 協作的流程整理成可重用技能：確認對話、保留草稿、核對是否真的送出、等待回覆，再驗證交接檔案。遇到逾時會先查清楚，不會直接重送。

同一份 skill 可供 Codex、Claude Code、Grok Build 使用；實際操控仍使用各平台提供的工具與你已授權的 Grok Bot 帳號。安裝後先檢查工具能力，再讓 agent 讀取指定對話。它不附帳密，也不提供全天候服務。

[Privacy](https://iml1s.github.io/grok-bot-control/privacy/) · [Terms](https://iml1s.github.io/grok-bot-control/terms/) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)
