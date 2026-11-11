# Email Triage Agent

## Portfolio entry

Sorts an inbox into routine, urgent, needs-human and spam, and gives each category a different level of autonomy rather than treating every message the same. Routine questions get a reply drafted from the FAQ, urgent mail gets flagged with a Slack alert and no generated response, everything in between gets a draft a person reviews. Nothing sends. Built as a LangGraph classify-and-route pipeline with structured output.

**Stack:** Python, LangGraph, Pydantic, Slack

---

## The obvious version of this is wrong

Classify the email, auto-reply to anything the model feels confident about. It demos well and it's a bad idea, because model confidence and correctness aren't the same thing, and the failure lands in a stranger's inbox with your client's name on it.

The useful question isn't "can it classify email". It's "how much should it be allowed to do about each kind".

## Four buckets, four levels of autonomy

**Routine** is the only category where the agent produces a full answer, and even there it's copying from a fixed FAQ rather than writing something new. Bounded and checkable.

**Urgent** gets the least autonomy of all. Legal language, an angry customer, a cancellation threat, the agent flags it, alerts Slack and writes nothing. Being wrong on this category is the expensive case, and a generated response is a liability rather than a help.

**Needs human** produces a short, non-committal draft. Judgment required, but nothing's on fire.

**Spam** gets filed.

Sorting the mail is the easy part. Deciding what the system is allowed to do about each pile is the actual design work.

## Nothing sends, and that's stated plainly

There's no Gmail integration in this version. It reads a local inbox file and replies are drafted and returned, never delivered anywhere. The function is named `draft_reply` rather than `send_reply` specifically so nobody reading a log line assumes mail went out.

I mention this because an earlier version of this code had a stub that returned "Sent reply to..." while doing nothing. That's a worse bug than a missing feature, code that reports success it didn't achieve. It's gone.

The Slack alert is real, if a webhook URL is set it fires.

## How I'd pitch this to a client

Most businesses aren't ready to let software send mail under their name, and they're right not to be. What they are ready for is something that drafts well and flags correctly, so they can watch it for a few weeks and judge whether the classification holds up on their actual mail.

Auto-sending is a permission a system earns, starting with the narrowest, most predictable category. Building the graduated version first, rather than an on/off switch, is what makes it adoptable.

## What comes next

Real Gmail read and send, which is a Google Cloud project and an OAuth consent screen.

But before that, a rules layer above the classifier. Certain sender domains, anything mentioning a refund, anything with legal phrasing, should route to urgent regardless of what the model decides. Model judgment is good enough for ordinary mail and not good enough for the mail that matters most, and the fix is boring, deterministic rules on top.

## My part

The four-category design and the autonomy level attached to each, the LangGraph pipeline, and the honest-by-default handling of anything that leaves the machine.
