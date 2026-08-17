#!/usr/bin/env python3
"""Clear notification noise out of the Gmail inbox, then email a brief of what is left.

One run does three things:

  1. Files notification noise. Each group in config.json has a Gmail search and a
     confirmation pattern. A message is only touched when both agree, so anything
     ambiguous is left alone.
  2. Reads what is still in the inbox and sorts the newest threads into
     "needs attention" and "FYI".
  3. Renders an HTML brief with scripts/render_brief.py and emails it to whoever
     the gws CLI is signed in as.

Usage:
  python3 clear_inbox.py            # the real run: files noise, sends the brief
  python3 clear_inbox.py --dry-run  # touches nothing, lists what it would file

Everything talks to Google through the gws CLI, so the only sign-in involved is
the one already on the machine. No address, label id or token is hardcoded.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from email.utils import getaddresses

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERER = os.path.join(HERE, "scripts", "render_brief.py")
CONFIG = os.path.join(HERE, "config.json")

GWS = os.environ.get("GWS_BIN", "gws")

# Gmail takes at most 1000 ids in one batchModify call.
BATCH_MODIFY_LIMIT = 1000

# A sender the brief treats as a robot rather than a person. Anything from one of
# these lands in FYI even when it survived the filing pass.
AUTO_LOCALPARTS = re.compile(
    r"^(no[-_.]?reply|do[-_.]?not[-_.]?reply|notifications?|alerts?|support|info|"
    r"team|hello|hi|contact|sales|marketing|admin|billing|accounts?|invoices?|"
    r"receipts?|news|newsletter|updates?|mailer-daemon|postmaster|bounces?|dmarc)"
    r"([-_.+][a-z0-9._-]*)?$",
    re.IGNORECASE,
)

# Wording that suggests someone is waiting on a reply.
ASK_SIGNALS = [
    "?",
    "please",
    "can you",
    "could you",
    "would you",
    "let me know",
    "review",
    "approve",
    "sign off",
    "follow up",
    "confirm",
    "available",
    "thoughts on",
    "wanted to ask",
    "had a question",
    "by friday",
    "asap",
    "action required",
]


class GwsError(RuntimeError):
    """A gws call failed. Carries the command, never the payload."""


def gws(args, params=None, body=None, label=None):
    """Run one gws call and return its parsed JSON (an empty dict when it returns none).

    `label` names the call in any error. Pass one whenever the arguments carry a
    payload (an address, an email body) so a failure never echoes it back.
    """
    name = label or " ".join(args)
    cmd = [GWS] + args
    if params is not None:
        cmd += ["--params", json.dumps(params)]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    cmd += ["--format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()
        raise GwsError(f"gws {name} failed: {detail[-1] if detail else 'no output'}")
    out = (proc.stdout or "").strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise GwsError(f"gws {name} returned output that is not JSON") from exc


# ---------------------------------------------------------------- account


def signed_in_address():
    """The mailbox this run works on: whoever the gws CLI is signed in as."""
    profile = gws(["gmail", "users", "getProfile"], params={"userId": "me"})
    address = (profile.get("emailAddress") or "").strip()
    if not address:
        raise GwsError("could not read the signed-in address from the Gmail profile")
    return address


# ---------------------------------------------------------------- labels


def label_map():
    """Every label in the mailbox, by name. Ids differ per mailbox, so never hardcode one."""
    data = gws(["gmail", "users", "labels", "list"], params={"userId": "me"})
    return {label["name"]: label["id"] for label in data.get("labels", [])}


def resolve_label(name, labels):
    """The id for a label name, creating the label (and any parent) when it is missing."""
    if name in labels:
        return labels[name]
    parent = name.rsplit("/", 1)[0] if "/" in name else None
    if parent and parent not in labels:
        resolve_label(parent, labels)
    created = gws(
        ["gmail", "users", "labels", "create"],
        params={"userId": "me"},
        body={
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    )
    labels[name] = created["id"]
    return created["id"]


# ---------------------------------------------------------------- messages


def list_ids(query, max_results=200):
    """Ids matching a search, plus whether the search had more than max_results."""
    data = gws(
        ["gmail", "users", "messages", "list"],
        params={"userId": "me", "q": query, "maxResults": max_results},
    )
    ids = [m["id"] for m in data.get("messages", [])]
    return ids, bool(data.get("nextPageToken"))


def message_meta(message_id):
    data = gws(
        ["gmail", "users", "messages", "get"],
        params={
            "userId": "me",
            "id": message_id,
            "format": "metadata",
            "metadataHeaders": ["From", "Sender", "To", "Cc", "Subject", "Date"],
        },
    )
    return flatten(data)


def thread_messages(thread_id):
    data = gws(
        ["gmail", "users", "threads", "get"],
        params={
            "userId": "me",
            "id": thread_id,
            "format": "metadata",
            "metadataHeaders": ["From", "To", "Cc", "Subject", "Date"],
        },
    )
    return [flatten(m) for m in data.get("messages", [])]


def flatten(message):
    headers = {
        h["name"].lower(): h["value"]
        for h in message.get("payload", {}).get("headers", [])
    }
    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "from": headers.get("from", ""),
        "sender": headers.get("sender", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "subject": headers.get("subject", ""),
        "snippet": (message.get("snippet") or "").strip(),
        "internal_date": int(message.get("internalDate") or 0),
    }


def inbox_count(cap):
    """How many messages sit in the inbox, counted page by page up to cap."""
    total = 0
    token = None
    while total < cap:
        params = {"userId": "me", "q": "label:INBOX", "maxResults": 500}
        if token:
            params["pageToken"] = token
        data = gws(["gmail", "users", "messages", "list"], params=params)
        total += len(data.get("messages", []))
        token = data.get("nextPageToken")
        if not token:
            return total, False
    return total, True


# ---------------------------------------------------------------- filing


def addresses(header):
    return [addr.lower() for _, addr in getaddresses([header or ""]) if addr]


def first_address(header):
    found = addresses(header)
    return found[0] if found else ""


def display_name(header):
    parsed = getaddresses([header or ""])
    if not parsed:
        return "Unknown"
    name, addr = parsed[0]
    if name:
        return name.strip('"')
    return addr.split("@")[0] if addr else "Unknown"


def expand(pattern, automated):
    """Put the shared automated-localpart pattern wherever a group wrote {automated}."""
    return pattern.replace("{automated}", automated) if pattern else pattern


def confirms(group, meta, me, automated):
    """Only file a message when the group's own pattern agrees with the search."""
    sender = first_address(meta["from"])
    checks = 0

    pattern = expand(group.get("confirm_sender"), automated)
    if pattern:
        checks += 1
        if not re.search(pattern, sender, re.IGNORECASE):
            return False

    # Some notifications carry the organiser in From and the robot in Sender.
    # Calendar replies are the common case.
    header_pattern = expand(group.get("confirm_sender_header"), automated)
    if header_pattern:
        checks += 1
        if not re.search(header_pattern, first_address(meta["sender"]), re.IGNORECASE):
            return False

    subject_pattern = expand(group.get("confirm_subject"), automated)
    if subject_pattern:
        checks += 1
        if not re.search(subject_pattern, meta["subject"], re.IGNORECASE):
            return False

    if group.get("confirm_from_self"):
        checks += 1
        if sender != me:
            return False

    return checks > 0  # a group with no confirmation would file blind


