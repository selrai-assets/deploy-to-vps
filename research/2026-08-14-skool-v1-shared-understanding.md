# deploy-to-vps — Skool v1 shared understanding

Date: 2026-08-14. Product of a grilling session (Harvey + Claude). This document defines
**v1-for-Skool**: the delta between the live-proven skill (CD-202, done 2026-08-12) and a
kit ready to drop into the Skool community. If later work contradicts it, update this
file deliberately or treat the work as out of scope.

Supersedes `research/2026-08-12-shared-understanding.md` (deleted in the same change).
That doc's content is fully condensed into Linear CD-202, with one stale bullet there
corrected 2026-08-14: gws credential sync is the **export method**, not the keychain
transplant (see §5 below).

## The reframe

Audience change: Ark team layer → general Skool members — non-technical business owners
with no team layer, no `aws` skill, no Ark context. Only two clients have a team setup
and one is in Skool; the kit assumes neither. The six verbs, live-proven 2026-08-12,
stay functionally untouched: v1-for-Skool is packaging, voice, and self-containment.

## The delta — what v1 adds or changes

1. **Kit shape.** `SETUP-PROMPT.md` at repo root (agent-facing installer, house
   pointer-prompt pattern: members paste "Clone <repo> and follow SETUP-PROMPT.md" into
   Claude Code) plus a member-facing README rewrite. No selr-kit-index entry. The Skool
   classroom (product name **The Always-On Server**) is a separate later effort — kit
   quality comes first.
2. **AWS self-containment.** New `references/aws-setup.md`, distilled from the proven
   `claude-workshop-kit/skills/aws-connector` choreography (588 lines, already generic).
   Flow: Claude opens the AWS signup page in the member's default browser → they sign up
   themselves (Claude answers plan questions) → Claude drives everything after sign-in
   via Playwright — `claude-assistant` IAM user, **PowerUserAccess not Admin**, root
   keys refused and deleted if found — → CLI installed and configured, region asked, not
   assumed (the connector's `us-east-1` hardcode does not carry over). Rejected
   alternative: bundling the connector as a second skill in the kit — the kit stays one
   skill; only enough AWS to spin up this server, and extraction later is cheap if a
   second kit ever needs it.
3. **Full de-Ark.** All Ark references stripped from this repo: the README's team-layer
   drop section, `docs/routines-decision.md` pointers, the Ark persona by name. Routines
   stay as a generic alternative. Ark's own copy is never touched — not Selr's to edit
   absent a new engagement. Edits are **prose-only**: any edit that would change a
   command or step behaviour is scope creep and gets flagged instead.
4. **Deploy verb reshaped.** The `team` source type is gone. Deploy takes an automation
   the user namedrops, finds it on the system, or builds it fresh as Claude normally
   would if it doesn't exist. Local folder and GitHub sourcing remain.
5. **Credential recipe corrected.** The gws Gotcha becomes the OS-portable export
   method: `gws auth export --unmasked` redirected straight to a file (umask 077, never
   printed), synced file-to-file over SSH into the automation's `.credentials/`, file
   keyring backend on the box; browser re-auth on the box as fallback. This replaces the
   Mac-only keychain-transplant recipe from the 2026-08-12 proof — the export method is
   the later, round-trip-tested conclusion and works Mac→Linux and Windows→Linux.
   Standing rule made explicit in the skill: **credentials move programmatically, never
   through the model's context.**
6. **Generic demo automation.** `examples/inbox-clearer/` — a folder + manifest exactly
   as a member's own automation would be. It triages notification noise (Hubstaff,
   GitHub, Linear and the like) out of the inbox — labelled, marked read — so only
   actual messages remain, then emails an HTML brief of what was cleared and what needs
   attention. **Email only: no calendar, no CRM.** Zero harveyisms: recipient discovered
   from whoever's signed in, labels resolved by name not ID, no personal branding.
   Derived from the generalised morning-brief fork
   (`claude-workshop-kit/skills/morning-brief`, newest) and its `render_brief.py`
   renderer pattern, trimmed to email-only.
