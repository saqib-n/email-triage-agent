from fastapi.testclient import TestClient

import app as web


def test_inbox_screen_and_triage_api(monkeypatch):
    seen = []

    def fake_triage(email):
        seen.append(email)
        return {"category": "routine", "reasoning": "Standard question.", "action": "Answer found in FAQ.", "draft": "We reply Monday to Friday."}

    monkeypatch.setattr(web, "triage_email", fake_triage)
    client = TestClient(web.app)

    assert "Triage inbox" in client.get("/").text
    assert len(client.get("/api/inbox").json()) == 6

    email = {"id": "MSG-001", "from": "priya@customerco.com", "subject": "Hours?", "body": "When are you open?"}
    result = client.post("/api/triage", json=email).json()
    assert result["category"] == "routine" and result["draft"] == "We reply Monday to Friday."
    assert seen[0]["from"] == "priya@customerco.com"
    assert client.post("/api/triage", json={**email, "body": ""}).status_code == 422

    monkeypatch.setattr(web, "triage_email", lambda email: (_ for _ in ()).throw(RuntimeError("quota")))
    assert client.post("/api/triage", json=email).status_code == 502
