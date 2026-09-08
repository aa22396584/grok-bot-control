# Grok Bot Control marketplace

This portable package contains the MIT-licensed community plugin and its Codex marketplace entry.

After extracting the ZIP, register the directory that contains `.agents/` and `plugins/`:

```sh
codex plugin marketplace add /path/to/grok-bot-control-marketplace
codex plugin add grok-bot-control@grok-bot-control-local
```

Open a new Codex task and ask it to use `$grok-bot-control` for your authorized Grok Bot conversation.

See the [plugin guide](plugins/grok-bot-control/README.md) for capabilities, requirements, commands, and proof boundaries. Run examples in that guide from the plugin directory unless it specifies otherwise.

[Website](https://iml1s.github.io/grok-bot-control/) · [Source and tests](https://github.com/ImL1s/grok-bot-control) · [License](LICENSE)

This community package is independent of OpenAI, Cursor, and xAI. Installation does not include Grok Bot, credentials, a computer-use backend, or a background service.
