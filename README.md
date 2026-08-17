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
examples/
  inbox-clearer/      # a working demo automation: folder + manifest, deployable as-is
research/             # scoping docs (not part of the skill)
```

`examples/inbox-clearer/` is both the server's first real job and the worked example to
copy when writing your own: it files notification noise out of the Gmail inbox and emails
an HTML brief of what was cleared and what needs attention. See its README.

Agreed scope lives in `research/2026-08-14-skool-v1-shared-understanding.md`. If later
work contradicts it, update that file deliberately or treat the work as out of scope.

Server lifecycle verbs need a working `aws` CLI login with write-level access, and the
skill sets that up itself — `skills/deploy-to-vps/references/aws-setup.md` goes from no
AWS account at all to a configured CLI, so there is no dependency on an external `aws`
skill. Deploying to an existing box needs only SSH.