7. **Docs.** Thin `CONTEXT.md` glossary (box, automation, manifest, verb, kit, the
   `automations` user, setup token — one line each, no implementation detail). Two ADRs,
   filtered through the hard-to-reverse ∧ surprising-without-context ∧ real-trade-off
   test: **EC2 over Lightsail** and **subscription setup tokens, never API keys, never
   an org-wide token**. Withdrawn candidates: single-skill packaging (cheap to reverse),
   systemd-over-cron and folder+manifest (reasoning already inline in SKILL.md).
8. **Repo home.** Transferred, history preserved, to the `selrai-assets` GitHub org —
   the new home for Skool kit repos. Private for now; flipped public at ship day (the
   pointer-prompt install needs it clonable by members).
9. **The proof.** Fresh t4g.small provisioned on Harvey's account through the skill's
   own provision path; inbox-clearer deployed under his identity on a systemd timer at
   **7:00, 12:00, and 15:00 Australia/Brisbane, Monday–Friday**. Success is the real
   side effect: noise actually leaves the inbox and the brief actually arrives. The box
   **stays up** — built to last, the standing home for Harvey's own automations and the
   demo environment for the later classroom build. (The AWS-from-zero signup path can't
   be tested from an already-configured machine; the first real member run is its test,
   as with every kit's install prompt.)

## Settled decisions (session record)

- Research doc: deleted once condensed; docs in the repo stay minimal, but thin
  `CONTEXT.md` + ADR layers are welcome.
- One skill, not two (AWS distilled in — Harvey's call, twice).
- IAM stance kept: dedicated `claude-assistant` user, root keys refused.
- Friendly Skool name: **The Always-On Server**; repo/skill name `deploy-to-vps`
  unchanged.
- Member-facing language pass on new surfaces only (README, SETUP-PROMPT, classroom
  copy later); the proven SKILL.md voice stays, bar de-Ark edits.
- No fresh live proof of the six verbs (edits are prose-only); the inbox-clearer
  deployment is the real-world verification.
- No new Linear issue yet — this file is the scope record until Harvey says otherwise.

## Facts discovered during grilling (verified 2026-08-14)

- **Kit conventions:** a Selr kit is a GitHub repo whose deliverable is the skill(s) +
  `SETUP-PROMPT.md`; members paste a one-line pointer prompt, never zips or typed
  commands. Reference kit: `~/selrai/products/brain-builder`. Drop assets live in
  `~/selrai/active/<kit>-drop/`; classroom states "coming soon" (no install link) and
  "ship day" are explicit and distinct. Skool copy rules: no em/en dashes, never say
  "free".
- **aws-connector prior art:** fully generic, no Ark content; covers install → sign-in
  poll → IAM wizard → key mint via DOM extraction → config write → root hard-gate. Gaps
  for our use: no account-signup step, `us-east-1` hardcoded.
- **morning-brief:** Harvey's triage logic is a Claude skill, canonical at
  `~/selrai/products/online-course-skills/morning-brief/` (personal, hardcoded label
  IDs) with generalised forks in the workshop kits; renderer
  `scripts/render_brief.py` exists and is mandatory-never-inline. **It has never run on
  a schedule** — no crontab/launchd; the Jul 8 Claude scheduled-task points at a skill
  installed in no loadable layer; all dated briefs were manual runs. This deployment
  closes that exact gap.
- **gws recipe conflict:** the SKILL.md Gotchas (keychain transplant, proven 2026-08-12)
  contradicted the later round-trip-tested export method in Harvey's memory
  (`reference_gws_routine_restore`). Resolved in favour of export (§5).
- **GitHub orgs:** `selrai-assets` exists alongside `selrai-company`; Harvey wants Skool
  repos stored in `selrai-assets`.
- CD-202 otherwise fully condensed the 2026-08-12 research doc — the gws bullet was its
  only stale fact.

## Held / out of scope for v1

- Classroom build (`skool-classroom-builder`) — after the kit is good.
- Public repo flip — ship day.
- Kit-index YAML entry — dropped.
- Ark's copy of anything — never touched.
- Agents SDK runtime — still just a name the manifest may use later.
