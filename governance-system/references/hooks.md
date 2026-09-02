# Hook Policy

Hooks are project-level adapters around the deterministic runtime. They enforce an
already-installed governance policy; they do not define policy.

## Activation

Install hooks only after project opt-in. Every hook first reads
`.governance/config.json`. Missing or disabled configuration is an immediate no-op.

## Events

- session start — refresh inventory and provide canonical-state context;
- subagent start — register agent, worktree and scope;
- pre-edit — ask or deny when another worktree owns a dirty overlapping path;
- post-edit — refresh the current worktree registry entry;
- before shell execution — ask before destructive Git operations;
- subagent stop — collect changed paths, tests and unfinished work;
- stop — refresh a stale inventory, then warn once about validation errors or unresolved
  resolutions; never block the turn (closure is gated by `close-stage`);
- session end — snapshot dirty variants and refresh state.

## Safety

- Parse and validate JSON input.
- Use bounded timeouts and no network calls.
- Never print environment values, file contents, patches or secrets.
- Never depend on hook order; matching hooks may run concurrently.
- Use atomic state updates.
- Fail closed for destructive Git; ask, never silently deny, on path collisions.
- Fail open with a warning for passive inventory failures.
- Cap stop/follow-up loops (`loop_limit` on Cursor; honour `stop_hook_active` on
  Claude Code).
- Re-running `install-hooks` replaces the governance entries rather than appending.
- The Cursor `preToolUse` entry carries no matcher; the adapter filters on the
  payload's command or file path because Cursor tool-type names are not verified.

Cursor and Claude Code event names and response envelopes differ. Their adapters
normalize input into `governancectl hook` and translate its neutral decision back into
the platform response.
