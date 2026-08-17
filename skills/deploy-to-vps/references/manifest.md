# The automation manifest — reference

An automation is **a folder plus a manifest**. The folder holds the code; the manifest,
a file called `automation.yaml` at the top of that folder, tells `deploy` everything it
needs to put the automation on the box and keep it running.

Loaded on demand when writing or reviewing an `automation.yaml`. A ready-to-copy
annotated example lives at `templates/automation.yaml`.

## The whole file at a glance

| Section | Required | What it settles |
|---|---|---|
| `name` | yes | the short handle used for the folder, the schedule and the logs |
| `description` | yes | one plain-English sentence, shown wherever the automation is listed |
| `owner` | yes | the person it runs as, and whose Claude seat and credentials it uses |
| `source` | yes | where the real copy of the code lives |
| `runtime` | yes | what has to be installed, and what one run executes |
| `schedule` | yes | when it fires |
| `credentials` | no | which sign-ins get copied onto the box |
| `claude` | no | whether it needs Claude Code signed in on the box |

---

## `name`

The short handle for this automation.

- **Allowed:** lowercase letters, digits and hyphens (kebab-case). Keep it under about
  30 characters. Unique per box.
- **Example:** `inbox-brief`
- **What deploy does:** everything on the box is named from it — the folder
  `/home/automations/inbox-brief/`, the two schedule files
  `automation-inbox-brief.service` and `automation-inbox-brief.timer`, and the log
  command `journalctl --user-unit automation-inbox-brief`. Deploying the same name twice
  replaces the existing automation rather than making a second one, so a rename creates a
  new automation and leaves the old one running — use `remove` on the old name.

## `description`

One sentence saying what it does, written for someone who has never seen it.

- **Allowed:** any single line of plain English.
- **Example:** `Emails me a morning brief of my inbox.`
- **What deploy does:** writes it into the schedule file as the unit description, so it
  shows up in `status` and in the logs instead of a bare name.

## `owner`

The person whose seat the automation runs on.

- **Allowed:** one email address.
- **Example:** `you@example.com`
- **What deploy does:** three things. It syncs credentials from **that person's**
  machine; if `claude.setup_token` is on, it signs Claude Code in on the box against
  **that person's** Claude subscription, so the usage lands on their seat; and it names
  the owner in `status` so it is clear who to ask when something breaks. Deploy
  checks the owner is the person actually running the deploy, and stops to ask if not.

## `source`

Where the real copy of the code lives — the copy that gets edited, not the copy sitting
on the box.

| `type` | `location` is | Example | What deploy does |
|---|---|---|---|
| `local` | a folder on the owner's own computer | `~/automations/inbox-brief` | copies the folder onto the box over SSH each deploy |
| `github` | a GitHub repo, as `owner/repo` | `my-automations/servicem8-morning-check` | clones the latest commit onto the deployer's machine, then copies it onto the box over SSH |

Use `local` for something being built and changed on one computer. Use `github` once
more than one person touches it, or once the history matters. Either way the box itself
never holds anyone's GitHub login — the code always arrives over SSH from the deployer's
machine, and a redeploy just repeats that.

**No repo yet?** The skill can create one: a **private** GitHub repo under the owner's
account, first commit pushed, and the manifest switched to `type: github` with the new
`owner/repo` in `location` — after checking the folder holds nothing credential-shaped,
which it must not.

## `runtime`

What has to be installed on the box, and what a single run actually executes.

```yaml
runtime:
  kind: script          # script | claude-code | playwright
  command: ./run.sh     # relative to the automation folder
  packages: [jq]        # optional apt packages
```

- **`kind`** — which of the three supported runtimes this needs. `script` is a plain
  program in any language; `claude-code` runs Claude Code headless, with no one watching;
  `playwright` drives a real browser with no window on screen. (`agents-sdk` is reserved
  for later and is not accepted yet.) What each one installs, and its honest limits, is
  in `references/runtimes.md` — read that before choosing `playwright`.
- **`command`** — the one thing a run executes, written relative to the automation
  folder. It must be executable (`chmod +x run.sh`) and start with `./`.
  **Example:** `./run.sh`. Deploy puts it in the schedule file as the command to start.
  A run is one-shot: it starts, does its work, exits. Exit code 0 means success;
  anything else marks the run failed and shows up in `status`.
