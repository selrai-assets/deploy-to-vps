# inbox-clearer

A working automation you can deploy today, and a worked example to copy when you build
your own.

Every weekday morning it files the notification noise out of your inbox (Hubstaff, GitHub,
Linear, build alerts, calendar replies, anything from a no-reply address), labels it, marks
it read, and then emails you an HTML brief: what it cleared, what needs your attention, and
what is worth being across.

Nothing is deleted, and a message is only filed when it came from a robot: the address it
was sent from has to look like `noreply@`, `notifications@` or similar, on top of matching
the group that found it. A message from a person stays in your inbox.

## What it is made of

```
automation.yaml           the manifest: name, owner, schedule, credentials
run.sh                    what one run executes
clear_inbox.py            the logic: file the noise, read what is left, send the brief
config.json               the noise groups and their labels, in plain JSON
scripts/render_brief.py   the email's look, and the only place it is defined
```

That is the shape of every automation on the server: a folder with a manifest at the top of
it. Copy this folder, change the parts that are yours, deploy it.

## Before you deploy it

You need the gws command line tool signed in to your Google account on your own computer.
The automation never asks who to send to. It reads the signed in address and sends the
brief there, so it works the same on your machine and on the server.

Try it on your own computer first, without changing anything:

```bash
./run.sh --dry-run
```

That lists every message it would file, and every message that looked like noise but did
not pass its check, so you can see the judgement before it happens. Nothing is changed and
no email is sent. The brief is written to a file so you can open it in a browser.

Happy with the list? Run it for real:

```bash
./run.sh
```

Your inbox changes and the brief arrives within about a minute.

## Then put it on the server

1. Open `automation.yaml` and change `owner` to your own email address.
2. Copy the folder to where you keep your automations, and point `source.location` at it.
3. Ask Claude to deploy it.

Deploy copies the folder onto the box, syncs your Google sign in into
`.credentials/` (locked to the automation's own user, never in any repo), installs the
schedule, and runs it once so you can see the brief land.

## How it decides what is noise

`config.json` holds the groups, in the order they run. Each group has two halves:

- a Gmail search, which finds candidates in the inbox
- a confirmation pattern, which has to agree before anything is touched

Both have to match. A DMARC report from a sender the pattern does not recognise, for
example, gets left exactly where it is and shows up in the dry run under "left alone". When
in doubt, the automation does nothing. That is the rule the whole thing is built on.

The confirmation patterns are deliberately about the address, not the company. Writing
`{automated}` in a pattern drops in the shared list of robot addresses at the top of
`config.json`, so `^{automated}@...linear\.app$` files the notification mail from Linear
and leaves a message from a person who happens to work there alone. Keep the `{automated}`
part when you add a group for a tool you use.

Labels are looked up by name and created when they are missing, so nothing is tied to one
mailbox. The groups ship with a `Notifications/...` label each: `Notifications/Hubstaff`,
`Notifications/GitHub`, `Notifications/Linear`, `Notifications/Builds`,
`Notifications/Calendar`, `Notifications/Inbox Clearer` and `Notifications/Automated`.

Nothing is deleted. Everything filed keeps its label, so it is one click away in Gmail.

### Making it yours

Add a group to `config.json` for the tool that clutters your inbox:

```json
{
  "key": "helpdesk",
  "label": "Notifications/Helpdesk",
  "pretty": "Helpdesk",
  "query": "from:helpdesk.example.com",
  "confirm_sender": "^{automated}@helpdesk\\.example\\.com$"
}
```

Order matters. Named groups run first, and the broad `automated` catch all runs last.

Three other settings live there: `analyse_threads` (how many of the newest inbox threads
the brief reads, 40 by default), `max_per_group` (how many messages one group files in a
single run, 200 by default, with the rest waiting for the next run) and `subject_prefix`
(the subject line of the brief). If you change `subject_prefix`, change the `past_briefs`
group's `query` and `confirm_subject` to match, or it stops finding yesterday's brief.

The shipped groups treat sign in codes and security alerts from those senders as noise as
well, because they come from no-reply addresses. If you would rather keep those in the
inbox, tighten that group's `confirm_sender` or drop it.

## What lands in the brief

- **Cleared**: how many messages were in the inbox, how many were filed and by which group,
  how many are left
- **Needs attention**: threads addressed to you, from a person, where the latest message
  reads like someone is waiting on you
- **FYI**: everything else worth a glance, in one line each
- **Hidden**: a count of threads where you replied last, or where you are no longer
  addressed

The email's layout lives in `scripts/render_brief.py` and nowhere else. If you want a
different look, edit that file. Do not build the HTML anywhere else in the automation.

## What it will not do

- It will not reply to anything, delete anything, or archive a message from a person.
- It will not send to anyone but you.
- It will not read message bodies. Sender, subject and Gmail's own preview line are enough.
