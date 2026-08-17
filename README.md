# The Always-On Server

Your automations should keep running when your laptop is shut, on a plane, or out of
battery. This kit rents you a small computer in a data centre, sets it up properly, and
puts your automations on it with a schedule that fires whether you are at your desk or
not.

You do not touch a server. You talk to Claude, and Claude does the whole thing: opens the
account, rents the machine, locks it down, installs your automation, sets its schedule,
and shows you the first real run working.

Made by Selr AI.

## Install

Paste this into Claude Code (or Codex, or another coding agent):

> Clone https://github.com/selrai-assets/deploy-to-vps and follow SETUP-PROMPT.md

That is the whole install. There is nothing to unzip and no command for you to type.
Claude clones the repo, installs the skill, checks it is complete, and tells you it is
ready. Installing spends no money and starts no server: one does not exist until you ask
for it, and Claude states the monthly price and waits for your yes before launching one.

## An automation, in this kit

An **automation** is one job you want done on a schedule, packaged as a folder: the code
that does the job, plus one small file next to it saying what it is called, who owns it,
when it should run, and which sign-ins it needs. That is the whole format. It can be a
script you had written, something Claude builds for you, or the demo further down.

The server is where those folders live and run. One server holds as many automations as
you care to put on it, each on its own schedule.

## Your only jobs

Three, and they never change:

1. **Sign in to your own accounts.** Your email, your password, your card. Claude never
   types those and never asks you to read them out.
2. **Click Allow** when something asks for permission.
3. **Say yes to costs.** Nothing that bills money or deletes anything happens without you
   agreeing first, with the number in front of you.

Everything else is Claude's job. If you find yourself being handed a command to type,
something has gone wrong.

## What it costs

The server is rented by the month from Amazon Web Services, and you pay Amazon directly.
Rounded up, and including the storage that goes with it:

| Server | Roughly per month | Right for |
|---|---|---|
| Standard | US$15 to US$25 | Scripts, email and document jobs, scheduled Claude work |
| Larger | US$28 to US$38 | Automations that drive a web browser, because a browser wants more memory |

Prices move a little by region and by exchange rate, so budget the top of the range you
pick. Billing starts the moment the server launches and stops when you ask for the server
to be removed. Nothing accumulates in the background: one server, one monthly cost,
visible on your own Amazon bill.

Two things worth knowing about the money. Amazon asks for a card during signup even
though nothing is running yet, because that is how it verifies an account. And scheduled
Claude work on the server signs in as you, so it draws on your own Claude plan's usage
rather than needing a separate paid account set up alongside it.

## What you need before you start

- A Mac or Linux computer with Claude Code on it. Windows works too, with the small
  caveat that the install steps want WSL or Git Bash rather than PowerShell.
- A card and a phone for the Amazon signup. If you do not have an Amazon Web Services
  account, Claude walks you through creating one and answers the questions as they come.
- Somewhere between half an hour and two hours for the first setup. Most of that is
  waiting on Amazon rather than on Claude: new accounts usually activate in minutes, but
  occasionally take hours, and nothing can be built until that clears. After the first
  time, putting a new automation on the server is five to fifteen minutes, most of it
  installing what the automation needs.
- For the bundled demo specifically, a Google mailbox.

## What it does once installed

You ask for these in plain English. There is nothing to memorise.

| You say | What happens |
|---|---|
| "Set up my always-on server" | A new server is created and locked down, with the cost confirmed before it launches |
| "Deploy my inbox clearer" | Your automation is copied over, its schedule set, and run once for real so you can watch it work |
| "Is the server running?" or "Show me the logs" | What is on the server, when each job last ran and next runs, and what happened, in plain English |
| "Put my automation on my colleague's server" | Your machine is set up to reach a server somebody else owns, or you get told exactly what is blocking it |
| "Give my business partner access" | A short message you can forward that lets them grant themselves access, with no password shared between you |
| "The server needs more power" | The server is resized, with the new monthly cost confirmed first |
| "Take it down" | One automation, or the whole server, is removed and the billing stops |

Locked down is the default rather than an option. The server takes one kind of connection
only, using a key rather than a password. A firewall closes every other way in, and
security updates install themselves. Access is granted one person at a time and taken
away the same way, so there is never a shared login floating around.

Your automations keep their sign-ins in a private folder on the server, copied straight
from your machine to the server without ever passing through the chat.

## The one thing you cannot undo

Removing the whole server destroys it and everything on it, and there is no way back.
Claude shows you what is still on the server and asks for an explicit yes first, but that
yes is final. Anything worth keeping should live in a repo or on your own machine as
well, not only on the server. Removing a single automation is the safer everyday move: it
takes that one job off the server and leaves the rest running.

## The demo that comes with it

`examples/inbox-clearer/` is a working automation, bundled so you have something real to
watch before you build your own. It is your server's first job.

It goes through your inbox and files the notification noise: the alerts and status emails
from the tools you use, labelled and marked read, so what is left in front of you is
actual messages from actual people. Then it emails you a short brief of what it cleared
and what still needs your attention.

Say *"deploy the inbox clearer"* and it goes onto the server on a schedule you choose,
working on your own mailbox and emailing the brief to you. It needs a Google mailbox,
signed in on your machine, and it never reads anything beyond your email. Nothing about
it is specific to us, so it is also the easiest thing to copy when you want to build the
next one.

## What is in this repo

- [`SETUP-PROMPT.md`](SETUP-PROMPT.md) is the install path, start to finish. Claude reads
  it, not you, but nothing in it is hidden from you.
- `skills/deploy-to-vps/` is the skill itself: the jobs listed above, the format that
  describes an automation, the recipes for the different things an automation can be
  written in, and the script that locks the server down.
- `skills/deploy-to-vps/references/aws-setup.md` is the path from no Amazon account at
  all to a working connection, which is why nothing else has to be installed first.
- `examples/inbox-clearer/` is the demo automation described above.
- `docs/` and `research/` hold the design notes and the working agreements behind the
  kit, kept for the curious.