- **`packages`** — extra Ubuntu software the command needs, by apt package name (apt —
  Ubuntu's software installer). **Example:** `[jq, ripgrep]`. Deploy installs them once
  on the box. Leave it as `[]` unless something is genuinely missing; the runtime's own
  pieces (Node, the browser, Claude Code) are installed by `kind`, not listed here.

## `schedule`

When it fires. Two lines, both required.

```yaml
schedule:
  calendar: "*-*-* 07:00:00"
  plain: Every morning at 7am (box time).
```

- **`calendar`** — a systemd OnCalendar expression. **systemd timer** — the server's
  built-in alarm clock, which runs a job on a schedule and logs every run. The expression
  is `DayOfWeek Year-Month-Day Hour:Minute:Second`; `*` means "every".
- **`plain`** — the same schedule in a sentence. Deploy reads this back during the
  confirm step and shows it in `status`, so it is what most people will actually read.
  Keep the two honest with each other.

Worked examples:

| `calendar` | `plain` |
|---|---|
| `*-*-* 07:00:00` | Every morning at 7am (box time). |
| `Mon..Fri *-*-* 09:00:00` | Every weekday at 9am. |
| `*-*-* *:00/30:00` | Every 30 minutes, on the hour and on the half hour. |
| `Mon *-*-* 08:00:00` | Every Monday at 8am. |
| `*-*-01 06:00:00` | The first of every month at 6am. |

Check any expression before deploying — this prints the next times it would fire:

```bash
systemd-analyze calendar "Mon..Fri *-*-* 09:00:00" --iterations=3
```

Two things worth saying out loud:

- **Missed runs catch up.** Timers are installed with `Persistent=true`, so a run that
  was due while the box was off fires as soon as the box is back, once, then returns to
  the normal schedule.
- **"Box time" is the box's clock, not yours.** A fresh Ubuntu box runs on UTC. Check it
  with `timedatectl` over SSH and set it once if local time is wanted:
  `sudo timedatectl set-timezone Australia/Brisbane`. Agree the timezone when you agree
  the schedule.

## `credentials`

Sign-ins the automation needs — API keys, CLI config folders, MCP server settings, the
saved login of a browser automation's own service account.

```yaml
credentials:
  - from: ~/.config/gws/        # on the owner's computer
    to: .credentials/gws/       # on the box, inside the automation folder
```

The model is **declare-and-sync**: the manifest only *names* what is needed. The actual
secret is never in the manifest, never in the repo, never in a shared folder, and is
never printed in output or logs. The standing rule: **credentials move
programmatically, never through the model's context** — file to file, down the SSH
pipe, under `umask 077`.

- **`from`** — the path on the owner's own computer. A file or a folder. Resolve it from
  the home folder (`~/...`), never as `/Users/someone/...`, so the same manifest works on
  anyone's machine.
- **`to`** — where it lands on the box, relative to the automation folder. It must sit
  under `.credentials/`.
- **What deploy does:** copies it over SSH straight into
  `/home/automations/<name>/.credentials/`, then locks it down — the folder is mode 700
  and every file inside is mode 600, owned by the `automations` user (mode 600 — readable
  and writable by that one user, invisible to anyone else on the box). Nothing goes near
  a repo on the way. Add `.credentials/` to the automation's `.gitignore` so an
  accidental commit is impossible.

**The special file `.credentials/env`.** If it exists, its `KEY=value` lines are loaded
as environment variables for every run, so the command can read a key without a file path
baked into it. It is optional — a missing one is not an error. Sync it like anything
else, with `to: .credentials/env`.

**Honest edge: keystore-held credentials need one extra move.** A tool that keeps its
sign-in behind an OS keystore — the macOS keyring, Windows Credential Manager; the `gws`
Google CLI is the one we hit first — has one piece that isn't a file. Deploy handles it
invisibly where the tool can export: it asks the tool for its own credentials
programmatically, redirects them straight into a scratch file (never showing them),
syncs that file to the box, deletes the scratch copy, and switches the tool to its
file-based store there — for gws, `gws auth export --unmasked` into a
`credentials.json`, the OAuth client's `client_secret.json` synced next to it (both
files, or the box gets a misleading `403` about project permissions), plus the two
`GOOGLE_WORKSPACE_CLI_*` environment variables in `.credentials/env`. That path is
OS-portable: it works the same from a Mac or a Windows machine. Only when a tool offers
no export does deploy fall back to a one-off browser sign-in **on the box** during
deploy — and it will say so, rather than silently producing an automation that fails at
7am.

## `claude`

```yaml
claude:
  setup_token: false
```

Set `setup_token: true` when the automation runs Claude Code on the box. At deploy time
the owner signs in to their own Claude account in a browser and deploy mints a **setup
token** — the one-time code that signs Claude Code in on the box — and stores it under
`.credentials/`, mode 600. It is never displayed, logged or echoed back.

The rules around it are firm:

- **Per owner, always.** The token comes from the subscription the `owner` is signed in
  to. Their automations spend their seat's usage.
- **Never one org-wide token** shared by every automation on the box. When one seat's
  limits are outgrown, the fix is more seats with automations spread across owners —
  that is the intended way to scale, and it only works if each automation carries its
  own owner.
- **Never an Anthropic API key.** Subscription setup tokens only. If an automation looks
  like it wants an API key, that is a design problem to raise, not a value to paste in.

Leave it `false` for anything that does not run Claude Code.

---

## A complete manifest

A daily ServiceM8 morning check: Claude reads yesterday's jobs and today's bookings out
of ServiceM8 and emails the owner what needs attention.

```yaml
name: servicem8-morning-check
description: Emails a 7am rundown of yesterday's jobs and today's bookings.
owner: you@example.com

source:
  type: github
  location: my-automations/servicem8-morning-check

runtime:
  kind: claude-code
  command: ./run.sh
  packages: [jq]

schedule:
  calendar: "*-*-* 07:00:00"
  plain: Every morning at 7am (box time).

credentials:
  - from: ~/.config/servicem8/credentials.env
    to: .credentials/servicem8/credentials.env
  - from: ~/.config/deploy-to-vps/mail-sender.env
    to: .credentials/env

claude:
  setup_token: true
```

On the box that becomes the folder `/home/automations/servicem8-morning-check/`, the
units `automation-servicem8-morning-check.service` and `.timer`, and logs read with
`journalctl --user-unit automation-servicem8-morning-check`.
