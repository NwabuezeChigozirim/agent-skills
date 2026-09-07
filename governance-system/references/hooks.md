# Hook policy

Hooks adapt an opted-in project's governance policy to a host. They do not approve
scope, settle decisions, establish completion or replace host permission controls.

## Activation and installation

Install only after project opt-in with `install-hooks`. It copies each platform
wrapper and its sibling `hook_support.py`, preserving unrelated hook configuration.
Reinstallation replaces the suite's entries and refreshes both copies of the helper.

Missing or disabled `.governance/config.json` is a no-op without invoking the runtime.
Malformed activation cannot establish that the guard is disabled: pre-actions deny,
passive events warn. The wrapper uses the Git worktree root or its installed project
location, never a payload's arbitrary repository path.

The shared transport resolves `GOVERNANCECTL` when explicitly set, otherwise the
documented local-share/Cursor/Claude skill installations. A missing explicit override
is an error, not permission to select a different runtime. Install the three sibling
skills on every host or set that override to the intended runtime. Hook installation
does not install a global runtime or upgrade project policy.

## Events and ownership

- Session/subagent start and post-tool use refresh inventory through the runtime.
  This is not a new agent-identity or delegated-scope authority.
- Pre-tool use classifies commands and checks direct edit targets against fresh local
  worktree inventory. It neither discovers nor reconciles state.
- Subagent stop/session end reconcile and retain unfinished variants, surfacing
  incomplete recovery without declaring integration complete.
- Stop may refresh stale inventory and warns about validation/resolution findings.
  It never blocks turn completion or closes a stage. Cursor permits one configured
  follow-up; an active stop-hook loop is silent.

A stored registry is not current ownership proof. New uncommitted work after the last
scan still requires review before editing its matching path. Relative edit targets
use the supplied working directory inside the current worktree; external targets need
review. Unknown/unavailable worktree content blocks direct edits until inspectable.
Recognized read tools do not create edit-collision gates.

## Neutral policy and host translation

The runtime returns allow/no-objection, ask/review, or deny/unavailable. The adapters
validate that response; missing fields, invalid permissions, crashes, timeouts or a
missing runtime/helper cannot silently authorize an enabled pre-action.

| Neutral result | Cursor generic pre-tool | Claude Code pre-tool |
|---|---|---|
| No governance objection | No permission override | No permission override |
| Owner review needed | Deny with visible review reason | Ask with permission decision reason |
| Guard unavailable | Deny with repair instruction | Deny with repair instruction |
| Passive warning | Non-blocking context/follow-up | Non-blocking system message |

As checked on 2026-09-07, Cursor documents that generic `preToolUse` does not enforce
`ask`; its adapter therefore blocks instead. See the
[Cursor hook contract](https://cursor.com/docs/hooks#pretooluse).
This does not mean the owner rejected the action. Reconcile the collision or have the
owner perform the reviewed action outside the agent hook; do not loop, disable the
guard speculatively, or treat a chat message as a machine-readable exception.

Claude's explicit `allow` can skip a permission prompt. No governance objection
therefore returns no permission decision, preserving normal host checks. Review and
denial use `hookSpecificOutput.permissionDecisionReason`. See
[Claude Code decision control](https://code.claude.com/docs/en/hooks#pretooluse-decision-control).
Do not equate an adapter JSON test with a live client's honoring that decision.

## Command classification

`scripts/hook_policy.py` is the one runtime-owned classifier. It tokenizes without
executing the command, understands common Git global options (including attached
values), and inspects literal Git in compound commands, transparent wrappers and
bounded shell command bodies.

History/worktree-changing or ambiguous commands require review: resets, forced cleans,
restore/checkout paths, rebase/merge, branch/tag deletion, worktree removal, stash
drop/clear/pop, forced/deleting pushes and unknown Git subcommands/aliases. Ambiguous
checkout operands cannot safely be classified as branch names without repository
interpretation, so use an unambiguous non-forced `switch` or request review.
Normal status/diff/log, add/commit, non-forced push and other recognized ordinary
operations do not acquire a new blanket approval requirement.

Unknown Git global-option arity, malformed shell quoting, excessive input or nested
evaluation cannot become a guessed safe command. The scanner is deliberately bounded;
it does not resolve aliases, execute scripts, evaluate arbitrary language interpreters,
prove all shell expansions safe or detect every shell-mediated file write. A command
can bypass this surface by using an unmodeled executable or host tool. This is a
guardrail around supported actions, not a security sandbox or general execution proxy.
Host permissions and the owner's scope constraints still apply.

## Failure and operational limits

- Input is capped at 1 MiB. Oversized/invalid enabled pre-action input denies without
  echoing its content. Action fields must have the expected types.
- Git root lookup is bounded to one second and the runtime call to seven, inside the
  configured ten-second host timeout. Large projects may surface a guard-unavailable
  result; measure latency before changing either budget.
- Child stderr, payloads, environment values and command contents are not echoed on
  transport failure. Runtime reasons are schema/length checked.
- Passive failures warn; even a malformed runtime denial cannot turn Stop into a
  blocking loop. No approval, waiver, test receipt or phase transition is synthesized.
- The runtime serializes state writes. Pre-action inventory is read-only, but external
  writers can still change ownership after the check: this is not a filesystem lock
  across execution.
- Python/the wrapper must actually run. Cursor's pre-tool entry retains `failClosed`;
  an absent interpreter, host ignoring hooks, disabled hooks or unsupported tool
  surface cannot be repaired by wrapper code. Claude has host-specific failure
  semantics; verify installation and native behavior on every supported deployment.
- Runtime and snapshot privacy/recovery limits still apply. Hook transcripts are not
  an authenticated owner identity or independent engineering assurance.
