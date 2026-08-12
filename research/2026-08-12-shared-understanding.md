# deploy-to-vps — shared understanding

Date: 2026-08-12. Product of a grilling session (Harvey + Claude, live in the room with
Ark/OA) before any code was written. This document is the agreed scope and design
context. If later work contradicts it, either update this file deliberately or treat the
work as out of scope.

## What it is

A **generalised, team-agnostic skill**: one place to deploy any automation onto a Linux
VPS. Owned by Harvey (Selr) first — private repo `deploy-to-vps` on **harvey-selr** —
and designed to be dropped into any team's Claude layer later (Ark/OA first) as a
straight copy + sync.

- Repo layout mirrors a team layer: `skills/deploy-to-vps/SKILL.md` + supporting files,
  so merging into e.g. `~/ark-claude-setup/skills/` is a copy, not a port.
- OS-agnostic on the operator side (Mac/Windows/Linux). The box itself is Linux.
- Speaks non-technically, per the Ark team persona: real names for things, defined once
  in one short line, nothing hidden — **explained, not abstracted away**. The users are
  not developers.

## Why a VPS (vs Claude cloud routines)

- Routines make CLIs hard to use; a VPS runs plain scripts, CLIs, long-lived processes,
  browser automations — anything. Routines stay as a second option/fallback.
- One place where a team deploys everything; starts small, scales up.
- The Ark team layer's canonical `docs/routines-decision.md` §7 already names an
  "always-on server on AWS" as a separate advanced kit — this skill *is* that kit. At
  merge time, that doc gets updated to point here.
- Tension acknowledged: the Ark engagement agreed "everyday devices, not transferred
  desktop setups — the gap is distribution, not capability". A VPS is a deliberate
  scope extension (automations shouldn't depend on someone's home desktop being awake)
  and should be said out loud in the room, not slipped in.

## Platform

- **AWS EC2**, driven by the `aws` CLI. Builds on the existing team `aws` skill's
  connection model (dedicated `claude-assistant` IAM user; needs write-level /
  PowerUserAccess for provisioning). That skill explicitly leaves server provisioning
  as "a separate setup" — this is it.
- **CLI first, browser (Playwright) only as fallback** for what the CLI genuinely
  can't do (e.g. AWS account creation, first console sign-in).
- Defaults: **t4g.small (2 vCPU, 2 GB, ARM), Ubuntu 24.04 LTS, ~US$12–18/mo**, size
  menu offered at provision time (t4g.medium ~US$24/mo for heavier workloads,
  especially browser automations). Region defaults to the deployer's home region.
- Lightsail considered and rejected: simpler pricing but a second-class CLI and walled
  off from the rest of AWS.

## Verbs (v1)

| Verb | What it does |
|---|---|
| `provision` | New box, hardened: SSH-only, firewall, unattended upgrades |
| `connect` | Attach to an existing box; on missing access, diagnose why and generate exact grant instructions for the box owner (both directions — e.g. Abby onto Bryce's box, or vice versa) |
| `deploy` | Automation folder + manifest → box, runtime installed, schedule live |
| `status` / `logs` | What's running, when it last fired, what it said |
| `scale` | Resize the instance when a box needs more power |
| `remove` | Take an automation (or the box) down cleanly |

## What it runs

Anything:

- Plain scripts, any language.
- **Headless Claude Code** running skills/prompts on a schedule.
- **Headless Playwright browser automations** — Playwright ships arm64 Linux Chromium;
  installed as an optional runtime with a persistent profile on the box. Caveats the
  skill states honestly: browser workloads want t4g.medium (2 GB is tight for
  Chromium), and bot-defended sites sometimes refuse headless first-time logins — the
  pattern is a dedicated service user on the target site, signed in once, profile
  persisted.
- **Claude Agents SDK apps later** — just another runtime the manifest can name. No
  framework code in v1; the deploy convention is designed so it drops in.

Scheduling via **systemd timers** (journald logs, catch-up semantics), not cron.

An **automation is a folder + a small manifest**: what it is, who owns it, where its
source lives, what runtime it needs, its schedule, which credentials it declares.
Source is versatile by design: a local folder, a GitHub repo, a team base (e.g. the Ark
setup repo) — and the skill can create a GitHub repo for an automation when one is
needed.

## Identity & spend — the core rule

- One `automations` Unix user by default; extra users allowed, never locked in.
- Per-person **SSH keys** control who can deploy. No shared login credentials.
- **Never a single org-wide Claude token.** Each automation pairs with its own Claude
  setup token, minted from whatever subscription its **owner** is signed into at deploy
  time. Automation owners spend their own seat's usage. As many subscriptions per box
  as the team likes; when a team outgrows one seat's limits (e.g. Team plan 5×), they
  add seats and load-balance automations across them. No Anthropic API key anywhere —
  subscription setup tokens only.

## Credentials

**Declare-and-sync**: the manifest lists what the automation needs; deploy copies it
from the deployer's machine over SSH, mode 600, into a per-automation location on the
box. Works for any connection type — CLI configs, raw API keys, MCP server configs,
and stored login details for dedicated browser-automation service users. Nothing
credential-shaped ever enters this repo or a team folder.

Known edge (today's demo): `gws` tokens live in the macOS keyring. **Update, verified
during the 2026-08-12 live proof:** re-auth is not needed — the keyring entry can be
extracted programmatically (`security find-generic-password -s gws-cli`) into gws's
file backend (`.encryption_key` in a scratch config dir) and synced to the box, where
gws reads mail with it directly. Browser re-auth into the file backend remains the
fallback if the keychain refuses. The skill's Gotchas table records the exact steps.

## Today's proof (2026-08-12, ~2h window)

1. Build the skill in this repo.
2. Live end-to-end test on Harvey's AWS account (`546105661473`, ap-southeast-2,
   already CLI-connected as IAM user `harvey` with AdministratorAccess): provision a
   t4g.small, deploy a toy automation — gws CLI on the box with Harvey's auth, on a
   systemd timer, pulling his inbox and emailing a brief to harvey@selrai.com.au.
3. Verify it fires, then **tear the box down** — the test box is disposable; the skill
   is the deliverable. (Harvey will later run automations on an existing instance of
   his own, in his own time.)
4. Deploying onto Bryce's/Ark's world is Harvey's job afterwards; the skill just has
   to make it trivial. Ark has **no AWS account yet** — account creation happens on
   their side when it's dropped into their base.

## Facts discovered during grilling (environment, verified 2026-08-12)

- Harvey's machine: `aws` CLI configured, IAM user `harvey`, account `546105661473`,
  AdministratorAccess, default region ap-southeast-2, five EC2 instances already
  running (t4g/t3 family).
- `gh` active account: **harvey-selr**. `gws` 0.22.5 and Claude Code 2.1.228 installed.
- Ark team layer: `~/ark-claude-setup/skills/<name>/SKILL.md`, flat, shared by /sync
  (everyone pushes to main, no review queue). Its `aws` skill: Playwright for one-time
  console setup, then pure CLI; mints `claude-assistant` IAM user; refuses root keys;
  no provisioning capability.
- Bryce (Office Manager, OA side) runs Claude-built automations on his home desktop:
  daily ServiceM8 previous-day checks, daily to-do list checks, 48-hour outstanding
  quote follow-ups. Other teammates have their own builds — the skill must work for
  everyone, not just Bryce.
