# Compatibility and evidence

The three plugin manifests refer to one canonical Agent Skill. Marketplace formats are adapters, not separate workflow implementations.

| Host | Distribution metadata | Verification boundary |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`; plugin `.codex-plugin/plugin.json` | Codex manifest validation; existing native macOS CUA workflow exercised. |
| Claude Code | `.claude-plugin/marketplace.json`; plugin `.claude-plugin/plugin.json` | Validate and install/discover with Claude Code; live UI control requires that host's own tools. |
| Grok Build | `.grok-plugin/marketplace.json`; plugin `.grok-plugin/plugin.json` | Native validation and install/discovery; Claude-compatible metadata is also included. |
| Other Agent Skills hosts | Standalone skills ZIP | Standard skill structure and Python helpers; host discovery and live tools vary. |

Grok Build does not use Codex's `.agents/plugins/marketplace.json` as a marketplace index. Its support for `.agents/skills` is a separate discovery feature. Neither portable frontmatter nor a plugin manifest grants tools, account access, or operating-system permissions.

## Host checks

On 2026-09-08, Claude Code 2.1.263 and Grok Build 1.0.13 passed their native plugin manifest validators. Both hosts installed version 0.2.0 from the local marketplace in fresh disposable configuration directories and reported one skill directory. All 26 installed plugin files matched the release candidate source byte-for-byte on both hosts. Grok also passed the direct-path install route in an earlier smoke. These checks validate packaging and discovery; they do not send messages, invoke an agent model, or open a Telegram Client.

## Upstream references

- [Agent Skills specification](https://agentskills.io/specification)
- [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code marketplace format](https://code.claude.com/docs/en/plugin-marketplaces)
- [Grok Build skills, plugins, and marketplaces](https://docs.x.ai/build/features/skills-plugins-marketplaces)

The optional [grok-bot-cli fork](https://github.com/ImL1s/grok-bot-cli) is a separate project. Its authentication, backend compatibility, and live behavior are not established by this plugin's CI.

## Optional CLI adapter in 0.3.0

The adapter requires the exact source hashes and commit in [`cli-compatibility.json`](../plugins/grok-bot-control/skills/grok-bot-control/assets/cli-compatibility.json), a trusted absolute Node.js path (major 22), and the canonical `/Applications/Grok Bot.app` bundle (identifier and version 0.44.0). Live operations are gated to macOS. This verifies the installed bundle and reviewed source files, not the identity or version of a remote Gateway server.

Only Bot roster, normalized transcript reads, explicit stdin sends, and readback reconciliation are exposed. Offline CI tests the decision and journal behavior on Linux, macOS, and Windows; subprocess fault tests run on POSIX. Windows and Linux live authentication are not validated. Direct CLI or UI operations that bypass the shared journal are outside its duplicate-send protection, and separate computers do not share a distributed lock. See the [adapter guide](../plugins/grok-bot-control/skills/grok-bot-control/references/cli-adapter.md) for setup and evidence limits.

The [bounded adapter exercise](ADAPTER_EVIDENCE.md) records the live roster/read/send/UI readback separately from synthetic fault tests. Bot replies lacking an explicit API role remain `unknown`; use independent UI evidence when author attribution matters.
