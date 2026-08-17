# AWS from zero — reference

Loaded when a server-lifecycle verb (**provision**, **scale**, **remove**) needs the AWS
CLI and `aws sts get-caller-identity` fails. It takes someone with **no AWS account at
all** to a connected, correctly scoped command line, without leaving this skill. Deploy,
status and logs never need any of this — they run over SSH.

**AWS** is Amazon's rent-a-computer service; the **AWS CLI** is the command-line tool this
skill drives it with. Three things have to exist before provision can run:

1. an **AWS account** — the billing relationship, created by the person themselves, in
   their name;
2. a dedicated **IAM user** called `claude-assistant` — **IAM** is AWS's system of logins
   and permissions, so this is a login of its own for this skill, scoped to
   **PowerUserAccess**, never the account's root login;
3. the CLI **installed and configured** on this machine, with a **region** — the city
   whose data centre the server lives in — that the person chose.

Stop when those three are true. This reference covers only enough AWS to spin up and look
after one server — not IAM as a subject, not organisations, not billing alarms.

---

## Rules that outrank everything below

- **Every key this skill uses belongs to `claude-assistant`.** The check is positive: the
  `Arn` that comes back from `get-caller-identity` ends in `:user/claude-assistant`. The
  root login owns the whole account and cannot be scoped down, so a key for it is a key to
  everything, including closing the account and reading the card on file — Stage 8 finds
  and removes any that exist.
- **They type their own sign-in; you drive the pages.** Passwords, card numbers and
  verification codes are theirs to enter — never typed, requested or repeated by you.
- **The region is one they said yes to.** Stage 6 asks; an already-configured region still
  gets read back and confirmed, because a region that was configured is not the same as a
  region that was chosen.
- **The secret access key reaches disk without passing through this conversation.**
  Stage 5's CSV download is the way that holds — file to file, matching the skill's
  credentials-never-in-context rule. The read-off-the-page fallback there breaks it, so it
  is a fallback: if you use it, write the value immediately, never repeat it back, never
  put it in a summary, and show only the last four characters of the key **id**.

---

## Stage 0 — find out what's actually missing

Run all three; each one narrows the work (silent — narrate the conclusion, not the
commands):

```bash
command -v aws            # is the CLI installed at all?
aws configure list        # is a profile configured, and with which region?
aws sts get-caller-identity --output json
```

`get-caller-identity` returning JSON with an `Account` and an `Arn` means most of this is
already done, but two things still have to be checked before you go back to the verb that
sent you here:

- **Whose key is it?** The `Arn` — AWS's identifier for a thing, the long
  `arn:aws:iam::…` string in that JSON — should end in `:user/claude-assistant`. One
  ending in `:root` is the root login, which must be replaced, not used: sign in to the
  console (**Stage 3**), make the proper user (**Stage 4**), give it a key (**Stage 5**),
  write and verify it (**Stage 7**), and only then clean up the root key (**Stage 8**).
  That order matters — Stage 8 deletes the only credential on the machine, so the
  replacement has to be working first.
- **Whose region is it?** A configured region is not the same as a chosen one; some other
  tool may have written it, and `us-east-1` is what most of them write. Read it back and
  get an explicit yes before any server is launched into it — that is Stage 6, and it
  applies just as much on this path:

  ```bash
  aws configure get region
  ```

  > AWS is already connected here, set to `<region>` — the server would live there.
  > Is that where you want it?

  A no sends you to Stage 6 to pick and write a region. Only when both checks pass is this
  reference finished.

Otherwise start at the earliest stage that is missing something: no `aws` binary →
Stage 1; no account → Stage 2; account but no `claude-assistant` user → Stage 3.

## Stage 1 — install the CLI

Tell the person this takes a minute or two, then install for the platform this machine is:

```bash
# macOS
brew install awscli

# Ubuntu / Debian (arch-aware — an ARM machine needs the aarch64 build, and a
# minimal image often has no unzip)
sudo apt-get install -y unzip
ARCH=$(uname -m)   # x86_64 or aarch64
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$ARCH.zip" -o /tmp/awscliv2.zip
unzip -q -o /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install --update

# Windows (PowerShell)
winget install --id Amazon.AWSCLI -e
```

