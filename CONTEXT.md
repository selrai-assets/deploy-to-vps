# deploy-to-vps

One skill that gives a person an always-on Linux server and puts their automations on it,
on a schedule. This glossary fixes the words used across the skill, the kit's member-facing
surfaces, issues and ADRs, so the same thing is not called three names.

## Language

**Box**:
One provisioned server this skill manages, tracked by its own local box record.
_Avoid_: instance, droplet, machine, node. (Member-facing prose still says "server" or "VPS" in plain English — "box" is the internal term.)

**Automation**:
A unit of work with an owner that runs on a schedule on the box.
_Avoid_: job, task, script, bot.

**Manifest**:
The one file inside an automation that states what it is, who owns it, what it needs, and when it runs.
_Avoid_: config, spec, descriptor, metadata file.

**Verb**:
One of the skill's six top-level operations a person can ask for — provision, connect, deploy, status/logs, scale, remove.
_Avoid_: command, mode, action, workflow.

**Kit**:
The GitHub repo a Skool member clones, whose deliverable is the skill plus its setup prompt.
_Avoid_: package, bundle, template, download.

**`automations` user**:
The single Unix user on the box that owns every automation; per-person SSH keys decide who may deploy.
_Avoid_: service account, deploy user, shared login.

**Setup token**:
The credential that lets one automation run Claude on the box under its owner's own subscription.
_Avoid_: API key, auth key, Claude key, org token.
