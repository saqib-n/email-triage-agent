"""LangGraph pipeline for one email: classify, then act.

Four categories: routine (auto-answerable from the FAQ), urgent (needs a
human right now), needs_human (not urgent, but not something the agent
should answer on its own), and spam. Each gets handled differently, only
routine emails get an automatic reply, everything else is about routing
and drafting, not deciding on behalf of a person.
"""

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from agent.llm import get_llm
from agent.tools import draft_reply, notify_urgent, search_faq


class EmailCategory(BaseModel):
    category: Literal["routine", "urgent", "needs_human", "spam"] = Field(
        description=(
            "routine: a common question that has a standard answer. "
            "urgent: needs a human's attention today, complaints, legal, angry customers, "
            "threats to cancel. needs_human: not urgent, but requires judgment or "
            "relationship context an agent shouldn't handle alone, e.g. partnership "
            "discussions, sales conversations. spam: promotional junk, obviously not real."
        )
    )
    reasoning: str = Field(description="One sentence on why this category")


class EmailState(TypedDict):
    email: dict
    category: str
    reasoning: str
    action: str
    draft: str | None


def classify_node(state: EmailState, llm) -> dict:
    email = state["email"]
    system = SystemMessage(content="Classify this email for a support inbox triage system.")
    human = HumanMessage(content=f"From: {email['from']}\nSubject: {email['subject']}\nBody: {email['body']}")

    structured_llm = llm.with_structured_output(EmailCategory)
    result = structured_llm.invoke([system, human])
    return {"category": result.category, "reasoning": result.reasoning}


def routine_node(state: EmailState) -> dict:
    email = state["email"]
    faq_answer = search_faq(f"{email['subject']} {email['body']}")

    if faq_answer is None:
        return {
            "action": "No FAQ match found despite routine classification, flagged for human review instead.",
            "draft": None,
        }

    status = draft_reply(to=email["from"], subject=email["subject"], body=faq_answer)
    return {"action": f"Answer found in FAQ. {status}", "draft": faq_answer}


def urgent_node(state: EmailState) -> dict:
    email = state["email"]
    slack_status = notify_urgent(email)
    action = "Flagged URGENT, needs a human today, no auto-reply sent."
    if slack_status:
        action += f" ({slack_status})"
    return {"action": action, "draft": None}


def needs_human_node(state: EmailState, llm) -> dict:
    email = state["email"]
    system = SystemMessage(content=(
        "Draft a short, friendly reply to this email for a human to review and send, "
        "don't send it yourself. Keep it to 2-4 sentences, acknowledge the email and "
        "suggest a next step, don't make commitments on behalf of the business."
    ))
    human = HumanMessage(content=f"Subject: {email['subject']}\nBody: {email['body']}")
    response = llm.invoke([system, human])
    return {"action": "Draft created, awaiting human review before sending.", "draft": response.text}


def spam_node(state: EmailState) -> dict:
    return {"action": "Marked as spam, archived, no reply needed.", "draft": None}


def route_after_classify(state: EmailState) -> Literal["routine", "urgent", "needs_human", "spam"]:
    return state["category"]


def build_graph(model: str | None = None, llm=None):
    llm = llm or get_llm(model)

    graph = StateGraph(EmailState)
    graph.add_node("classify", lambda state: classify_node(state, llm))
    graph.add_node("routine", routine_node)
    graph.add_node("urgent", urgent_node)
    graph.add_node("needs_human", lambda state: needs_human_node(state, llm))
    graph.add_node("spam", spam_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route_after_classify)
    graph.add_edge("routine", END)
    graph.add_edge("urgent", END)
    graph.add_edge("needs_human", END)
    graph.add_edge("spam", END)

    return graph.compile()


_graph = None


def triage_email(email: dict, model: str | None = None) -> dict:
    # Build the graph once and reuse it for every email in the batch.
    global _graph
    if _graph is None or model:
        _graph = build_graph(model)
    return _graph.invoke({"email": email})
