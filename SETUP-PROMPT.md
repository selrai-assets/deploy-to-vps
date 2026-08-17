# SETUP-PROMPT.md

**You are Claude (or any coding agent), and you are installing The Always-On Server
on this machine.** The member has just cloned this repo and pointed you here. Do every
step yourself. If a step fails, fix it and retry. Never hand a terminal command back to
the member, and never stop to ask a question you can answer by looking.

Everything below runs from the root of the clone. Nothing here needs an AWS account, a
card, or an API key. The only step that touches the network after the clone is Step 5,
which fetches the browser tool the AWS path later needs.

**Steps 3 and 4 are bash.** On Windows, run them in WSL or Git Bash rather than
PowerShell. The skill itself works from PowerShell once installed, as `SKILL.md`
explains, but symlinking and the file checks below are POSIX shell.

**Installing the kit launches no server and spends no money.** Provisioning is a
separate conversation the member starts later, and it states the monthly cost and waits
for a clear yes before anything bills. Do not provision anything during setup, and do
not offer to.

---

## What you are installing

One skill: `deploy-to-vps`, at `skills/deploy-to-vps/`. It carries six verbs that cover
the whole life of an always-on server: **provision** a new hardened one, **connect** to
one somebody else owns, **deploy** an automation onto it with its schedule live,
**status / logs**, **scale** it up, and **remove** an automation or the whole server.

It ships everything it needs, including `references/aws-setup.md`, which takes a member
with no AWS account at all through to a configured command line. There is no second
skill to install and no external AWS skill to depend on.

`examples/inbox-clearer/` is a demo automation that rides along in the repo. It is not
installed by this prompt and needs no install step. It is deployed later, by the deploy
verb, exactly as the member's own automations will be.

---

## Step 1: check the machine

Three commands, checking three things. Run all three, then narrate the conclusion rather
than the commands:

```bash
git --version
ssh -V
rsync --version | head -1   # deploy copies folders to the server with this
```

`git` and `ssh` are the two that matter. macOS and Linux ship all three. Windows 10 and
newer ship OpenSSH, so `ssh`, `scp` and `~/.ssh/config` work as written in PowerShell,
but Windows has no `rsync`: on that machine the deploy verb copies with `scp -r`
instead, or runs in WSL. Say that once, here, rather than discovering it mid-deploy. If
`ssh` is genuinely missing, install it and carry on.

Do not install `gh` (the GitHub command line) here either. Deploy reaches for it only
when an automation's source lives in a GitHub repo, and that is the moment to add it.

Do **not** check for or install the AWS CLI here. The skill installs and configures it
at the moment a server verb needs it, and installing it now would skip the account,
region and permission choices that path exists to make.

---

## Step 2: find the skills directory

Install into every harness the member actually uses. The two are independent and neither
loads the other's directory:

| Harness | Skills directory |
|---|---|
| Claude Code | `~/.claude/skills` |
| Codex | `~/.codex/skills` |

If the member uses both, run steps 2 and 3 once per directory.

---

## Step 3: link the skill in

Symlink rather than copy, so a `git pull` in the clone updates the installed skill with
no reinstall step:

```bash
CLONE="$PWD"                               # the root of this clone, absolute
SKILLS_DIR="$HOME/.claude/skills"          # or "$HOME/.codex/skills" for Codex
mkdir -p "$SKILLS_DIR"
link="$SKILLS_DIR/deploy-to-vps"
if [ -e "$link" ] && [ ! -L "$link" ]; then
  echo "$link exists and is not a symlink: move it aside yourself" >&2
  exit 1
fi
ln -sfn "$CLONE/skills/deploy-to-vps" "$link"
ls -l "$link"
```

Run that block from the root of the clone, and note the absolute path it resolved. Shell
variables do not survive from one call to the next, so `SKILLS_DIR` has to be set again
in every later block that uses it, and `$PWD` has to still be the clone root when this
block runs. Installing for a second harness means running this whole block again, from
the clone root again, with the other directory in `SKILLS_DIR`.

**The guard is not decoration.** `ln -sfn` pointed at a path where a real directory
already sits does not replace it and does not fail. It quietly creates the link *inside*
that directory, at `$SKILLS_DIR/deploy-to-vps/deploy-to-vps`, where the skill is dead and
`ls -l` still looks healthy.

Two consequences to state to the member in one line each, because both surprise people
later:

- **The clone has to stay where it is.** Moving or deleting the folder breaks the link.
  If they want it somewhere tidier, move it *first*, then re-run this step.
- **No restart.** Skills are read once per session, so their next new session has it.

---

## Step 4: prove the skill is whole

The skill drives a real server, so a half-copied clone is worth catching now rather than
halfway through a provision. Check the files positively, by name:

