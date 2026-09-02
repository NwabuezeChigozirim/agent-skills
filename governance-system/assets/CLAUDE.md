# Claude Code Project Entry Point

Read [AGENTS.md](AGENTS.md) first. It is the canonical platform-neutral session guide.

Claude Code-specific rule: project hooks under `.claude/settings.json` enforce active
governance gates when `.governance/config.json` enables them. Hook success never grants
permission for a gated wave, destructive Git operation, deployment, or stage closure;
the owner must still authorize those actions explicitly.
