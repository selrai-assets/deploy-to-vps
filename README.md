# deploy-to-vps

One place to deploy any automation onto an always-on, hardened Linux VPS on AWS EC2 —
so scheduled jobs stop depending on someone's home desktop being awake.

The deliverable is a single Claude skill:

```
skills/deploy-to-vps/
  SKILL.md            # the six verbs: provision, connect, deploy, status/logs, scale, remove
  references/         # manifest format, runtime catalogue
  templates/          # example manifest + systemd unit templates
  scripts/harden.sh   # idempotent box hardening
research/             # scoping docs (not part of the skill)
```

Agreed scope lives in `research/2026-08-14-skool-v1-shared-understanding.md`. If later
work contradicts it, update that file deliberately or treat the work as out of scope.

The skill assumes an `aws` skill (or an equivalent working `aws` CLI login with
write-level access) for server lifecycle verbs; deploying to an existing box needs only
SSH.
