"""Inbox screen for the email triage agent.

Opens a mail-client style page in the browser. Press "Triage inbox" and the
agent works through data/inbox.json one email at a time, using exactly the
same graph as process_inbox.py. You can also write your own test email.

Run:
    python app.py
"""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from agent.llm import DEFAULT_MODEL
from agent.tools import load_inbox
from agent.triage import triage_email

load_dotenv()

logger = logging.getLogger("email-triage")
app = FastAPI(title="Email Triage Agent")
WEB_DIR = Path(__file__).resolve().parent / "web"


class Email(BaseModel):
    id: str = Field(default="CUSTOM", max_length=40)
    sender: str = Field(alias="from", min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=5000)


@app.get("/", include_in_schema=False)
def inbox_screen():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/info")
def info():
    return {"model": os.getenv("LLM_MODEL") or DEFAULT_MODEL}


@app.get("/api/inbox")
def inbox():
    return load_inbox()


@app.post("/api/triage")
def triage(email: Email):
    """Classify one email and take the action for its category."""
    started = time.perf_counter()
    payload = {"id": email.id, "from": email.sender, "subject": email.subject, "body": email.body}
    try:
        result = triage_email(payload)
    except Exception as exc:
        logger.exception("Triage failed for %s", email.id)
        detail = str(exc).splitlines()[0][:200] if str(exc) else ""
        return JSONResponse(status_code=502, content={"error": f"The agent could not triage this email ({type(exc).__name__}: {detail})."})
    return {
        "id": email.id,
        "category": result["category"],
        "reasoning": result["reasoning"],
        "action": result["action"],
        "draft": result.get("draft"),
        "seconds": round(time.perf_counter() - started, 1),
    }


if __name__ == "__main__":
    import threading
    import webbrowser

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    uvicorn.run(app, host="127.0.0.1", port=port)
