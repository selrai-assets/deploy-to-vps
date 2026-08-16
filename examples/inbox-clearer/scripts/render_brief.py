#!/usr/bin/env python3
"""Render the inbox-clearer HTML email body.

This script is the only place the email's look is defined. The automation must
call it. Building the HTML inline instead produces a different email and quietly
drops whatever was tuned here.

Usage:
  python3 render_brief.py < data.json > body.html

Input JSON shape:
  {
    "long_date": "MONDAY, 17 AUGUST 2026",
    "cleared": {
      "pre": int, "pre_capped": bool,
      "post": int, "post_capped": bool,
      "filed_total": int,
      "per_group": {"GitHub": 12, "Calendar replies": 3},
      "left_alone": int
    },
    "needs_attention": [
      {"sender":str,"recipient":str|null,"subject":str,"snippet":str,"ago":str,"thread_size":int}
    ],
    "fyi": [{"sender":str,"recipient":str|null,"subject":str,"ago":str,"thread_size":int}],
    "hidden_count": int,
    "analysed": int,
    "dry_run": bool
  }
"""

import html
import json
import sys

ACCENT = "#4F46E5"
BLACK = "#0A0A0A"
GRAPHITE = "#6E7180"
CLOUD = "#EDEFF7"
SMOKE = "#D3D6E0"
WHITE = "#FFFFFF"
PAGE_BG = "#F3F4F8"


def section_card(title, inner_html):
    return (
        f'<div style="background:{WHITE};border:1px solid {SMOKE};border-radius:8px;'
        f'padding:18px 22px;margin-bottom:16px;">'
        f'<div style="font-size:13px;font-weight:700;color:{ACCENT};letter-spacing:1.6px;'
        f'margin-bottom:12px;font-family:Helvetica,Arial,sans-serif;">{title}</div>'
        f"{inner_html}</div>"
    )


def quiet_line(text):
    return (
        f'<div style="color:{GRAPHITE};font-style:italic;font-size:14px;font-weight:500;">'
        f"{html.escape(text)}</div>"
    )


def count_label(value, capped):
    return f"{value}+" if capped else f"{value}"


def render_cleared(cleared):
    per_group = cleared.get("per_group") or {}
    parts = [f"{count} {name}" for name, count in per_group.items() if count]
    breakdown = ", ".join(parts) if parts else "nothing matched today"
    pre = count_label(cleared.get("pre", 0), cleared.get("pre_capped"))
    post = count_label(cleared.get("post", 0), cleared.get("post_capped"))
    filed = cleared.get("filed_total", 0)

    line = (
        f"Started at <strong>{pre}</strong> in the inbox, filed <strong>{filed}</strong> "
        f"as noise ({html.escape(breakdown)}), <strong>{post}</strong> left for you."
    )
    left_alone = cleared.get("left_alone", 0)
    if left_alone:
        line += (
            f'<div style="margin-top:8px;color:{GRAPHITE};font-size:13px;">'
            f"{left_alone} message{'s' if left_alone != 1 else ''} looked like noise but did not "
            f"match its check, so they were left where they were.</div>"
        )
    return (
        f'<div style="background:{CLOUD};border:1px solid {SMOKE};border-radius:8px;'
        f'padding:18px 22px;margin-bottom:16px;color:{BLACK};font-size:15px;line-height:1.55;">'
        f"{line}</div>"
    )


def render_needs_attention(rows):
    title = f"NEEDS ATTENTION &middot; {len(rows)}"
    if not rows:
        inner = (
            f'<div style="color:{BLACK};font-size:16px;padding:6px 0;font-weight:500;">'
            f"All clear. Nothing is waiting on you right now.</div>"
        )
        return section_card(title, inner)

    parts = []
    for row in rows:
        sender = html.escape(row.get("sender") or "Unknown")
        subject = html.escape(row.get("subject") or "") or '<span style="color:#999;">(no subject)</span>'
        snippet = html.escape(row.get("snippet") or "")
        when = html.escape(row.get("ago") or "")
        recipient = row.get("recipient")
        recipient_block = (
            f' <span style="color:{GRAPHITE};font-weight:400;">to {html.escape(recipient)}</span>'
            if recipient
            else ""
        )
        snippet_block = (
            f'<div style="font-size:14px;color:{BLACK};margin-top:6px;line-height:1.5;opacity:0.85;">'
            f"{snippet}</div>"
            if snippet
            else ""
        )
        parts.append(
            f'<div style="padding:16px 0;border-bottom:1px solid {CLOUD};">'
            f'<div style="font-size:17px;color:{BLACK};font-weight:700;">{sender}{recipient_block} '
            f'<span style="color:{GRAPHITE};font-size:13px;font-weight:500;">&middot; {when}</span></div>'
            f'<div style="font-size:15px;color:{BLACK};margin-top:4px;font-weight:500;">{subject}</div>'
            f"{snippet_block}</div>"
        )
    return section_card(title, "".join(parts))


