---
name: govern
description: "Default entry point for any non-trivial task under governance: restate the goal, match the task to a playbook, run it as a stage with frozen checks, real-app proof and an independent verdict. Use for /govern, or when asked to work in a governed, verified way."
disable-model-invocation: true
---

# Govern

Bundled skills live at `../<name>/SKILL.md` from this file. Scripts live at `../../scripts/`. Put this file's absolute path in every subagent brief so the subagent can find them.

## Non-negotiables

- **Your first message on a task** tells the owner, in your own words, their goal, the problem they are solving, and the smallest change you expect to meet it (the **in-your-own-words** skill). Repeat the goal in each subagent brief and at the top of your final report.
- **Any change that ships behavior runs as a stage** (the **stage** skill). No stage, no claim of done.
- **Done means proven on the real artifact** (the **principle-prove-it-works** skill): driven through the project's `verify-<app>` skill, sealed with `verifyctl`, and confirmed by `stagectl close`. "It compiles" and "tests pass" are not done. If no `verify-<app>` skill exists, run **create-verification-skill** first.
- **The owner approves once per stage.** Show them the intent, the acceptance list and the check commands, then ask them to run the `stagectl freeze ... --owner-approved` command themselves. The hook blocks you from running it. After that, do not ask "should I do X?" on reversible work: proceed, and report. Ask only for irreversible actions and for product calls no experiment can settle.
- **An author does not judge their own change.** Stages with `review: independent` get their verdict from a fresh agent in its own worktree (the **verify-stage** skill).
- **When the owner corrects you**, fix the mistake, then run the **correct** skill so the repo makes the mistake impossible. A rule that only lives in prose is not in force.
- **Never weaken a check, an acceptance item or a feature-map journey to make it pass.** A failure is a finding. Fix the root cause or report it.

## Playbooks

Open a todo list whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to one playbook and open `playbooks/<name>.md`.

- **Feature** (`playbooks/feature.md`). New or changed behavior.
- **Bug fix** (`playbooks/bug-fix.md`). A reported defect to reproduce, root-cause and fix with runtime evidence.
- **Refactor** (`playbooks/refactor.md`). A change to structure that must not change behavior.
- **Investigation** (`playbooks/investigation.md`). A read-only question. No stage, no code change.

Work larger than one reviewable unit is split first (the **principle-sequence-verifiable-units** skill): one stage per unit, each in its own worktree when run in parallel. If no playbook fits, say so, propose the steps and their checks, and run them as a stage.

## Writing the reply

Open with the goal as you restated it. Then: what changed, the stage ID and closure receipt, the independent verdict, and what you could not verify with the reason. Paste check output verbatim where it is the evidence. Never report a skipped or unreachable path as verified.
