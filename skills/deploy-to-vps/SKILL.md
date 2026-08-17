---
name: deploy-to-vps
description: "One place to deploy any automation onto an always-on Linux server (a VPS) on AWS EC2 — so scheduled jobs stop depending on someone's home computer being awake. Six verbs: provision a new hardened server, connect to an existing one someone else owns (with access diagnosis and exact grant instructions), deploy an automation (folder + manifest → server, runtime installed, schedule live), status/logs, scale the server up, and remove an automation or the whole server. Runs plain scripts, headless Claude Code, and headless Playwright browser automations on systemd timers. Use when someone says 'deploy my automation', 'put this on the server', 'set up an always-on server', 'is the server running', 'show me the logs', 'give someone else access to the box', 'the server needs more power', or 'take it down'. Server lifecycle verbs need an AWS CLI connection, and this skill sets that up itself from a standing start — account signup through to a scoped IAM user and a configured CLI; deploying to an existing server needs only SSH."
allowed-tools: Bash, Read, Write, Edit, mcp__playwright__*, mcp__plugin_playwright_playwright__*
metadata:
  category: Productivity & Integrations
  tags:
    - vps
    - server
    - ec2
    - aws
    - deploy
    - automation
    - systemd
    - scheduling
  pairs-with:
    - skill: gws
      reason: "gws-based automations deployed to a server need their gws sign-in exported to the box's file backend (see Gotchas)"
---

# deploy-to-vps — an always-on home for your automations

## Overview

A **VPS** — a rented computer in a data centre that is always on — gives you one place
to run every automation, instead of jobs firing only while someone's home desktop is
awake. This skill provisions that server on **AWS EC2** (Amazon's rent-a-server
service), hardens it by default, and deploys automations onto it as
**folder + manifest** packages on a schedule.

- An **automation** is a folder plus a small manifest file (`automation.yaml`) stating
  what it is, who owns it, where its source lives, what runtime it needs, its schedule,
  and which credentials it declares. Full format: `references/manifest.md`.
- Scheduling uses **systemd timers** — the server's built-in alarm clock, which logs
  every run and catches up on runs missed while the server was off. Never cron.
- It runs anything: plain scripts in any language, **headless Claude Code** on a
  schedule, and **headless Playwright** browser automations. Catalogue and honest
  caveats: `references/runtimes.md`.
- **Claude cloud routines remain a second option** for simple wake-run-stop jobs that
  need nothing local. This server is for CLIs, long-lived processes, and browser work.

**What this costs.** The default server size is t4g.small (2 CPU cores, 2 GB memory):
roughly **US$12–18 a month** depending on region, plus about US$2/month for its 20 GB
disk. t4g.medium (4 GB memory, ~US$24/month) suits heavier work — especially browser
automations, for which 2 GB is tight. Always state the monthly cost and get a clear
yes before launching anything that bills.

**What "hardened" means here.** The server accepts connections only over **SSH** (the
secure remote-login channel, port 22), key-only — password logins are switched off. A
firewall (ufw) blocks every other inbound door, and security patches install
themselves (unattended-upgrades). `scripts/harden.sh` does all of it, and is safe to
run again — every step checks first and only acts if something is missing.

**Identity — the core rules.**

- One Unix user on the server, **`automations`**, owns every automation. Per-person SSH
  keys in its `authorized_keys` control who can deploy. **No shared login credentials**
  — granting access is adding one key line; revoking is removing it.
- **Never a single org-wide Claude token.** Each automation that runs Claude gets its
  own setup token, minted from whatever subscription its *owner* is signed into at
  deploy time — owners spend their own seat's usage. No Anthropic API key anywhere.
- **Credentials are declare-and-sync.** The manifest declares what the automation
  needs; deploy copies it from the deployer's machine over SSH into the automation's
  private `.credentials/` folder on the server (folder mode 700, files 600). Nothing
  credential-shaped ever enters a repo or a shared folder.
- **Credentials move programmatically, never through the model's context.** Every
  secret goes file-to-file — written straight to a file or piped down the SSH pipe,
  under `umask 077`. Never print one, never read one back, never let one land in the
  conversation. This rule outranks convenience in every verb.

