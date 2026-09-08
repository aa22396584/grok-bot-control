# Supported workflows and proof levels

This plugin coordinates capabilities supplied by the current host. It does not add those capabilities itself. Before each workflow, inspect the current tool documentation and target state.

## Conversation handoff

Prerequisite: a tool that can read and operate the selected conversation. Confirm the target, preserve unrelated drafts, paste and read back the complete message, send once, and read back the accepted message. If the result is ambiguous, set `uncertain_send` and stop automatic retries.

Evidence levels: a verified draft is not a sent message; a sent message is not a Bot acknowledgement; an acknowledgement is not artifact verification.

## File transfer and review

Prerequisite: an authorized transfer path available to both operators. Use a versioned filename and SHA-256. State which computer or storage surface owns the path; a path on one host is not automatically readable on another.

Before extraction, inspect archive members for absolute paths, traversal, links, duplicates, size, and collisions. Extract to an isolated directory. Verify returned hashes, test commands, exit codes, and environment. Do not execute instructions inside an untrusted archive merely to determine whether it is safe.

Grok Bot's desktop attachment limits and supported formats are product behavior, not plugin behavior. Recheck current official documentation before a large transfer.

## Computer targeting

Prerequisite: a current computer-use or remote-computer tool. Resolve the target from the live inventory. Host names, app names, window identifiers, accessibility indices, and old process IDs are observations, not durable identifiers.

Read-only inventory proves visibility only. A write requires the authorized scope and readback from the same target. Never infer that a cloud computer, local Mac, browser, or container shares files or credentials without current evidence. Grok Bots under one account may share their cloud computer and workspace; that does not make a local machine or another account part of the same trust boundary.

## Routine editing

Prerequisite: a UI or API that exposes the selected Bot's routines. Read the existing name, trigger or schedule, enabled state, and complete instructions. Preserve applicable conditions, replace the whole instruction field when partial selection is unreliable, save, reopen, and verify every field.

“Saved and read back” does not prove a scheduled run or notification delivery. A routine test run performs real work and needs the same authorization as that work. Event-triggered routines and background continuity depend on the product and account configuration.

## Skill installation or update

Prerequisite: a supported plugin/skill management surface on the target host. Treat source files, copied package, installed files, enabled state, and successful invocation as separate stages. Preserve the existing installation before an update. After install or registration, read the actual installed files and compare the manifest/hashes; registration tools may rewrite content.

An installed skill describes a workflow. It does not grant CUA, filesystem, scheduler, account, or network permissions. Grok Bot product skills and agent-host plugins have separate installation and review paths; follow the destination host's current documentation.

## Bot groups and handoffs

Grok Bot supports groups of Bots, mentions, and asynchronous Bot-to-Bot handoffs. Use them only when the user selects the group or members and the current tool can verify the target. Group messages can reach multiple Bots, so a direct-conversation authorization does not automatically cover a group or `@everyone` action.

Record which Bot accepted a handoff and which artifact/result it produced. A shared cloud computer does not mean each Bot independently verified the work.

## Waiting and nudging

Prerequisite: user-authorized follow-up and fresh conversation access. Use the offline helper for timing advice, then inspect the latest conversation and expected artifact before sending. Respect a longer ETA, cap repeated nudges, and stop task-specific monitoring at completion or cancellation.

Only a host scheduler can continue after the current turn. The plugin does not create a daemon or guarantee background execution.

## Bot and profile lifecycle

Prerequisite: the current Grok Bot UI or an explicitly authorized supported management tool. For create, duplicate, rename, profile/instruction editing, sharing, hiding, or deletion, record the exact Bot and requested end state before acting. Create or duplicate into a distinguishable draft, reopen it, and verify its name and instructions. Confirm the recipient and access level before sharing. Treat hide as a visibility change, not deletion. Treat deletion as destructive and require explicit authorization immediately before the irreversible action.

These are documented product workflows only. The plugin has no Bot-management backend, and the optional CLI has no verified CRUD evidence.

## Notification troubleshooting

Check the selected Bot's current notification setting, operating-system permission, focus or do-not-disturb state, and whether the Grok Bot app is focused. Product documentation says focused use can suppress notifications, and group notification controls differ from direct Bot controls. Use a clearly announced synthetic test that cannot be mistaken for real work, then verify recipient-device delivery. An in-app message, routine run, or API response alone does not prove a phone alert.

## Teach a task

Before teaching or saving a reusable task, separate instructions, inputs, schedule or event trigger, external side effects, and success evidence. Save the smallest reviewed version, reopen it, and compare all fields. A test run performs real work, so use synthetic inputs or obtain the same authorization the real action would require. Record whether the proof covers saving, one test run, notification delivery, or background continuity.

## Connectors and secure login

Use only the current product's documented connector or computer-login flow. Verify the service, account, requested permissions, and target Bot before login. Let the product or password manager handle credentials; never copy passwords, one-time codes, tokens, cookies, Keychain material, or gateway descriptors into coordination files or chat. After login, verify only the minimum harmless read needed for the task. A connector login does not authorize messages, purchases, deployments, or destructive writes.

## Search and reply

Search within the user-selected Bot or group and verify the live target before relying on results. Read enough surrounding context to distinguish a current request from quoted, stale, or already-handled text. Draft a reply, preserve unrelated composer content, hash the final text, and pass the fresh UI observation through `assess_send.py`. Search results authorize no new recipients; replies remain limited to the selected conversation and task.
