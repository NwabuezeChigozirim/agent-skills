# Wave 6 — Hook reliability, behavioral evaluation and release readiness

Start authority: the owner's “Proceed to wave 6”. Baseline: pushed Wave 5 commit
`d4a9c2e35d0f586af450e22b8df88e7c1f4f27cd`; the source worktree was clean.

## Contract

Complete the remaining hook-adapter regression work, exercise the suite's behavior
independently in isolated scenarios, and assess compatibility/release evidence.
Preserve default legacy policy, explicit project opt-in, owner authority, immutable
recovery/stage history, read-only inspection, and non-blocking turn completion.

Classify command strings without executing them. Enabled pre-action failure must
never become an approval. Translate neutral policy to each host's actual supported
permission behavior without overriding unrelated host permissions. Keep detailed
mechanics outside the skill entrypoints. Do not install hooks in the source checkout,
upgrade a live project, or infer commit/push/release authority from wave progression.

## Implementation

- Replaced regular-expression command matching with a bounded, non-executing token
  classifier. Literal Git commands, global options, transparent wrappers, command
  chains and bounded shell bodies receive explicit treatment. Unknown Git aliases,
  destructive operations and ambiguous forms require review. Malformed, conflicting
  or missing action fields cannot silently authorize a known tool action.
- Consolidated installed adapter transport in `hooks/hook_support.py`. Activation
  precedes runtime lookup; disabled projects remain no-ops. Explicit stale runtime
  overrides do not fall back to another installation. Enabled pre-action transport
  failures deny; passive events warn without blocking turn completion. Payloads and
  runtime duration are bounded, and failures do not echo payloads or child stderr.
- Kept policy decisions in the runtime and host translation in the adapters. Neutral
  no-objection returns `{}`, preserving the host's own permissions. Claude uses its
  permission-decision contract; Cursor maps review to denial because its generic
  pre-tool hook does not enforce `ask`. Operators must resolve the review explicitly;
  denial is not permission to retry through another tool.
- Direct edit ownership checks now use fresh read-only worktree inventory and resolve
  relative targets against the reported working directory. Stale discovery cannot
  hide a newly competing worktree. Unverifiable ownership does not authorize edits.
- Hook installation verifies all required source assets before copying and installs
  the shared helper beside both wrappers. Packaging validation requires both new
  modules. Existing hook enablement and installation remain explicit operations.
- Fixed installed-hook tests to select the checkout's runtime explicitly. Their
  previous reliance on a developer's global installation caused actual clean-host
  CI failures, not merely a theoretical portability concern.
- Added focused adapter/classifier/installation tests and promoted the last two
  original review regressions from expected failures to ordinary passing tests.
  Added three behavioral scenario definitions; definitions alone are not executions.
- Kept detailed mechanics in routed references. Following skill-creator's independent
  forward-testing guidance exposed a small audit ergonomics issue: use
  `git --no-optional-locks` for read-only probes and put global `--json` before the
  runtime subcommand. No broader discovery or planning redesign was introduced.

## Preserved boundaries and limitations

Default policy remains 1 and `CURRENT_POLICY_READY` remains false. This wave neither
releases policy 2 nor upgrades a project. Owner authority, legacy opt-in, stage and
recovery history, specification/planning gates and non-blocking Stop behavior remain
intact. No governance state, hooks or recovery refs were installed in this source
checkout. Generated evaluation artifacts belong to disposable test repositories.

Command classification is not a shell interpreter or a security sandbox. It does not
comprehensively inspect script contents, dynamically selected executables, shell
aliases or shell-mediated file writes. Direct edit ownership checks do not become a
general filesystem access-control system. These limits are documented rather than
hidden behind a claim of complete enforcement.

## Deterministic verification

All check-runner components completed successfully in local component runs:

| Component | Passing tests |
|---|---:|
| Governance runtime and packaging | 43 |
| Specification | 29 |
| Planning | 36 |
| Change impact | 31 |
| Graph contracts | 27 |
| Hook guards | 21 |
| Policy upgrade | 22 |
| Recovery | 26 |
| Original review regressions | 12 |
| Stage contracts | 31 |
| **Python total** | **278** |
| Renderer, including PDF/page images | **4** |

There are no remaining expected-failure decorators in the test suite. The final
host-specific runtime-preference refinement was followed by another successful
21-test hook-guard run. Suite validation, all three skill frontmatter validators and
`git diff --check` also passed. Environment: Linux, Python 3.12.3, Node 22.22.1;
renderer dependencies were reused from an isolated existing installation.

The initial serial `scripts/check.py` invocation was interrupted across a resume;
remaining components were run separately and their successful exits captured. This
record does **not** claim a completed single aggregate invocation or a local macOS /
Python 3.10 matrix run.

The pushed Wave 5 [CI run](https://github.com/NwabuezeChigozirim/agent-skills/actions/runs/34093750544)
passed rendering but failed all four Python jobs. The inspected Linux 3.12 log showed
installed-hook tests using the wrong/missing runtime on a clean host. Explicit test
runtime selection addresses that demonstrated cause and passes locally. The exact
Wave 6 candidate has not been pushed or run in hosted CI; a green matrix remains
required evidence, not an inferred result of this fix.

## Behavioral and host evidence

See [the forward-check record](wave-6-forward.md) for raw requests, condition
fingerprints, observed outcomes and limits. The paired baseline/candidate sample
preserved three useful behaviors: evidence-based refusal to claim legacy readiness,
distinguishing a requested map from the underlying economic need, and stopping
governance planning when authoritative inputs are absent. Candidate audit probes also
left Git metadata unchanged. A single pair is not a statistical efficacy claim.

The separate positive planning check produced one complete vertical slice from valid
inputs, with traceable requirements, explicit future evidence and owner-gated wave
status. The evaluator wrote only the three authorized planning documents. Independent
inspection and current-checkout plan/specification/trace validation all passed; the
canonical inputs and legacy policy remained unchanged. This is useful evidence that
the planning boundary supports productive work, not only refusal. It is one legacy
scenario, not policy-2 acceptance, and is not counted among deterministic tests.

Native Claude evidence includes a real permission denial for the review probe and
non-blocking Stop output. Neutral no-objection did not override the host's own
permission check. Cursor reported an ordinary command succeeding and the review
probe being blocked, but did not exit before the outer deadline. This is partial
native evidence, not a clean end-to-end compatibility pass or interactive approval
validation. No permission bypass was used to force a pass.

## Release assessment and handoff

Local implementation and deterministic verification are complete. Policy-2 release
acceptance remains **pending**. Before releasing it, obtain a green hosted matrix
for the exact candidate, clean Cursor completion and appropriate interactive review
evidence, and an owner assessment of representative behavior/adoption evidence.
Any further compatibility fix must preserve failure-to-deny, disabled no-op, host
permission independence and passive-event completion; retest those invariants.

Wave progression does not authorize commit, push or policy activation. All Wave 6
changes remain uncommitted and unpushed at this handoff. The next bounded step is
owner review and explicitly authorized publication for candidate CI, followed by
release assessment—not an automatic additional implementation wave or policy flip.

Source fingerprint:
`ecd89138cb1ef7fc85640a0ce95cf653e1a25f9b1e9b28e8fc40bb6810b24cd2`.
The fingerprint excludes only this file to avoid self-reference; it covers tracked
and non-ignored untracked source files using sorted path-qualified SHA-256 entries.

```bash
git ls-files --cached --others --exclude-standard -z -- . ':(exclude)docs/evolution/wave-6.md' | sort -z | xargs -0 sha256sum | sha256sum
```