def render_fyi(rows, hidden_count):
    title = f"FYI &middot; {len(rows)}"
    parts = []
    if not rows:
        parts.append(quiet_line("Nothing else to be across."))
    for row in rows:
        sender = html.escape(row.get("sender") or "Unknown")
        subject = html.escape(row.get("subject") or "") or '<span style="color:#999;">(no subject)</span>'
        when = html.escape(row.get("ago") or "")
        size = row.get("thread_size") or 0
        badge = (
            f' <span style="color:{GRAPHITE};font-size:12px;font-weight:500;">&middot; {size} msgs</span>'
            if size > 1
            else ""
        )
        recipient = row.get("recipient")
        sender_line = (
            f"<strong>{sender}</strong>"
            f'<span style="color:{ACCENT};font-weight:600;"> to {html.escape(recipient)}</span>'
            if recipient
            else f"<strong>{sender}</strong>"
        )
        parts.append(
            f'<div style="padding:13px 0;border-bottom:1px solid {CLOUD};">'
            f'<div style="font-size:15px;color:{BLACK};">{sender_line}'
            f'<span style="color:{GRAPHITE};font-size:13px;font-weight:500;"> &middot; {when}</span>'
            f"{badge}</div>"
            f'<div style="font-size:14px;color:{BLACK};margin-top:3px;opacity:0.8;">{subject}</div>'
            f"</div>"
        )
    if hidden_count:
        parts.append(
            f'<div style="margin-top:14px;padding:12px 16px;background:{CLOUD};border-radius:6px;'
            f'font-size:13px;color:{GRAPHITE};font-weight:500;">'
            f'<strong style="color:{BLACK};font-weight:700;">{hidden_count}</strong> '
            f"quiet thread{'s' if hidden_count != 1 else ''} hidden "
            f"(you replied last, or you are no longer addressed).</div>"
        )
    return section_card(title, "".join(parts))


def render_body(data):
    long_date = html.escape(data.get("long_date", ""))
    cleared = render_cleared(data.get("cleared") or {})
    needs = render_needs_attention(data.get("needs_attention") or [])
    fyi = render_fyi(data.get("fyi") or [], data.get("hidden_count") or 0)

    analysed = data.get("analysed") or 0
    footer_note = (
        f"Read the {analysed} newest thread{'s' if analysed != 1 else ''} still in the inbox."
        if analysed
        else ""
    )
    if data.get("dry_run"):
        footer_note = "Practice run. Nothing in the inbox was changed. " + footer_note

    return (
        f'<div style="background:{PAGE_BG};padding:24px 12px;font-family:Helvetica,Arial,sans-serif;'
        f'-webkit-font-smoothing:antialiased;">'
        f'<div style="max-width:680px;margin:0 auto;background:{WHITE};border:1px solid {SMOKE};'
        f'border-radius:12px;padding:32px 32px 28px;">'
        f'<h1 style="margin:0 0 6px;font-size:32px;font-weight:700;color:{BLACK};line-height:1.15;'
        f'font-family:Helvetica,Arial,sans-serif;letter-spacing:-0.5px;">Inbox Clearer</h1>'
        f'<div style="font-size:14px;font-weight:700;color:{ACCENT};letter-spacing:1.6px;'
        f'margin-bottom:28px;">{long_date}</div>'
        f"{cleared}{needs}{fyi}"
        f'<div style="margin-top:24px;color:{GRAPHITE};font-size:13px;">{html.escape(footer_note)}</div>'
        f"</div></div>"
    )


def main():
    sys.stdout.write(render_body(json.load(sys.stdin)))


if __name__ == "__main__":
    main()
