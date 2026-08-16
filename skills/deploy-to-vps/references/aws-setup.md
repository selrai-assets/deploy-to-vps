# AWS from zero — reference

Loaded when a server-lifecycle verb (**provision**, **scale**, **remove**) needs the AWS
CLI and `aws sts get-caller-identity` fails. It takes someone with **no AWS account at
all** to a connected, correctly scoped command line, without leaving this skill. Deploy,
status and logs never need any of this — they run over SSH.

**AWS** is Amazon's rent-a-computer service; the **AWS CLI** is the command-line tool this
skill drives it with. Three things have to exist before provision can run:

1. an **AWS account** — the billing relationship, created by the member, in their name;
2. a dedicated **IAM user** called `claude-assistant` — a login of its own for this skill,
   scoped to **PowerUserAccess**, never the account's root login;
3. the CLI **installed and configured** on this machine, with a **region** the member
   chose.

Stop when those three are true. This reference covers only enough AWS to spin up and look
after one server — not IAM as a subject, not organisations, not billing alarms.

---

## Rules that outrank everything below

- **Never the root user's keys.** The root login owns the whole account and cannot be
  scoped down; a key for it is a key to everything, including closing the account and
  reading the card on file. Never create one. If the account already has one, say so
  plainly and delete it (see **Root access keys** at the end).
- **The member types their own passwords.** Never type, request, or repeat an AWS
  password, a card number, or a verification code. You drive the pages; they drive the
  sign-in.
- **Ask the region. Never assume one.** Not the account's default, not `us-east-1`, not
  the region of whatever console page happened to load.
- **The secret access key is written, never spoken.** It has to pass through this
  conversation once, when it is read off the console page — that is the single documented
  exception to the skill's credentials-never-in-context rule, and it is why the key
  belongs to a scoped, dedicated user that can be revoked with two clicks. Write it to
  disk immediately, never repeat it back, never put it in a summary, and show only the
  last four characters of the key **id** when confirming.

---

## Stage 0 — find out what's actually missing

Run all three; each one narrows the work (silent — narrate the conclusion, not the
commands):

```bash
command -v aws            # is the CLI installed at all?
aws configure list        # is a profile configured, and with which region?
aws sts get-caller-identity --output json
```

`get-caller-identity` returning JSON with an `Account` and an `Arn` means everything is
already in place — say so and go back to the verb that sent you here. Read the `Arn`
before you do: one ending in `:root` is the root login, which must be replaced, not used
(jump to **Stage 4** to make a proper user, then **Root access keys**).

Otherwise start at the earliest stage that is missing something: no `aws` binary →
Stage 1; no account → Stage 2; account but no `claude-assistant` user → Stage 3.

## Stage 1 — install the CLI

Tell the member this takes a minute or two, then install for the platform this machine is:

```bash
# macOS
brew install awscli

# Ubuntu / Debian
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install --update

# Windows (PowerShell)
winget install --id Amazon.AWSCLI -e
```

The positive check is a version number, not the absence of complaint:

```bash
aws --version    # expect: aws-cli/2.x.x ...
```

If the shell still can't find `aws` afterwards, the install worked but this shell's `PATH`
predates it — start a fresh shell and check again before treating it as a failure.

## Stage 2 — the account, opened by the member

Account signup asks for a card, a phone number and a real identity. It is theirs to do,
and Playwright must not drive it. Open the page in **their own default browser** so they
finish it in a normal window:

```bash
open "https://portal.aws.amazon.com/billing/signup"          # macOS
xdg-open "https://portal.aws.amazon.com/billing/signup"      # Linux
start "" "https://portal.aws.amazon.com/billing/signup"      # Windows
```

Say what's coming before they hit it — an email address and a password, a card, an SMS or
voice code, and a support-plan choice — then stay with them and answer as they go. The
questions that come up, and the answers:

| They ask | Answer |
|---|---|
| Personal or business account? | Either works. Business if the card and the ABN/company are the business's — it only changes the tax details on the invoice. |
| Why a card, if nothing is running yet? | Nothing bills until a server is launched, and that launch is a confirmed step with the price stated. The card is how AWS verifies the account. |
| Which support plan? | **Basic** — free, and enough. Developer and Business plans are paid and buy nothing this skill needs. |
| Is this free? | Don't promise the free tier. Quote the real figure from the skill's cost section — roughly US$12–18 a month for the default box, plus about US$2 for its disk, from launch until it's removed. |
| The card was declined / the code never arrived | Both are ordinary. A card with international payments blocked is the usual first cause; the code can take a few minutes and can be re-requested by voice instead of SMS. |

Signup finishes on a "Congratulations" page or in an email a few minutes later. Wait for
them to say they're in — account activation is occasionally not instant, and IAM pages
won't work until it is.

While they're at it, MFA on the root login is worth thirty seconds and is the single
biggest thing protecting the account. Offer it; don't insist, and don't let it block the
rest.

## Stage 3 — sign in to the console, then take over the browser