The positive check is a version number, not the absence of complaint:

```bash
aws --version    # expect: aws-cli/2.x.x ...
```

If the shell still can't find `aws` afterwards, the install worked but this shell's `PATH`
predates it — start a fresh shell and check again before treating it as a failure.

## Stage 2 — the account, opened by the person themselves

Account signup asks for a card, a phone number and a real identity. It is theirs to do,
and Playwright must not drive it. Open the page in **their own default browser** so they
finish it in a normal window:

```bash
open "https://portal.aws.amazon.com/billing/signup"                    # macOS
xdg-open "https://portal.aws.amazon.com/billing/signup"                # Linux
Start-Process "https://portal.aws.amazon.com/billing/signup"           # Windows (PowerShell)
```

Say what's coming before they hit it — an email address and a password, a card, an SMS or
voice code, and a support-plan choice — then stay with them and answer as they go. The
questions that come up, and the answers:

| They ask | Answer |
|---|---|
| Personal or business account? | Either works. Business if the card and the ABN/company are the business's — it only changes the tax details on the invoice. |
| Why a card, if nothing is running yet? | Nothing bills until a server is launched, and that launch is a confirmed step with the price stated. The card is how AWS verifies the account. |
| Which support plan? | **Basic** — included at no cost, and enough. Developer and Business plans are paid and buy nothing this skill needs. |
| Does this cost anything? | Don't promise a no-cost tier. Quote the real figure from the skill's cost section — roughly US$12–18 a month for the default box, plus about US$2 for its disk, from launch until it's removed. |
| The card was declined / the code never arrived | Both are ordinary. A card with international payments blocked is the usual first cause; the code can take a few minutes and can be re-requested by voice instead of SMS. |

Signup finishes on a "Congratulations" page or in an email a few minutes later. Wait for
them to say they're in — account activation is occasionally not instant, and IAM pages
won't work until it is.

While they're at it, offer **MFA** on the root login — multi-factor authentication, the
phone-app code on top of the password. It takes about thirty seconds during signup and is
the single biggest thing protecting an account whose root login can close it. Offer once;
don't insist, and don't let it block the rest.

## Stage 3 — sign in to the console, then take over the browser

From here you drive, with **Playwright**. Open the IAM users page; not being signed in
yet, it will bounce to the sign-in form:

```
browser_navigate → https://console.aws.amazon.com/iam/home#/users
browser_snapshot
```

The sign-in form asks for root or IAM user. Someone who has just created the account
only has the root login, so **root is correct here** — signing in as root is fine and
normal; only root *access keys* are forbidden. If they already have their own IAM login,
pick IAM user and ask for the 12-digit account id or alias (it's shown top-right in any
console window they already have open).

Then hand the keyboard back:

> Type your email and password on the AWS page — I'll wait. Tell me when you can see the
> AWS console.

Do not type any of it. When they say they're in, `browser_snapshot` and confirm you can
see the console shell and the account menu top-right before going on.

## Stage 4 — the `claude-assistant` user, PowerUserAccess

A user of its own means this skill's access can be reviewed and revoked on its own,
without touching the person's own login. Drive **Users → Create user**:

1. User name: `claude-assistant`.
2. Leave console access **off** — this login is for the CLI, so it needs no password.
3. Permissions: **Attach policies directly**, search `PowerUserAccess`, tick it.
4. Create user, and confirm from the resulting user page that the policy is attached.

**PowerUserAccess, not AdministratorAccess.** PowerUserAccess covers every service this
skill touches — EC2 instances, key pairs, security groups, and the **SSM parameter** (an
AWS-published lookup value) that resolves the current Ubuntu image — while withholding
IAM, Organizations and account-level actions. In practice that means a leaked
`claude-assistant` key cannot create logins, widen its own permissions, or close the
account. Be accurate about the limit: it is a permissions boundary, **not** a billing one
— the policy does not fence off billing APIs, and the real protection against surprise
spend is that every launch in this skill is a confirmed step with the price stated.

Administrator adds nothing provision needs and hands over the whole account. If they ask
for Administrator "to be safe", it is the opposite of safe: the narrower policy is what
makes an assistant's key survivable if it ever leaks.

