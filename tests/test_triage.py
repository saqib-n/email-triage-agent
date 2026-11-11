from agent import triage
from agent.tools import load_inbox, notify_urgent, search_faq
from tests.fakes import FakeStructuredLLM

EMAILS = {e["id"]: e for e in load_inbox()}


def test_faq_matches_common_questions():
    assert "Monday to Friday" in search_faq("what are your business hours?")
    assert "20% off" in search_faq("do you have a student discount")
    assert search_faq("can I bring my dog to the office") is None


def test_routine_without_faq_answer_goes_to_a_human():
    email = {"from": "a@example.com", "subject": "Dogs?", "body": "Can I bring my dog?"}
    result = triage.routine_node({"email": email})
    assert result["draft"] is None
    assert "human review" in result["action"]


def test_urgent_never_drafts_and_slack_is_optional(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    assert notify_urgent(EMAILS["MSG-002"]) is None
    result = triage.urgent_node({"email": EMAILS["MSG-002"]})
    assert result["draft"] is None and "URGENT" in result["action"]


def test_full_pipeline_with_stand_in_model(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    llm = FakeStructuredLLM(triage.EmailCategory(category="routine", reasoning="Standard question."))
    graph = triage.build_graph(llm=llm)
    result = graph.invoke({"email": EMAILS["MSG-001"]})
    assert result["category"] == "routine"
    assert "Monday to Friday" in result["draft"]