From here you drive, with **Playwright**. Open the IAM users page; not being signed in
yet, it will bounce to the sign-in form:

```
browser_navigate → https://console.aws.amazon.com/iam/home#/users
browser_snapshot
```

The sign-in form asks for root or IAM user. A member who has just created the account
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
without touching the member's login. Drive **Users → Create user**:

1. User name: `claude-assistant`.
2. Leave console access **off** — this login is for the CLI, so it needs no password.
3. Permissions: **Attach policies directly**, search `PowerUserAccess`, tick it.
4. Create user, and confirm from the resulting user page that the policy is attached.

**PowerUserAccess, not AdministratorAccess.** PowerUserAccess covers every service this
skill touches — EC2 instances, key pairs, security groups, the SSM parameter that resolves
the Ubuntu image — while withholding the ability to create users, change permissions, or
alter billing. Administrator adds nothing provision needs and hands over the whole
account. If the member asks for Administrator "to be safe", it is the opposite of safe:
say that the narrower policy is what makes an assistant's key survivable if it ever leaks.

If a `claude-assistant` user already exists, reuse it — check its attached policy is
PowerUserAccess and move on.

## Stage 5 — one access key for that user

On the user's **Security credentials** tab → **Create access key**:

1. Purpose: **Command Line Interface (CLI)**.
2. Tick the acknowledgement, then Next, skip the description tag, Create.
3. On the retrieve page the secret is shown **once**. If it's masked, click **Show**
   first, then read both values off the page:

```
() => {
  const t = [...document.querySelectorAll('*')].map(e => (e.innerText || '').trim());
  return {
    akid: t.find(s => /^AKIA[A-Z0-9]{16}$/.test(s)),
    secret: t.find(s => /^[A-Za-z0-9+/=]{35,45}$/.test(s) && !s.startsWith('AKIA')),
  };
}
```

Validate both before using them — the id matches `AKIA` plus 16 characters, the secret is
a 40-character base64-ish string. A null secret means the page is still masking it; click
Show and read again rather than guessing.

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

Write the files directly, never echoing either value into chat. If `~/.aws/credentials`
already exists, read it first and check for a `[default]` profile — something else is
using this machine's AWS access, and clobbering it is a real outage. Back it up and say so.

```bash
mkdir -p "$HOME/.aws"
[ -f "$HOME/.aws/credentials" ] && cp "$HOME/.aws/credentials" "$HOME/.aws/credentials.bak"
umask 077
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

`$AKID`, `$SECRET` and `$REGION` have to be set in the **same shell call** as the heredoc
— shell variables don't survive between calls. Then verify:

```bash
aws sts get-caller-identity --output json
aws ec2 describe-regions --region "$REGION" --query 'Regions[0].RegionName' --output text
```

The first must return an `Arn` ending in `:user/claude-assistant` — an `Arn` ending in
`:root` means the wrong key got written, and the whole point was missed. The second proves
the key can actually reach EC2 in the chosen region, which `get-caller-identity` alone does
not (it succeeds for a key with no permissions at all).

Finally, click **Done** on the console page and tell the member what now exists:

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

## Root access keys — refuse, and clean up

Root keys are the one thing here worth interrupting for. Check while you're in the console
— the root **My security credentials** page lists them:

```
browser_navigate → https://console.aws.amazon.com/iam/home#/security_credentials
```

If the Access keys section is empty, good — say nothing and carry on. If a key is listed,
tell the member what it is in one line ("that key can do anything to the account,
including close it") and offer to remove it: **Actions → Deactivate**, confirm the account
still works, then **Actions → Delete**, which asks for the key id typed out to confirm.
Only the root login can do this, so it has to happen in the session they signed into.

Deactivate before deleting. If some other tool of theirs was quietly using that key, the
deactivation shows up as that tool breaking, which is recoverable; a deletion isn't. If
they'd rather keep it, that's their call — record that you flagged it, don't fight it, and
never use it for this skill.

## Gotchas

| Problem | Fix |
|---|---|
| IAM pages 403 or look empty right after signup | Activation hasn't finished. It's usually minutes, occasionally hours, and there is nothing to fix — wait and retry. |
| `get-caller-identity` works, but `run-instances` says not authorized | The key is real but under-scoped. Check the user's attached policy is PowerUserAccess, not a narrower one someone picked. |
| `Arn` ends in `:root` | Root keys are in use. Stage 4 to make the proper user, then delete the root key. |
| The secret was closed without being saved | It cannot be retrieved — the page shows it once. Delete that key and create a new one. |
| Shell can't find `aws` after a clean install | `PATH` in this shell predates the install. New shell, check again. |
| A second person needs to run these verbs | Their machine, their own `claude-assistant` key. Never copy `~/.aws/credentials` between machines. |
| Console lands in the wrong region | The console's region picker is cosmetic here — what matters is the region in `~/.aws/config`, and every command in this skill passes `--region` explicitly. |