If a `claude-assistant` user already exists, reuse it — check its attached policy is
PowerUserAccess and move on.

## Stage 5 — one access key for that user

On the user's **Security credentials** tab → **Create access key**:

1. Purpose: **Command Line Interface (CLI)**.
2. Tick the acknowledgement, then Next, skip the description tag, Create.
3. The retrieve page shows the secret **once**, and offers **Download .csv file**. Click
   that. It writes both values straight to a file, which is the whole point — the secret
   never enters this conversation, exactly as the skill's credentials rule requires.

Find what landed and read the values out of it in the same shell call that writes them
(see Stage 7); the file goes to the browser's download folder, so locate it rather than
assuming a path:

```bash
CSV=$(ls -t "$HOME/Downloads"/*accessKeys*.csv 2>/dev/null | head -1)
AKID=$(awk -F, 'NR==2{print $1}' "$CSV" | tr -d '\r"')
SECRET=$(awk -F, 'NR==2{print $2}' "$CSV" | tr -d '\r"')
[ "${#AKID}" -eq 20 ] && [ "${#SECRET}" -eq 40 ] || {
  echo "CSV did not parse as expected — write nothing"; exit 1; }
```

The `tr` is not optional: AWS writes that CSV with Windows line endings, so `awk` hands
back a secret with a trailing carriage return. It is invisible in every way except that
the key then fails to authenticate, as `SignatureDoesNotMatch`, for no visible reason. And
the length check is a gate, not a report — on a surprise from the file, stop rather than
write a broken credential.

The CSV is a live credential sitting in a downloads folder, so shred it once Stage 7 has
verified. That is a later shell call and `$CSV` will not have survived it, so find the file
again rather than reusing the variable:

```bash
CSV=$(ls -t "$HOME/Downloads"/*accessKeys*.csv 2>/dev/null | head -1)
[ -n "$CSV" ] && { rm -P "$CSV" 2>/dev/null || shred -u "$CSV"; }   # -P macOS, shred Linux
```

**Fallback, if the download is unavailable** (a locked-down browser, a Playwright profile
with downloads disabled): read the values off the page instead, clicking **Show** first if
the secret is masked.

```
() => {
  const t = [...document.querySelectorAll('*')].map(e => (e.innerText || '').trim());
  return {
    akid: t.find(s => /^AKIA[A-Z0-9]{16}$/.test(s)),
    secret: t.find(s => /^[A-Za-z0-9+/=]{35,45}$/.test(s) && !s.startsWith('AKIA')),
  };
}
```

This route puts the secret through the conversation, which is why it is the fallback and
not the default. Validate both before using them — the id is `AKIA` plus 16 characters,
the secret is 40 characters of letters, digits, `+`, `/` and `=`. A null secret means the
page is still masking it; click Show and read again rather than guessing.

**One key per user.** If the user already has an active key and nobody has its secret, the
fix is to delete that one and make a fresh one — never a second live key.

## Stage 6 — region, asked

Ask before writing anything:

> Which of these is closest to you? The server lives there for good — moving it later
> means rebuilding it.

| Where they are | Region |
|---|---|
| Australia / NZ | `ap-southeast-2` (Sydney) |
| Singapore / SE Asia | `ap-southeast-1` |
| UK | `eu-west-2` (London) |
| Europe | `eu-central-1` (Frankfurt) |
| US east | `us-east-1` (N. Virginia) |
| US west | `us-west-2` (Oregon) |

Nearest wins on latency, and it's usually the right answer for where the data should sit.
Price varies a few percent between regions — not enough to override either. If they have
no preference, offer the nearest to them and get a yes; don't pick silently.

## Stage 7 — write the credentials, then prove they work

Write the files directly, never echoing either value into chat. First check whether
anything is already there:

```bash
grep -l '^\[default\]' "$HOME/.aws/credentials" 2>/dev/null
```

A hit means something else on this machine is already using AWS, and overwriting it is a
real outage for whatever that is. **Stop and ask** — don't back up and proceed on the
assumption a `.bak` makes it reversible:

> There's already an AWS key configured on this machine. I can replace it with the new
> one, or leave it alone and add this as a second, separately named setup. Which?

