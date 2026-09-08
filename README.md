# Grok Bot Control

**Reviewable handoffs between Codex and Grok Bot.** Identify the right conversation, preserve drafts, reconcile uncertain sends, and verify the work that comes back.

[Website](https://iml1s.github.io/grok-bot-control/) · [Releases](https://github.com/ImL1s/grok-bot-control/releases) · [Support](https://iml1s.github.io/grok-bot-control/support/) · [MIT license](LICENSE)

This is an independent community plugin by [ImL1s](https://github.com/ImL1s). It is not affiliated with or endorsed by OpenAI, Cursor, or xAI. Public availability here does not mean approval or listing in an official plugin directory.

## Install in Codex

```sh
codex plugin marketplace add ImL1s/grok-bot-control
codex plugin add grok-bot-control@grok-bot-control-local
```

Start a new Codex task, then ask:

> Use $grok-bot-control to coordinate with my authorized Grok Bot conversation. Read the latest response, check the returned evidence, and continue the handoff.

You need a host-provided computer-use tool and access to the target conversation. The native app procedure has been exercised on macOS. Installing this plugin does not grant account access or install a computer-use tool. The optional third-party CLI is separate and experimental.

For an offline install, extract the marketplace ZIP from [Releases](https://github.com/ImL1s/grok-bot-control/releases), add that extracted folder with `codex plugin marketplace add /path/to/grok-bot-control-marketplace`, then run the second install command above.

## What is included

- A reusable conversation workflow: target, draft, readback, send, acknowledgement, and artifact review.
- Read-only Python helpers for send-state decisions and bounded follow-up timing.
- Procedures for file handoffs, routines, skills, notifications, and other product surfaces, with their verification limits stated.
- Offline tests and synthetic reviewer cases that do not contact Grok or any real account.

There is no MCP server, bundled API client, background scheduler, push provider, or credential store. The operator record is advisory and is not a distributed lock. A timed-out send must be reconciled before retrying.

See the [plugin guide](plugins/grok-bot-control/README.md) for the capability matrix and [skill](plugins/grok-bot-control/skills/grok-bot-control/SKILL.md) for the full workflow.

## Test locally

Python 3.10 or newer; no additional Python packages are required for these checks.

```sh
python3 -m unittest discover -s plugins/grok-bot-control/skills/grok-bot-control/tests -v
python3 scripts/run_review_cases.py
python3 scripts/validate_release.py
python3 scripts/build_release.py --output dist
```

The automated cases prove offline decision behavior and packaging. They do not simulate delivery to a real Bot or prove that a future UI version works. Read [reviewer cases](submission/TEST_CASES.md) for those boundaries.

## Development and publication

Edit source under `plugins/grok-bot-control`, not the installed Codex cache. Pull requests run the offline checks; pushes to `main` deploy the static `site/` directory to GitHub Pages. `scripts/build_release.py` creates a portable marketplace ZIP and a skills-only ZIP with SHA-256 checksums.

Official directory submission is a separate review process. [Listing draft and reviewer material](submission/) are preparation assets, not evidence of acceptance.

## 繁體中文

這個開源 plugin 把與 Grok Bot 協作的流程整理成可重用技能：確認對話、保留草稿、核對是否真的送出、等待回覆，再驗證交接檔案。遇到逾時會先查清楚，不會直接重送。

它使用你現有的 Codex 工具與已授權的 Grok Bot 帳號；不附帳密，也不提供全天候服務。安裝後開新任務，直接說「用 $grok-bot-control 幫我跟指定的 Grok Bot 協作」。

[Privacy](https://iml1s.github.io/grok-bot-control/privacy/) · [Terms](https://iml1s.github.io/grok-bot-control/terms/) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)
