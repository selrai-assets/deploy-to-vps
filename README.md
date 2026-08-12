# deploy-to-vps

One place to deploy any team automation onto an always-on, hardened Linux VPS on AWS
EC2 — so scheduled jobs stop depending on someone's home desktop being awake.

The deliverable is a single Claude skill, laid out to mirror a team layer:

```
skills/deploy-to-vps/
  SKILL.md            # the six verbs: provision, connect, deploy, status/logs, scale, remove
  references/         # manifest format, runtime catalogue
  templates/          # example manifest + systemd unit templates
  scripts/harden.sh   # idempotent box hardening
research/             # scoping docs (not part of the skill)
```

Agreed scope lives in `research/2026-08-12-shared-understanding.md`. If later work
contradicts it, update that file deliberately or treat the work as out of scope.

## Dropping it into a team layer

The layout mirrors `~/ark-claude-setup/skills/`, so the merge is a copy, not a port:

1. `cp -R skills/deploy-to-vps ~/ark-claude-setup/skills/`
2. `/sync` from any session on the team layer.
3. Update the team's `docs/routines-decision.md` §7, which currently says the
   always-on server "lives in a separate advanced kit". Suggested replacement for that
   sentence:

   > That setup now lives in the **deploy-to-vps** skill: one place to provision a
   > hardened always-on server on AWS and deploy any automation onto it — plain
   > scripts, headless Claude Code, and browser automations. Ask Claude to "set up a
   > server for the team" to start. Most users still never need this; routines remain
   > the right home for simple wake-run-stop jobs.

The skill assumes the team's `aws` skill (or an equivalent working `aws` CLI login
with write-level access) for server lifecycle verbs; deploying to an existing box
needs only SSH.