**Who needs what.** Deploying onto an existing server, checking status, and reading
logs need only SSH. Creating, resizing, or destroying a server needs the AWS CLI
connected — if it isn't, `references/aws-setup.md` gets there from wherever the person
actually is, including no AWS account at all: signup in their own browser, a dedicated
`claude-assistant` IAM user scoped to PowerUserAccess, and the CLI configured with a
region they chose. No other skill is needed.

**Operating from Windows.** Windows 10+ ships OpenSSH, so `ssh`, `scp` and
`~/.ssh/config` all work as written in PowerShell. Where a snippet uses `rsync`
(which Windows lacks), copy with `scp -r` instead, or run the snippet in WSL. The gws
credential recipe in Gotchas is OS-portable — it works the same from Mac or Windows.

## Which verb to run

| The person wants | Verb |
|---|---|
| A new always-on server | **provision** |
| To use a server someone else owns (or access is failing) | **connect** |
| An automation put on the server, or updated | **deploy** |
| To know what's running / what happened | **status / logs** |
| The server needs more power | **scale** |
| An automation retired, or the whole server gone | **remove** |

Before any verb: `ls "$HOME/.config/deploy-to-vps/"` — each `<boxname>.env` file there
is a server this machine already knows. If the verb targets a known box, load its
record first — **in the same shell call as the commands that use it** (shell variables
don't survive between separate calls):

```bash
set -a; . "$HOME/.config/deploy-to-vps/<boxname>.env"; set +a   # INSTANCE_ID, REGION, BOX_USER
```

## Communication rules (all verbs)

- You drive. The person's only jobs: sign in to their own accounts, click
  Allow/Approve, and say yes to anything that costs money or destroys something.
- Name every technical thing once in one short line, then use its name. Standard
  one-liners to reuse: **VPS** — "a rented computer in a data centre that's always on";
  **SSH** — "the secure way this machine talks to the server"; **systemd timer** —
  "the server's alarm clock — runs the job on schedule and logs every run";
  **manifest** — "one small file saying what the automation is and needs";
  **firewall** — "blocks every door into the server except the one we use".
- Say what's about to happen before it happens, with a time estimate ("launching the
  server — about two minutes"). Slow steps can look frozen without being frozen.
- Never show raw error text — translate it. Never echo a credential, token, key, or
  its contents into chat, narration, or a log. On failure: "No problem — let me try a
  different way", then diagnose silently.
- Confirm before: launching a server (state size + monthly cost), resizing (new cost),
  terminating anything, and any run that sends email or writes to a business system.

---

## PROVISION — a new hardened server

**Goal:** a running, hardened Ubuntu box the owner can deploy to, and so can anyone they
later grant a key.

1. **Offer the size menu** (honest costs, monthly, roughly — varies a little by region):
   - **t4g.small** — 2 cores, 2 GB. ~US$12–18/mo. Right for scripts and Claude jobs. *(default)*
   - **t4g.medium** — 2 cores, 4 GB. ~US$24/mo. Right when browser automations are planned.

   Ask for a short server name (lowercase-with-hyphens, e.g. `my-automations`). The
   region comes from the CLI (`aws configure get region`) — never a default of your own.
   If it was chosen during AWS setup, don't re-ask; if the CLI was already configured
   when you arrived, nobody has agreed to it yet, so say it once and get a yes before
   launching ("the server would live in `<region>` — is that where you want it?"). Hold
   the size as `SIZE` (`t4g.small` or `t4g.medium`) for step 5.

2. **Check the connection** (silent):

   ```bash
   aws sts get-caller-identity --output json   # must succeed; if not → references/aws-setup.md
   REGION="$(aws configure get region)"
   BOX=<boxname>
   ```

3. **Make the deployer's SSH key** (each step checks first, so re-running is safe):

   ```bash
   [ -f "$HOME/.ssh/vps-$BOX" ] || ssh-keygen -t ed25519 -f "$HOME/.ssh/vps-$BOX" -N "" -C "$(whoami)@$BOX"
   aws ec2 describe-key-pairs --region "$REGION" --key-names "vps-$BOX-$(whoami)" >/dev/null 2>&1 || \
     aws ec2 import-key-pair --region "$REGION" --key-name "vps-$BOX-$(whoami)" \
       --public-key-material "fileb://$HOME/.ssh/vps-$BOX.pub"
   ```

4. **Security group** — the firewall AWS itself puts in front of the server; SSH only
   (reuse it if a previous run already made it):

   ```bash
   VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true \
     --query 'Vpcs[0].VpcId' --output text)
   SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
     --filters "Name=group-name,Values=$BOX-sg" --query 'SecurityGroups[0].GroupId' --output text)
   if [ "$SG_ID" = "None" ]; then
     SG_ID=$(aws ec2 create-security-group --region "$REGION" --group-name "$BOX-sg" \
       --description "deploy-to-vps: SSH only" --vpc-id "$VPC_ID" --query GroupId --output text)
     aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG_ID" \
       --protocol tcp --port 22 --cidr 0.0.0.0/0
   fi
   ```

5. **Launch** (confirm size + cost first). Ubuntu 24.04 LTS for ARM, resolved
   per-region so this works anywhere:

   ```bash
   AMI=$(aws ssm get-parameter --region "$REGION" \
     --name /aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id \
     --query Parameter.Value --output text)
   IID=$(aws ec2 run-instances --region "$REGION" --image-id "$AMI" --instance-type "$SIZE" \
     --key-name "vps-$BOX-$(whoami)" --security-group-ids "$SG_ID" \
     --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
     --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$BOX},{Key=managed-by,Value=deploy-to-vps}]" \
     --query 'Instances[0].InstanceId' --output text)
   aws ec2 wait instance-running --region "$REGION" --instance-ids "$IID"
   IP=$(aws ec2 describe-instances --region "$REGION" --instance-ids "$IID" \
     --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
   ```

6. **Wait for SSH** (cloud boxes take ~30–60s after "running" to accept logins), and
   check it positively — never fall through to hardening on a box that never answered:

   ```bash
   SSH_OK=no
   for i in $(seq 1 30); do
     ssh -i "$HOME/.ssh/vps-$BOX" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
       ubuntu@"$IP" true && { SSH_OK=yes; break; }; sleep 5
   done
   [ "$SSH_OK" = yes ] && echo "OK: server answering" || echo "FAILED: server never answered"
   ```

7. **Harden** — copy `scripts/harden.sh` from **this skill's own folder** (resolve it
   from the skill's base directory, never the current working directory) and run it
   with the deployer's public key. It sets up the firewall, self-installing security
   patches, key-only SSH, the `automations` user, and lets its timers run with nobody
   logged in:

   ```bash
   scp -i "$HOME/.ssh/vps-$BOX" "<this skill's folder>/scripts/harden.sh" ubuntu@"$IP":/tmp/harden.sh
   ssh -i "$HOME/.ssh/vps-$BOX" ubuntu@"$IP" \
     "sudo bash /tmp/harden.sh \"$(cat "$HOME/.ssh/vps-$BOX.pub")\" && rm /tmp/harden.sh"
   ```

   Every step prints `OK: …` — check each line is present, not merely that nothing
   complained.

8. **Record the box** locally and give it a memorable SSH name:

   ```bash
   mkdir -p "$HOME/.config/deploy-to-vps"
   printf 'INSTANCE_ID=%s\nREGION=%s\nBOX_USER=automations\n' "$IID" "$REGION" \
     > "$HOME/.config/deploy-to-vps/$BOX.env"
   ```

   Append to `~/.ssh/config` (create if absent; if a `Host $BOX` block already exists,
   update its HostName instead):

   ```
   Host <boxname>
     HostName <IP>
     User automations
     IdentityFile ~/.ssh/vps-<boxname>
   ```

9. **Smoke test** — the positive check is the automations user answering:

   ```bash
   ssh "$BOX" 'whoami && hostname'   # expect: automations
   ```

   Tell the person: the server is up, hardened, and costs ~US$X/month from now until
   it's removed.

**The server's address can change.** AWS hands out a new public IP whenever the server
is stopped and started (scale does this). The instance id in the box record is the
source of truth — whenever SSH fails or after any stop/start, refresh:

```bash
IP=$(aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
# then update the HostName line in the Host block in ~/.ssh/config
```

---

## CONNECT — use a server someone else owns

**Goal:** this machine can deploy to an existing box — or, when it can't, the person
gets an exact, forwardable fix rather than a shrug.

1. **Identify the box.** Need: box name, and either its address or (better) its
   instance id + region — from the owner, or by tag if this AWS account can see it:

   ```bash
   aws ec2 describe-instances --region "$REGION" --filters "Name=tag:Name,Values=$BOX" \
     "Name=instance-state-name,Values=running" \
     --query 'Reservations[0].Instances[0].{id:InstanceId,ip:PublicIpAddress}' --output json
   ```

2. **Make this person's key** if they don't have one for this box
   (`~/.ssh/vps-$BOX`, step 3 of provision), then **try the door**:

   ```bash
   ssh -i "$HOME/.ssh/vps-$BOX" -o BatchMode=yes -o ConnectTimeout=10 \
     -o StrictHostKeyChecking=accept-new automations@"$IP" 'whoami'
   ```

   Success (`automations` printed) → write the box record + SSH config block
   (provision step 8) and finish.

3. **Diagnose in order** when it fails — each check separates one cause:
   - Instance not found / not `running` → the box is off or gone; that's the owner's
     call, not an access problem.
   - `ConnectTimeout` → the door is blocked: wrong address (refresh the IP from the
     instance id) or the security group lost its port-22 rule.
   - `Permission denied (publickey)` → the server is fine; this person's key simply
     isn't on it yet. Go to step 4.

4. **Generate grant instructions — both directions.** Compose a short message the
   person can forward, containing their public key (the `.pub` file — safe to share;
   the private half never leaves this machine):

   > To give <name> deploy access to <boxname>, run this on any machine that can
   > already reach it:
   >
   > ```bash
   > ssh <boxname> 'printf "%s\n" "<contents of their vps-<boxname>.pub>" >> ~/.ssh/authorized_keys'
   > ```

   The same works in reverse: when *this* person owns the box and someone else is
   locked out, take that person's public key and run that line here, now. Revoking is
   deleting that key's line from the same file.

---

## DEPLOY — automation folder + manifest → server, schedule live

**Goal:** the automation is on the box, its runtime installed, its credentials in
place, its timer live, and one real run observed.

1. **Find the automation, then read its manifest.** The person usually just names it —
   "deploy my inbox clearer". Locate that folder on this machine the way you would
   locate anything else: ask them where it lives, or search for it. If it doesn't exist
   yet, build it first, exactly as you normally would, then deploy what you built. The
   positive check before going on: you can list the folder and see the code in it.

   Then read the manifest (`automation.yaml` at the top of that folder). You read it
   yourself — there is no parser program. No manifest yet? Write one with the person
   using `templates/automation.yaml`; format reference: `references/manifest.md`.
   `name` becomes the folder and unit names — check it's not already deployed
   (`ssh "$BOX" 'ls ~'`) unless this is an update.

2. **Resolve the source.** `local` → the folder is already here. `github` → clone it
   fresh (`gh repo clone <owner>/<repo> <tmpdir>`). If the person wants version history
   and the automation has no repo, offer to make one:
   `gh repo create <owner>/<name> --private --source <folder> --push` — after confirming
   the folder holds no credentials (it must not; the manifest only *names* credentials,
   deploy syncs them separately).

3. **Copy the folder** to the box (never `.git`, never local credential files):

   ```bash
   rsync -a --delete --exclude '.git' --exclude '.credentials' "<folder>/" "$BOX:<name>/"
   ```

4. **Install the runtime** the manifest names — recipes per kind (script /
   claude-code / playwright) live in `references/runtimes.md`. Announce installs
   before running them; they can take a few minutes on a small box.

5. **Sync declared credentials** — for each manifest `credentials` entry:

   ```bash
   ssh "$BOX" "mkdir -p '<name>/.credentials' && chmod 700 '<name>/.credentials'"
   rsync -a "<from>" "$BOX:<name>/<to>"
   ssh "$BOX" "chmod -R go-rwx '<name>/.credentials'"   # dirs 700, files 600 — run after every sync
   ```

   (The chmod runs box-side because the Mac's built-in rsync — openrsync — doesn't
   support `--chmod` filters.)

   If the runtime is claude-code (or `claude.setup_token: true`): mint the owner's
   setup token on *this* machine and ship it straight to the box — capture and send in
   **one shell call** (variables don't survive between calls), and never print it:

   ```bash
   TOKEN="$(claude setup-token)"   # opens the owner's browser once; output is the token — check it's non-empty
   [ -n "$TOKEN" ] && printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' "$TOKEN" | \
     ssh "$BOX" "umask 077; cat >> '<name>/.credentials/env'" && echo "OK: token on box"
   unset TOKEN
   ```

6. **Install the schedule.** Render `templates/automation.service` and
   `templates/automation.timer` (fill `{{name}}`, `{{description}}`, `{{command}}`,
   `{{calendar}}`), copy both to `~/.config/systemd/user/` on the box (make the folder
   first — a fresh box doesn't have it), then:

   ```bash
   ssh "$BOX" 'mkdir -p ~/.config/systemd/user'
   scp <rendered .service and .timer> "$BOX:.config/systemd/user/"
   ssh "$BOX" 'export XDG_RUNTIME_DIR=/run/user/$(id -u)
     systemctl --user daemon-reload
     systemctl --user enable --now automation-<name>.timer
     systemctl --user list-timers automation-<name>.timer --no-pager'
   ```

   The `XDG_RUNTIME_DIR` line is required every time systemd is driven over SSH —
   without it systemctl can't find the user session.

7. **Run it once, for real** (confirm first if the run has outward effects — sends
   email, writes to a business system):

   ```bash
   ssh "$BOX" 'export XDG_RUNTIME_DIR=/run/user/$(id -u)
     systemctl --user start automation-<name>.service
     journalctl --user-unit automation-<name> -n 30 --no-pager'
   ```

   Success is the automation's **real side effect observed** (the email arrived, the
   record was written) *plus* `Deactivated successfully` in the journal — never just
   an absence of error words.

8. **Tell the person** what's now true: the automation's name, its schedule in plain
   English, whose seat it spends (the owner's), and that logs are one ask away.

---

## STATUS / LOGS — what's running, when it last fired, what it said

```bash
ssh "$BOX" 'export XDG_RUNTIME_DIR=/run/user/$(id -u)
  systemctl --user list-timers --all --no-pager'                     # every automation: last run, next run
ssh "$BOX" 'export XDG_RUNTIME_DIR=/run/user/$(id -u)
  journalctl --user-unit automation-<name> --since -48h --no-pager'  # one automation's story
ssh "$BOX" 'uptime && df -h / && free -h'                            # the box itself: load, disk, memory
ssh "$BOX" 'grep -H -E "^(owner|description):" */automation.yaml'    # who owns what — every deployed manifest
```

For the box's AWS-side state (running? what size? costing money?):

```bash
aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].{state:State.Name,type:InstanceType,ip:PublicIpAddress}' --output json
```

Translate for the person: which automations exist, **who owns each** (that's whose
seat and credentials it runs on — the load-balancing decision when a seat hits its
limits), when each last fired and next fires, and anything that failed — with what its
log actually said, in plain English.

---

## SCALE — resize the server

Resizing needs the box stopped for two–three minutes; timers catch up on anything
missed (that's `Persistent=true` doing its job). **Stay in the t4g family** — the box
is ARM, and x86 sizes won't boot it. Confirm the new size and monthly cost first.

```bash
aws ec2 stop-instances --region "$REGION" --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-stopped --region "$REGION" --instance-ids "$INSTANCE_ID"
aws ec2 modify-instance-attribute --region "$REGION" --instance-id "$INSTANCE_ID" \
  --instance-type '{"Value":"<new size, e.g. t4g.medium>"}'
aws ec2 start-instances --region "$REGION" --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"
```

Then refresh the IP into `~/.ssh/config` (the address changed — see the note at the
end of PROVISION) and smoke test: `ssh "$BOX" 'whoami'` expecting `automations`.

---

## REMOVE — an automation, or the whole server

**One automation** (leaves its source repo untouched — only the deployed copy goes):

```bash
ssh "$BOX" 'export XDG_RUNTIME_DIR=/run/user/$(id -u)
  systemctl --user disable --now automation-<name>.timer
  rm -f ~/.config/systemd/user/automation-<name>.service ~/.config/systemd/user/automation-<name>.timer
  systemctl --user daemon-reload && systemctl --user reset-failed
  rm -rf ~/<name>
  systemctl --user list-timers --all --no-pager'
```

The final listing must no longer show the automation — that's the positive check.

**The whole server.** First show the person what still lives on it
(`ssh "$BOX" 'ls ~'` + the timer list) and get an explicit yes — this destroys the box
and everything on it, and is not undoable. Then:

```bash
aws ec2 terminate-instances --region "$REGION" --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-terminated --region "$REGION" --instance-ids "$INSTANCE_ID"
aws ec2 delete-security-group --region "$REGION" --group-name "$BOX-sg"
aws ec2 delete-key-pair --region "$REGION" --key-name "vps-$BOX-$(whoami)"
rm -f "$HOME/.config/deploy-to-vps/$BOX.env"
# and delete the Host <boxname> block from ~/.ssh/config
```

Confirm billing has actually stopped — the positive check:

```bash
aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].State.Name' --output text   # expect: terminated
```

Tell the person: the server is gone and nothing about it bills from here on. (The
disk dies with it — anything worth keeping should have been in a repo.)

---

## Gotchas

| Problem | Fix |
|---|---|
| SSH suddenly refuses / times out to a box that worked | The IP changed (stop/start does this). Refresh it from the instance id — end of PROVISION. |
| `systemctl --user` says "Failed to connect to bus" | The `XDG_RUNTIME_DIR` export is missing from that SSH command — every user-level systemd call over SSH needs it. |
| `gws` on the box can't read synced credentials | The deployer's gws keeps its sign-in encrypted behind an OS keystore (the macOS keyring, Windows Credential Manager) that doesn't copy as a file. Export it instead — same on Mac and Windows. Write the export to a scratch file under the home folder, so it can be declared as a normal manifest `from:` path: `mkdir -p ~/.cache/deploy-to-vps && umask 077 && gws auth export --unmasked > ~/.cache/deploy-to-vps/gws-credentials.json` (redirect straight to the file, never let it print; `--unmasked` is mandatory — without it the client secret comes back as a placeholder and fails on the box). Declare it like any other credential — `from: ~/.cache/deploy-to-vps/gws-credentials.json`, `to: .credentials/gws/credentials.json` — then put both of these in the automation's `.credentials/env`: `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=/home/automations/<name>/.credentials/gws` and `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file`. The file backend makes gws read that plaintext `credentials.json` directly — no encryption key, no keystore. **Delete the scratch file once the sync is confirmed** (`rm -f ~/.cache/deploy-to-vps/gws-credentials.json`) — it is a live refresh token in the clear. Fallback if the export refuses: `gws auth login` **on the box**, with those same two env vars set, opening the sign-in URL it prints in the deployer's own browser. |
| Browser automation is slow or the browser gets killed | 2 GB is tight for Chromium — this workload wants t4g.medium. Say so honestly and offer **scale**. |
| A site refuses the automation's headless login | Bot defence. The pattern: a dedicated service user on that site, signed in once (interactively if needed), profile persisted in the automation folder — see `references/runtimes.md`. |
| Scale to an x86 size fails to boot | The box is ARM — stay in the t4g family (or another `g`-suffixed ARM family). |
| `import-key-pair` says the key name exists | Fine on re-run if it's the same key; if a different person shares the name, suffix theirs — key names are per person by design. |
| Timer never fires | `list-timers --all` — if the timer isn't listed, step 6 of DEPLOY didn't finish; if listed with a NEXT time, it's waiting as designed; check the calendar expression against `systemd-analyze calendar '<expr>'`. |

## Where things live

- **On each deployer's machine:** box records `~/.config/deploy-to-vps/<box>.env`;
  keys `~/.ssh/vps-<box>` (+ `.pub`); a `Host <box>` block in `~/.ssh/config`.
- **On the server:** automations at `/home/automations/<name>/`; credentials inside
  each at `<name>/.credentials/` (700/600, never in any repo); schedules at
  `/home/automations/.config/systemd/user/automation-<name>.{service,timer}`; logs in
  journald.
- Resolve every path from the home folder — never hardcode a username.

## Files in this skill

- `SKILL.md` — this file: the six verbs.
- `references/aws-setup.md` — no AWS account to connected CLI: signup, the
  `claude-assistant` IAM user at PowerUserAccess, region, credentials.
- `references/manifest.md` — the automation manifest, field by field.
- `references/runtimes.md` — script / claude-code / playwright recipes and caveats
  (agents-sdk reserved for later).
- `templates/automation.yaml`, `templates/automation.service`,
  `templates/automation.timer` — the manifest example and the two unit templates
  deploy renders.
- `scripts/harden.sh` — idempotent hardening, run once per new box (and safe to run
  again).

## Related skills

- **gws** — for Google-Sheets/Gmail automations; note the credential-export gotcha
  above.
- **Claude cloud routines** — not a skill, but the other place a scheduled job can
  live. Right for simple wake-run-stop work that needs nothing on a particular
  machine; this server is for CLIs, long-lived processes and browser work.
