# Runtimes — reference

Loaded during `deploy` when an automation's manifest names a runtime, or when someone
asks what the box can run. A **runtime** is simply the thing on the box that knows how to
execute this automation — a language, a command-line tool, or a browser. The manifest's
`runtime.kind` field picks one.

| `runtime.kind` | What it runs | What deploy installs on the box | Box size |
|---|---|---|---|
| `script` | Plain scripts, any language | Whatever `runtime.packages` lists | t4g.small is fine |
| `claude-code` | Claude, headless, on a schedule | Claude Code, plus the owner's setup token | t4g.small is fine |
| `playwright` | A real browser with no screen | Node.js, Playwright, Chromium | t4g.**medium** |
| `agents-sdk` | Reserved — not built in v1 | — | — |

Two rules apply to every runtime. Anything the automation prints goes to **journald** —
the server's own logbook — and comes back with
`journalctl --user-unit automation-<name>`. And every automation runs as the
`automations` user, which has no admin rights: installs that need admin (`sudo`) are done
once at deploy time over SSH as the `ubuntu` admin user, never by the automation itself.
In the snippets below, `ssh ubuntu@"$BOXNAME"` is that admin sign-in — same key, the
`ubuntu` user instead of the `Host` entry's default `automations`.

---

## `script` — plain scripts, any language

The simplest kind, and the right default. The automation folder holds a script; the
manifest says how to run it; the timer runs it. Nothing else is involved.

```yaml
runtime:
  kind: script
  command: ./run.sh              # relative to the automation folder
  packages: [python3-venv, jq]   # optional; apt package names
```

- `runtime.command` is what one run executes. Deploy marks it executable (`chmod +x`) so
  systemd can start it. Give it a **shebang** — the `#!/usr/bin/env bash` or
  `#!/usr/bin/env python3` first line that tells Linux which language it is.
- `runtime.packages` lists **apt** packages — apt is Ubuntu's software installer. Deploy
  installs them as the admin user, non-interactively, before the first run:

  ```bash
  ssh ubuntu@"$BOXNAME" "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv jq"
  ```

- Ubuntu 24.04 already ships `python3`, `bash`, `curl` and `git`. Node.js, `jq`,
  `ffmpeg` and friends do not — list them.
- **Python extras go in a virtual environment**, not system-wide. Ubuntu 24.04 refuses a
  plain `pip install` with an "externally managed environment" message; that is Ubuntu
  protecting itself, not a broken box. Put `python3-venv` in `packages`, create
  `.venv/` inside the automation folder once, and have `run.sh` call `.venv/bin/python`.
- Credentials the script needs arrive as environment variables from
  `.credentials/env` — the service unit reads that file before every run.

## `claude-code` — Claude itself, running headless

**Claude Code** is Anthropic's command-line Claude — the same tool the deployer runs on
their own laptop, installed on the box so it can run prompts and skills on a schedule
with nobody watching.

**Install** (done once per box, as the `automations` user — it lands in that user's own
`~/.local/bin`, so no admin rights are needed):

```bash
ssh "$BOXNAME" 'curl -fsSL https://claude.ai/install.sh | bash'
ssh "$BOXNAME" 'export PATH="$HOME/.local/bin:$PATH"; claude --version'
```

Expect a version number back — that positive answer is the check that it worked.

**Running a prompt.** `claude -p` is print mode: one prompt in, the answer out, then it
exits. No chat window, no waiting for a person.

```bash
claude -p "Read yesterday's ServiceM8 jobs and email me a summary" \
  --allowedTools "Bash" "Read" "Write"
```

Because nobody is there to click Approve, the tools Claude may use have to be named up
front with `--allowedTools`. Skills work too: the service unit's `WorkingDirectory` is
the automation folder, so a skill copied to `<automation>/.claude/skills/<name>/` is
picked up automatically and can be invoked from the prompt by name.

**Authentication — a setup token, minted from the owner's own subscription.** A
**setup token** is a long-lived sign-in that Claude Code can use without a browser. It is
minted on the **deployer's machine**, not on the box:

```bash
claude setup-token
```