def file_noise(config, me, dry_run):
    """Walk the groups in order and file what each one confirms."""
    labels = label_map()
    automated = config.get("automated_localpart", "(?!)")
    per_group_cap = config.get("max_per_group", 200)
    filed = {}
    would_file = []
    # A message can match one group's search, fail its confirmation, and then be
    # filed by a later, broader group. Key the left-alone set by message id so it
    # is counted once, and drop anything that was filed in the end.
    left_alone = {}
    # A real run takes each group's messages out of the inbox before the next
    # group searches, so the later, broader groups never see them again. Track
    # the same set by hand so a dry run reports the same numbers.
    handled = set()

    for group in config["groups"]:
        query = "label:INBOX " + group["query"]
        found, more = list_ids(query, per_group_cap)
        if more:
            print(
                f"note: {group['key']} matched more than {per_group_cap} messages; "
                f"the rest wait for the next run"
            )
        ids = [i for i in found if i not in handled]
        confirmed = []
        for message_id in ids:
            meta = message_meta(message_id)
            if confirms(group, meta, me, automated):
                confirmed.append(meta)
            else:
                left_alone.setdefault(message_id, (group["key"], meta))
        if not confirmed:
            continue
        handled.update(meta["id"] for meta in confirmed)
        would_file.extend((group["key"], meta) for meta in confirmed)
        filed[group["key"]] = len(confirmed)
        if dry_run:
            continue
        label_id = resolve_label(group["label"], labels)
        ids_to_modify = [meta["id"] for meta in confirmed]
        for start in range(0, len(ids_to_modify), BATCH_MODIFY_LIMIT):
            gws(
                ["gmail", "users", "messages", "batchModify"],
                params={"userId": "me"},
                body={
                    "ids": ids_to_modify[start : start + BATCH_MODIFY_LIMIT],
                    "addLabelIds": [label_id],
                    "removeLabelIds": ["INBOX", "UNREAD"],
                },
            )

    skipped = [entry for mid, entry in left_alone.items() if mid not in handled]
    return filed, would_file, skipped


