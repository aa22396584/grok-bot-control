# Optional CLI adapter

The plugin includes `scripts/grok_cli.py`, a thin adapter for a separately installed and reviewed `grok-bot-cli` checkout. The dependency is optional and is not vendored, installed, updated, or discovered automatically. It does not add an MCP server.

Use only absolute paths for the reviewed CLI source, Node executable, Grok Bot app bundle, message file, and delivery journal. The source commit and required file hashes are release data in `assets/cli-compatibility.json`; do not substitute a moving branch, npm `latest`, or another checkout. Source-file verification detects a mismatch in the listed files, but it is not cryptographic attestation of the Node process, operating system, app, remote gateway, or loaded runtime after verification.

The validated live host is macOS with `/Applications/Grok Bot.app` (`com.anysphere.sand`), Grok Bot 0.44.0, and Node 22. Other versions remain unvalidated. `check` is pure offline inspection: it verifies the source pin and that the supplied Node path is an absolute existing file without executing Node, reading the app credential, or using the network. Its output therefore reports `node_version: not_executed_offline`; the pinned Node major is checked only after explicit live opt-in.

First obtain the dependency explicitly after reviewing its source:

```sh
git clone https://github.com/ImL1s/grok-bot-cli /absolute/path/to/reviewed-grok-bot-cli
git -C /absolute/path/to/reviewed-grok-bot-cli checkout --detach 60f571416aa9659b1a1b610001ac7384ab722b78
```

This pinned checkout needs no runtime npm dependencies; a trusted Node 22 executable is still required. Updating to another commit requires reviewing and releasing a new compatibility pin.

```sh
python3 scripts/grok_cli.py check \
  --cli-dir /absolute/path/to/reviewed-grok-bot-cli \
  --node /absolute/path/to/node
```

The complete adapter interface is available from `python3 scripts/grok_cli.py --help`. Live reads require both `--allow-live` and the explicit app bundle:

```sh
python3 scripts/grok_cli.py bots \
  --cli-dir /absolute/path/to/reviewed-grok-bot-cli \
  --node /absolute/path/to/node \
  --app-bundle '/Applications/Grok Bot.app' \
  --allow-live

python3 scripts/grok_cli.py thread \
  --cli-dir /absolute/path/to/reviewed-grok-bot-cli \
  --node /absolute/path/to/node \
  --app-bundle '/Applications/Grok Bot.app' \
  --allow-live \
  --target-id '<EXACT_TARGET_ID>' \
  --target-name '<EXACT_TARGET_NAME>' \
  --limit 50
```

`bots` verifies the live roster shape. `thread` rechecks the exact target against that roster and requests the CLI's normalized JSON. A normalized transcript retains only the target identity and messages with `id`, explicit `user`/`assistant`/`unknown` role, and text. Do not infer an outgoing message from its wording or order.

## One delivery journal for CLI and UI

Use one private local SQLite journal for every surface that could send to the same target. Give each intended logical operation a unique, non-secret `--scope`, then reuse that exact scope, target ID, and exact UTF-8 message SHA-256 for inspection, send, reconciliation, and any resumed attempt. Never create a new scope merely to get around an `uncertain` record.

The CLI send reads a baseline transcript, atomically reserves the delivery as `uncertain`, passes the exact message through stdin, and then looks for a new outgoing `role: user` message whose ID was absent from the baseline. This bounded check assumes the pinned endpoint returns stable message IDs and that its tail contains the relevant newest message. The normalized payload provides no independent chronology or ordering guarantee, so a new-ID match is bounded evidence rather than general exactly-once proof. The message must be valid UTF-8, have no NUL or surrounding whitespace, and be at most 64 KiB. Its supplied digest must match those exact bytes.

```sh
python3 scripts/grok_cli.py send \
  --cli-dir /absolute/path/to/reviewed-grok-bot-cli \
  --node /absolute/path/to/node \
  --app-bundle '/Applications/Grok Bot.app' \
  --allow-live --allow-send \
  --target-id '<EXACT_TARGET_ID>' \
  --target-name '<EXACT_TARGET_NAME>' \
  --message-file /absolute/private/path/message.txt \
  --message-sha256 '<LOWERCASE_SHA256>' \
  --journal /absolute/private/path/delivery.sqlite3 \
  --scope '<UNIQUE_OPERATION_SCOPE>' \
  --operator '<CURRENT_OPERATOR>'
```

Only run `send` within the user-authorized task and target. Existing delegation covers routine messages needed for that task; do not request the same authorization again. An acknowledgement does not confirm delivery. A timeout, CLI error, malformed response, missing baseline, read failure, or absence from a bounded transcript tail remains `uncertain` and blocks another CLI or UI send. Use `reconcile` with the same arguments except `--allow-send` and `--operator`; it reads again and never sends.

For a UI send, inspect and reserve through the same journal before activating Send:

```sh
python3 scripts/delivery_state.py inspect /absolute/private/path/delivery.sqlite3 \
  --scope '<UNIQUE_OPERATION_SCOPE>' --target '<EXACT_TARGET_ID>' \
  --message-sha256 '<LOWERCASE_SHA256>'

python3 scripts/delivery_state.py begin /absolute/private/path/delivery.sqlite3 \
  --scope '<UNIQUE_OPERATION_SCOPE>' --target '<EXACT_TARGET_ID>' \
  --message-sha256 '<LOWERCASE_SHA256>' --operator '<CURRENT_OPERATOR>' \
  --transport ui
```

Native UI surfaces may not expose message IDs. Compare the post-send UI with the fresh pre-send snapshot and confirm only when the exact target has one unambiguous new outgoing bubble with the exact message text. If stable message IDs are visible, supply each pre-send ID as another optional `--baseline-id`. Without recorded baseline IDs, CLI reconciliation remains `uncertain`; the original UI operator must make the fresh visual confirmation instead.

```sh
python3 scripts/delivery_state.py confirm /absolute/private/path/delivery.sqlite3 \
  --scope '<UNIQUE_OPERATION_SCOPE>' --target '<EXACT_TARGET_ID>' \
  --message-sha256 '<LOWERCASE_SHA256>' --transport ui
```

UI remains a fallback for unsupported CLI operations and for inspection before any send. It can also provide independent readback. Never turn CLI uncertainty into an automatic UI retry; reconcile on the original surface or stop for an operator.
