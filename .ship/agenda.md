# Batch review agenda — ship/batch-2026-08-17-skool-v1

Batch for CORE-174 (Skool v1, The Always-On Server). Constituent PRs, all reviewed clean and merged here:

| PR | Issue | What | Review outcome |
|---|---|---|---|
| #5 | CORE-178 | CONTEXT.md glossary + two ADRs | 2 findings fixed |
| #6 | CORE-175 | SKILL.md Skool pass (de-Ark, team source, gws export recipe) | 1 finding fixed (missing client_secret.json, live-verified 403) |
| #7 | CORE-177 | inbox-clearer demo (live e2e: 60 filed, brief arrived) | 6 findings fixed (incl. domain-only confirm could file real humans) |
| #8 | CORE-179 | AWS-from-zero reference | 4 findings fixed (incl. root-key deletion ordering, CRLF secret corruption) |
| #9 | CORE-181 | Member README + SETUP-PROMPT.md | 6 findings fixed (incl. wrong price band, access-grant direction) |

CORE-176 (repo transfer to selrai-assets) done outside the diff. CORE-180 (live proof) is not in this batch.

## Resolved in-session (Claude drove)

- Codex verify sweep over the assembled batch: 10/10 in substance (the one nominal fail — no clone URL inside SETUP-PROMPT.md — matches the brain-builder house pattern exactly; URL lives in the README pointer prompt).
- Combined-diff two-axis review (/code-review, fresh contexts). All meaningful findings fixed forward in commit 17cabe5:
  - Demo manifest declared the retired whole-folder gws credential move; now declares the corrected export-method shape (credentials.json + client_secret.json).
  - run.sh now guards on a missing gws CLI with a plain-English error; prerequisite noted in the demo README.
  - PROVISION region step restored to main's proven wording (behaviour change made without a flag; reverted, flagged on CORE-175).
  - README overclaim corrected: the member creates the AWS account themselves, Claude coaches and then drives from sign-in.
  - "box" leak in demo README → "server"; CONTEXT.md Automation entry gained the member-facing "job" gloss (Box precedent); "free" removed from spoken lines of aws-setup.md; BULK_SENDER_LOCALPARTS rename disambiguates filing vs brief-classification patterns.
- Recorded and skipped (unanchored preference on a demo example): renderer row-shape extraction, a Message type for the flattened dict, confirms() loop-ification.

## Harvey drives (human-judgment shortlist)

1. **Copy tone** of README.md and SETUP-PROMPT.md — reads right for a non-technical Skool member? (Taste; unverifiable by tooling.)
2. **Timing claims** in README ("half an hour to two hours" install, "five to fifteen minutes" AWS) are unsupported by any measured run — keep, soften, or cut.
3. **gws-on-the-box decision.** The skill has no documented way to install a non-apt CLI on the server (`packages` is apt-only; only claude-code and playwright have per-kind install recipes). The demo now fails loudly if gws is absent, but the CORE-180 proof deploy must either install gws by hand on the box, or the skill gains a documented step — the latter is a verb behaviour change and needs a deliberate decision.
4. **Calendar group** in the demo config files calendar-reply *emails* (Sender: calendar-notification@google.com). Kept as compliant with "email only"; confirm or cut.

## Attention flags (sensitive surfaces, from PR judgment comments)

- Secrets/env: tripped on #6 (gws export recipe), #7 (credential declaration), #8 (IAM user + access key choreography) — all by design; eyes on the recipes recommended.
- Outbound comms: tripped on #7 (the demo sends the brief email to the signed-in account).
- All other surfaces (migrations, auth beyond the above, payments, deploy/CI config, destructive ops): clear, cited in the PR comments.

## Pre-merge gates

None. No DB migrations, no auto-deploy-on-main. Merge to main is Harvey's call, made explicitly.