# ---------------------------------------------------------------- what is left


def ago(internal_date_ms, now=None):
    now = now or datetime.now(timezone.utc)
    then = datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)
    minutes = int((now - then).total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def recipient_of(latest, me):
    """Who the latest message was addressed to, with your own address dropped."""
    others = [a for a in addresses(latest["to"]) if a != me]
    if not others:
        return None
    parsed = {addr.lower(): name for name, addr in getaddresses([latest["to"] or ""])}
    first = others[0]
    label = parsed.get(first) or first.split("@")[0]
    label = label.strip('"') or first
    if len(others) > 1:
        label = f"{label} +{len(others) - 1}"
    return label


def classify(latest, me):
    """hidden, fyi or needs_attention. First match wins, and borderline means FYI."""
    sender = first_address(latest["from"])
    to = addresses(latest["to"])
    cc = addresses(latest["cc"])

    if sender == me:
        return "hidden"  # you replied last, the ball is with them
    if me not in to and me not in cc:
        return "hidden"  # a thread you are no longer addressed on

    local = sender.split("@")[0] if sender else ""
    if AUTO_LOCALPARTS.match(local):
        return "fyi"
    if me in cc and me not in to:
        return "fyi"

    haystack = f"{latest['subject']} {latest['snippet']}".lower()
    if any(signal in haystack for signal in ASK_SIGNALS):
        return "needs_attention"
    return "fyi"


def read_remaining(me, window):
    """Sort the newest inbox threads into needs attention, FYI and hidden."""
    ids = gws(
        ["gmail", "users", "messages", "list"],
        params={"userId": "me", "q": "label:INBOX", "maxResults": 500},
    ).get("messages", [])

    seen = []
    for entry in ids:
        if entry["threadId"] not in seen:
            seen.append(entry["threadId"])
        if len(seen) >= window:
            break

    needs_attention, fyi = [], []
    hidden = 0
    for thread_id in seen:
        messages = sorted(
            thread_messages(thread_id), key=lambda m: m["internal_date"], reverse=True
        )
        if not messages:
            continue
        latest = messages[0]
        bucket = classify(latest, me)
        if bucket == "hidden":
            hidden += 1
            continue
        row = {
            "sender": display_name(latest["from"]),
            "recipient": recipient_of(latest, me),
            "subject": latest["subject"],
            "ago": ago(latest["internal_date"]),
            "thread_size": len(messages),
        }
        if bucket == "needs_attention":
            row["snippet"] = latest["snippet"][:220]
            needs_attention.append(row)
        else:
            fyi.append(row)

    return needs_attention, fyi, hidden, len(seen)


# ---------------------------------------------------------------- brief


def render(data):
    """The HTML body always comes from the renderer script. Never build it inline."""
    if not os.path.exists(RENDERER):
        raise RuntimeError(f"renderer missing at {RENDERER}")
    proc = subprocess.run(
        [sys.executable, RENDERER],
        input=json.dumps(data),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"renderer failed: {(proc.stderr or '').strip()[:300]}")
    if not proc.stdout.strip():
        raise RuntimeError("renderer produced an empty brief")
    return proc.stdout


def send(address, subject, html):
    result = gws(
        ["gmail", "+send", "--to", address, "--subject", subject, "--body", html, "--html"],
        label="gmail +send",  # keeps the address and the rendered body out of any error
    )
    return result.get("id", "sent")


# ---------------------------------------------------------------- run


def main():
    parser = argparse.ArgumentParser(description="Clear inbox noise and email a brief.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="change nothing: list what would be filed and write the brief to a file",
    )
    args = parser.parse_args()

    with open(CONFIG, encoding="utf-8") as handle:
        config = json.load(handle)

    me = signed_in_address()
    print(f"mailbox: {me}")

    cap = config.get("inbox_count_cap", 2000)
    pre, pre_capped = inbox_count(cap)

    filed, would_file, skipped = file_noise(config, me, args.dry_run)

    if args.dry_run:
        print(f"\nwould file {len(would_file)} message(s):")
        for key, meta in would_file:
            print(f"  [{key}] {meta['id']}  {first_address(meta['from'])}  {meta['subject'][:70]}")
        print(f"\nleft alone (matched a search but not its confirmation): {len(skipped)}")
        for key, meta in skipped:
            print(f"  [{key}] {first_address(meta['from'])}  {meta['subject'][:70]}")
        # Nothing moved, so report the count the inbox would have been left at.
        post, post_capped = max(pre - len(would_file), 0), pre_capped
    else:
        post, post_capped = inbox_count(cap)

    needs_attention, fyi, hidden, analysed = read_remaining(
        me, config.get("analyse_threads", 40)
    )

    now = datetime.now()
    data = {
        "long_date": now.strftime("%A, %d %B %Y").upper(),
        "cleared": {
            "pre": pre,
            "pre_capped": pre_capped,
            "post": post,
            "post_capped": post_capped,
            "filed_total": sum(filed.values()),
            "per_group": {
                group["pretty"]: filed[group["key"]]
                for group in config["groups"]
                if filed.get(group["key"])
            },
            "left_alone": len(skipped),
        },
        "needs_attention": needs_attention,
        "fyi": fyi,
        "hidden_count": hidden,
        "analysed": analysed,
        "dry_run": args.dry_run,
    }

    html = render(data)
    subject = f"{config.get('subject_prefix', 'Inbox Clearer')} {now.strftime('%Y-%m-%d')}"

    if args.dry_run:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".html", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(html)
            path = handle.name
        print(f"\nbrief written to {path} (nothing sent)")
    else:
        message_id = send(me, subject, html)
        print(f"\nbrief sent, message id {message_id}")

    breakdown = ", ".join(f"{v} {k}" for k, v in data["cleared"]["per_group"].items())
    print(
        f"filed {data['cleared']['filed_total']} of {pre} inbox messages"
        f"{' (' + breakdown + ')' if breakdown else ''}, {post} remain, "
        f"{len(needs_attention)} need attention"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (GwsError, RuntimeError) as error:
        print(f"inbox-clearer failed: {error}", file=sys.stderr)
        sys.exit(1)
