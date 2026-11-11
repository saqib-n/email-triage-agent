"""Triage every email in data/inbox.json and log the result.

Run:
    python process_inbox.py
"""

import csv
from pathlib import Path

from dotenv import load_dotenv

from agent.tools import load_inbox
from agent.triage import triage_email

load_dotenv()

OUTPUT_DIR = Path(__file__).parent / "output"
LOG_FILE = OUTPUT_DIR / "triage_log.csv"


def main():
    inbox = load_inbox()
    if not inbox:
        print("Inbox is empty, nothing to triage.")
        return

    print(f"Triaging {len(inbox)} emails\n")

    OUTPUT_DIR.mkdir(exist_ok=True)
    rows = []
    counts = {"routine": 0, "urgent": 0, "needs_human": 0, "spam": 0}

    for email in inbox:
        result = triage_email(email)
        category = result["category"]
        counts[category] += 1

        print(f"[{category.upper()}] {email['subject']} (from {email['from']})")
        print(f"  Reason: {result['reasoning']}")
        print(f"  Action: {result['action']}")
        if result.get("draft"):
            print(f"  Draft: {result['draft']}")
        print()

        rows.append({
            "id": email["id"],
            "from": email["from"],
            "subject": email["subject"],
            "category": category,
            "reasoning": result["reasoning"],
            "action": result["action"],
            "draft": result.get("draft") or "",
        })

    with open(LOG_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Summary: {counts}")
    print(f"Full log saved to {LOG_FILE}")


if __name__ == "__main__":
    main()