That opens a browser once, the person signs in to the Claude subscription the automation
should run on, and a token comes back. Deploy writes it straight into the automation's
credentials file on the box and never displays, logs or repeats it:

```
/home/automations/<name>/.credentials/env      # mode 600, folder mode 700
CLAUDE_CODE_OAUTH_TOKEN=<token>
```

The service unit loads that file before each run, so the automation is signed in as the
owner every time. Set `claude.setup_token: true` in the manifest to have deploy do all
of this.

**The spend rule, plainly.** Each automation spends **its own owner's seat** — the
person named in the manifest's `owner` field, on whatever subscription they signed into
when the token was minted. Never one org-wide token shared by everything on the box.
Never an Anthropic API key, anywhere. A box can hold as many people's subscriptions as
it needs to, one credentials file per automation. When one seat runs into its usage
limits, the fix is to **add a seat and spread the automations across them** — three on
one seat, two on the other — not to route everything through one account.

Tokens can expire or be revoked. When that happens the run fails with an
authentication error in the logs; re-run `claude setup-token` on the deployer's machine
and re-sync. That is a two-minute fix, not a rebuild.

## `playwright` — headless browser automations

**Playwright** is Microsoft's browser-automation tool: it drives a real Chrome-family
browser (**Chromium**) with no window on screen — that is what **headless** means. It is
the runtime for anything that has to click through a website that offers no API.

Playwright publishes an ARM64 Linux build of Chromium, so it runs natively on the
t4g box with no emulation.

**Install** — two halves, because one needs admin rights and one does not:

```bash
# admin half: Node.js, plus the system libraries Chromium needs to start at all
ssh ubuntu@"$BOXNAME" "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs npm"
ssh ubuntu@"$BOXNAME" "sudo npx --yes playwright install-deps chromium"

# automations half: Playwright and the browser itself, inside the automation folder
ssh "$BOXNAME" "cd <name> && npm install --no-fund --no-audit playwright && npx playwright install chromium"
```

**The persistent profile.** A **browser profile** is the folder where a browser keeps its
cookies and logged-in sessions. Keeping it inside the automation folder means a site
signed into once stays signed in run after run:

```js
const ctx = await chromium.launchPersistentContext('.browser-profile', {
  headless: true,
  args: ['--disable-dev-shm-usage'],   // small boxes have a small /dev/shm; this avoids crashes
});
```

That profile is credential-shaped — it holds live sessions. It lives on the box only:
never in a repo, never in a shared folder. Add `.browser-profile/` to the automation's
`.gitignore`.

**Two honest caveats.**

1. **Browser workloads want t4g.medium.** 2 GB of memory is tight for Chromium — a
   t4g.small will run a simple page fetch but will start failing on heavier pages. Size
   up at provision time, or later with the `scale` verb.
2. **Bot-defended sites sometimes refuse a headless first-time login.** Cloudflare-style
   checks and login flows that expect a real person can block a fresh headless browser.
   The pattern that works: a **dedicated service user on the target site** — its own
   account, not a person's — signed in once from a normal browser, with that profile
   persisted and synced to the box. After the first sign-in the automation is resuming a
   session, not creating one, which is a much easier thing to be allowed to do.

## `agents-sdk` — reserved

The **Claude Agents SDK** — the framework for building custom Claude agents as an
application — is not built in v1. When it lands, the manifest simply names it as another
`runtime.kind`, and the existing deploy convention (folder, credentials file, systemd
unit) already fits it unchanged. Nothing about a box provisioned today needs to change to
support it later.

---

## Claude cloud routines are still an option

The box is not a replacement for **Claude routines** — scheduled jobs that run in
Anthropic's cloud. Routines remain the better answer for a periodic wake-up job that
needs nothing on any particular machine: check a web page, read an inbox, post a summary.
Nothing to provision, nothing to patch, no monthly instance cost.

Reach for the box when the work needs what a routine cannot give it: a **command-line
tool** installed and signed in, a **long-lived process** that stays up between runs, a
**browser profile** that has to persist, or a pile of automations kept in one place. The
two sit alongside each other: routines for the simple wake-run-stop jobs, this box for
everything that needs a real machine underneath it.