```bash
SKILL="$HOME/.claude/skills/deploy-to-vps"    # the link from step 3; adjust for Codex
for f in SKILL.md \
         references/aws-setup.md references/manifest.md references/runtimes.md \
         templates/automation.yaml templates/automation.service templates/automation.timer \
         scripts/harden.sh; do
  [ -s "$SKILL/$f" ] || { echo "MISSING: $f" >&2; exit 1; }
done
bash -n "$SKILL/scripts/harden.sh" && echo "OK: skill complete, hardening script parses"
```

`SKILL` is set again here on purpose: this is a new shell call, and nothing set in step 3
survived into it. Reading through the link is also the point, since it proves the link
resolves as well as proving the files exist.

A healthy run prints exactly that one `OK:` line and nothing else. A `MISSING:` line
means either an incomplete clone or a link that does not resolve, in that order of
likelihood: check the link with `ls -l "$SKILL"` first, and only re-clone if the clone
really is short of files. Do not patch a gap by hand.

---

## Step 5: add the browser tool the AWS path needs

`references/aws-setup.md` drives real console pages with Playwright: the IAM user, its
access key, and the check for root keys. Without it, that whole path stalls at Stage 3.
The member's own account signup is deliberately not driven this way, so nothing here
changes who types the card details.

Check what this harness already has. On Claude Code:

```bash
claude mcp list
```

If nothing Playwright-shaped is listed, add it at **user** scope, so it is there in the
member's own working folders rather than only in this clone:

```bash
claude mcp add --scope user playwright -- npx @playwright/mcp@latest
```

That fetch needs `node` and `npx` on PATH; check with `node -v` before blaming the
command. Unlike the skill, a newly added tool is not live in the session that added it,
so it arrives with the member's next new session, alongside the skill.

This step serves the AWS-from-zero path only. A member who already has a working `aws`
command, or who is only deploying onto a server somebody else owns, needs none of it. If
the tool cannot be added on this machine, do not treat setup as failed: install the skill
anyway and say plainly that AWS setup will need a browser tool added before it can run.

---

## Step 6: tell the member it is ready

Report short, and **in plain words**. Everything above this step is your vocabulary, not
theirs. Symlink, harness, IAM and hardening all get translated before they reach the
member, or explained in one short line where the detail genuinely matters. Hide nothing;
just do not assume they know the term. One line per bullet below is the target.

Cover exactly these, and stop:

- **Installed, and where it works.** If they only use Claude Code, that is *"installed
  for Claude Code, and your next new session will have it, no restart needed"*, with
  nothing about tools plural.
- **Step 3's two consequences**, in that plain wording: the skill is linked to this
  folder rather than copied, so a `git pull` updates it, but moving the folder breaks
  the link.
- **Nothing is running and nothing is billing yet.** A server has to be launched for
  that, and launching is a separate step that states the cost and waits for a yes.
- **What it will cost when they do launch**, as a range and rounded up: about US$15 to
  US$25 a month for the standard server, or about US$25 to US$35 a month for the larger
  one browser automations want. It bills from launch until they ask for the server to be
  removed. (Both ranges take the skill's own figures, server plus disk, from the "What
  this costs" section of `SKILL.md`, round them up and leave headroom at the top for
  region and exchange rate. If those figures move, these move with them.)
- **Their three jobs**, which is the whole of what the kit ever asks of them: sign in to
  their own accounts, click Allow when something asks permission, and say yes to
  anything that costs money, deletes something, or sends something out into the world.
- **One example of how to start**, in their words rather than a command:

  > Say *"set up my always-on server"* and I will take it from there, including the AWS
  > account if you do not have one yet.

  If they want to watch it work on something real before writing their own automation,
  the inbox clearer in `examples/inbox-clearer/` is the thing to deploy first. Say in the
  same breath that it works on a Google mailbox, so a member on Outlook knows now rather
  than at deploy time.

Do not walk them through the six verbs, do not explain AWS, and do not offer to
provision anything. Setup is finished. The first server is a conversation they start.

---

## If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| The skill does not fire in a new session | linked into a harness they do not use | re-run steps 2 and 3 against the other skills directory |
| `... exists and is not a symlink` | a real directory sits at the link path | move it aside by hand; the guard will not delete it for you |
| `MISSING: ...` in step 4 | a link that does not resolve, or an incomplete clone | `ls -l` the link first; re-clone only if the clone is genuinely short of files |
| `ls -l` shows the link, but the skill still does nothing | the link was created inside an existing directory (see step 3) | remove the stray directory, then re-run step 3 |
| `claude mcp add` is not available | an older CLI, or a harness that is not Claude Code | install the skill anyway; say the browser tool is outstanding and only the AWS setup path needs it |
| `npx: command not found` in step 5 | no Node on this machine | install Node, or leave the browser tool outstanding and say so |
| `ln: command not found`, or the link silently fails on Windows | steps 3 and 4 were run in PowerShell | re-run them in WSL or Git Bash |

Fix it and retry. Escalate to the member only when the machine itself is the problem: no
`git`, no `ssh`, or no write access to their home folder.
