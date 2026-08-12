# deploy-to-vps

A generalised, team-agnostic Claude skill: one place to deploy any automation onto a Linux VPS (AWS EC2). Repo layout mirrors a team layer (`skills/deploy-to-vps/SKILL.md` + supporting files) so it drops into any team's Claude base as a copy + sync. Agreed scope lives in `research/2026-08-12-shared-understanding.md`.

## Agent skills

### Issue tracker

Issues live in Linear — Client Delivery team, Ark Bathrooms ASA project — via the Linear MCP tools. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical labels, used verbatim (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`); the Linear team already carries them. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root, created lazily. See `docs/agents/domain.md`.
