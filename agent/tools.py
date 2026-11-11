"""FAQ lookup, inbox reading, and reply drafting.

Everything here runs against local files. There is no Gmail integration in
this version, replies are drafted and returned, never sent. Connecting a
real inbox is the first thing I'd do on a client project, see the README.
"""

import json
import os
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(filename: str):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def load_inbox() -> list[dict]:
    return _load("inbox.json")


def search_faq(text: str) -> str | None:
    faqs = _load("faq.json")
    text_lower = text.lower()

    best_match = None
    best_score = 0
    for entry in faqs:
        score = sum(1 for kw in entry["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = entry

    return best_match["answer"] if best_match and best_score > 0 else None


def notify_urgent(email: dict) -> str | None:
    """Posts to Slack if SLACK_WEBHOOK_URL is set. This one does really fire."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return None

    message = f"Urgent email flagged: '{email['subject']}' from {email['from']}"
    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        # A Slack outage shouldn't stop the rest of the inbox being triaged.
        return f"Slack alert failed: {exc}"
    return "posted to Slack"


def draft_reply(to: str, subject: str, body: str) -> str:
    """Builds the reply that would be sent and returns a description of it.

    Nothing leaves the machine. Named draft_reply rather than send_reply
    so nobody reading a log line thinks mail actually went out.
    """
    return f"Drafted reply to {to}, subject: Re: {subject}"