Replacing is usually right when the existing key is theirs and stale; if they're unsure,
leave it and use a named profile instead (`[claude-assistant]` in both files, and every
`aws` command in this skill then needs `--profile claude-assistant`). Only with a clear
answer, write:

```bash
mkdir -p "$HOME/.aws"
umask 077
[ -f "$HOME/.aws/credentials" ] && cp "$HOME/.aws/credentials" "$HOME/.aws/credentials.bak"
cat > "$HOME/.aws/credentials" <<EOF
[default]
aws_access_key_id = $AKID
aws_secret_access_key = $SECRET
EOF
cat > "$HOME/.aws/config" <<EOF
[default]
region = $REGION
output = json
EOF
chmod 600 "$HOME/.aws/credentials" "$HOME/.aws/config"
```

The `.bak` is only there to undo a mistake in the next few minutes — it is a live
credential too, not an archive. Delete it once Stage 7's verification passes, the same way
the CSV goes.

`$AKID`, `$SECRET` and `$REGION` have to be set in the **same shell call** as the heredoc
— shell variables don't survive between calls. On the CSV path that means the two `awk`
lines from Stage 5 go in this same call, so the secret travels file to file and is never
seen. Then verify:

```bash
aws sts get-caller-identity --output json
aws ec2 describe-regions --region "$REGION" --query 'Regions[0].RegionName' --output text
```

The first must return an `Arn` ending in `:user/claude-assistant` — an `Arn` ending in
`:root` means the wrong key got written, and the whole point was missed. The second proves
the key can actually reach EC2 in the chosen region, which `get-caller-identity` alone does
not (it succeeds for a key with no permissions at all).

## Stage 8 — root access keys: find them, delete them

Do this before declaring the setup finished, and while the root session from Stage 3 is
still open — only the root login can remove its own keys. The root **My security
credentials** page lists them:

```
browser_navigate → https://console.aws.amazon.com/iam/home#/security_credentials
browser_snapshot
```

Empty Access keys section → good, say nothing and go to Stage 9. A key listed is worth
interrupting for: tell them in one line what it is ("that key can do anything to
this account, including close it and read the card on file"), then remove it —
**Actions → Deactivate** first, then **Actions → Delete**, which asks for the key id typed
out to confirm.

Deactivate before deleting, and leave a minute between them. If some forgotten tool of
theirs was quietly using that key, deactivation surfaces it as that tool breaking, which is
undoable; a deletion isn't.

Deleting is the default, not a suggestion — this is the one step here worth being firm
about, and a `claude-assistant` key now exists so nothing is lost by removing it. The only
reason to stop is their naming a specific thing that still uses it: then deactivation
alone is the compromise, and it goes in the Stage 9 summary as an open risk in their words,
not quietly dropped. Either way, never use a root key for this skill.

## Stage 9 — confirm what exists

Click **Done** on the console page and tell them what now exists:

```
AWS is connected.
Account:   <12-digit id>
User:      claude-assistant (PowerUserAccess — can run servers, can't change permissions or billing)
Region:    <region>
Access key: AKIA…<last 4>, saved to ~/.aws/credentials on this machine only
```

Nothing is billing yet — a server has to be launched for that, and that's the next
confirmed step.

---

## Gotchas

| Problem | Fix |
|---|---|
| IAM pages 403 or look empty right after signup | Activation hasn't finished. It's usually minutes, occasionally hours, and there is nothing to fix — wait and retry. |
| `get-caller-identity` works, but `run-instances` says not authorized | The key is real but under-scoped. Check the user's attached policy is PowerUserAccess, not a narrower one someone picked. |
| `Arn` ends in `:root` | Root keys are in use. Stage 4 for the proper user, then Stage 8 to remove the root key. |
| The secret was closed without being saved, or the CSV never downloaded | It cannot be retrieved — the page shows it once. Delete that key and create a new one; there is no recovery path and no reason to hunt for one. |
| Shell can't find `aws` after a clean install | `PATH` in this shell predates the install. New shell, check again. |
| A second person needs to run these verbs | Their machine, their own `claude-assistant` key. Never copy `~/.aws/credentials` between machines. |
| Console lands in the wrong region | The console's region picker is cosmetic here — what matters is the region in `~/.aws/config`, and every command in this skill passes `--region` explicitly. |
