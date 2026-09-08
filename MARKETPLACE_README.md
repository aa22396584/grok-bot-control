# Grok Bot Control marketplace

This portable package contains the MIT-licensed community plugin and its Codex, Claude Code, and Grok Build marketplace entries. All platforms use one shared skill directory.

After extracting the ZIP, register the directory that contains `.agents/` and `plugins/`:

```sh
codex plugin marketplace add /path/to/grok-bot-control-marketplace
codex plugin add grok-bot-control@grok-bot-control-local
```

Open a new Codex task and ask it to use `$grok-bot-control` for your authorized Grok Bot conversation.

Claude Code:

```sh
claude plugin marketplace add /path/to/grok-bot-control-marketplace
claude plugin install grok-bot-control@grok-bot-control-local
```

Invoke `/grok-bot-control:grok-bot-control` in Claude Code.

Grok Build:

```sh
grok plugin marketplace add /path/to/grok-bot-control-marketplace
grok plugin install grok-bot-control --trust
grok plugin details grok-bot-control
```

If another marketplace exposes the same plugin name, install this extracted plugin directly with `grok plugin install /path/to/grok-bot-control-marketplace/plugins/grok-bot-control --trust` and verify the source in plugin details.

See the [plugin guide](plugins/grok-bot-control/README.md) for capabilities, requirements, commands, and proof boundaries. Run examples in that guide from the plugin directory unless it specifies otherwise.

[Website](https://iml1s.github.io/grok-bot-control/) · [Source and tests](https://github.com/ImL1s/grok-bot-control) · [License](LICENSE)

This community package is independent of OpenAI, Cursor, and xAI. Installation does not include Grok Bot, credentials, a computer-use backend, or a background service.
