<div align="center">

<h1>Email Triage Agent</h1>

<p><b>Sorts an inbox into routine, urgent, needs-a-human and spam, and gives each one a different level of autonomy. Nothing is sent without a person.</b></p>

<p>
  <a href="https://github.com/saqib-n/email-triage-agent/actions/workflows/tests.yml"><img src="https://github.com/saqib-n/email-triage-agent/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python: 3.12+">
  <img src="https://img.shields.io/badge/LangGraph-1.x-1C3C3C" alt="LangGraph: 1.x">
  <img src="https://img.shields.io/badge/alerts-Slack-4A154B?logo=slack&logoColor=white" alt="alerts: Slack">
  <img src="https://img.shields.io/badge/models-OpenAI%20%7C%20Claude%20%7C%20Gemini-444444" alt="models: OpenAI | Claude | Gemini">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2E7D32" alt="license: MIT"></a>
</p>

<p>
  <a href="#what-it-does">What it does</a> &nbsp;|&nbsp;
  <a href="#how-it-works">How it works</a> &nbsp;|&nbsp;
  <a href="#sample-run">Sample run</a> &nbsp;|&nbsp;
  <a href="#quick-start">Quick start</a> &nbsp;|&nbsp;
  <a href="#configuration">Configuration</a> &nbsp;|&nbsp;
  <a href="#roadmap">Roadmap</a>
</p>

</div>

<br>

<h2>See it in action</h2>

<p align="center"><img src="demo/demo.gif" alt="Inbox screen: the agent sorts each email into a folder and shows why, what it did and the drafted reply" width="100%"></p>

<p align="center"><sub>Recorded in the built-in inbox from a real run on Google Gemini (<code>gemini-3.5-flash-lite</code>) on 14 November 2026. Nothing is scripted. Only the time spent waiting for the model is fast-forwarded, and the real response times are shown on screen. <a href="demo/demo.mp4">Download the MP4</a>.</sub></p>

<p>Run <code>python app.py</code> and it opens an inbox where the agent sorts every email into a folder, with its reason, the action it took and any drafted reply. It is the same agent code as the command line version, with a screen on top.</p>

<h2>The problem</h2>

<p>A shared inbox mixes questions answered a hundred times before, messages that need a careful human reply, the occasional legal or angry email that needs attention today, and a lot of noise.</p>

<p>Treating all of these the same way is the mistake. An autoresponder that confidently answers a legal threat does more damage than having no automation at all.</p>

<h2>What it does</h2>

<table>
  <tr><th align="left">Capability</th><th align="left">What that means in practice</th></tr>
  <tr><td><b>Routine</b></td><td>Common questions are matched to the FAQ and the agent drafts a complete reply from it, not from memory.</td></tr>
  <tr><td><b>Urgent</b></td><td>Legal threats, cancellations and angry customers get no draft at all. The agent flags them and sends a Slack alert so a person sees them right away.</td></tr>
  <tr><td><b>Needs a human</b></td><td>Partnership and sales conversations get a short, non-committal draft for a person to edit and send.</td></tr>
  <tr><td><b>Spam</b></td><td>Marked and archived.</td></tr>
  <tr><td><b>A reason for every decision</b></td><td>Each email is logged with its category and a one-line reason, so you can check the agent's judgement over time.</td></tr>
  <tr><td><b>Full audit log</b></td><td>Every email, decision and draft is written to <code>output/triage_log.csv</code>.</td></tr>
</table>

<h2>How it works</h2>

<pre>
email --&gt; classify --+--&gt; routine      --&gt; FAQ lookup --&gt; drafted reply
                     +--&gt; urgent       --&gt; flag + Slack alert, no reply
                     +--&gt; needs_human  --&gt; short draft for a person
                     +--&gt; spam         --&gt; archive
</pre>

<p>A LangGraph pipeline classifies each email with structured output (category and reason), then routes it to the handler for that category. Drafts are returned and logged. The function is called <code>draft_reply</code> on purpose, so nobody reading a log thinks mail went out.</p>

<p>This version reads from <code>data/inbox.json</code>. The triage logic doesn't change when it is connected to a real Gmail or Outlook inbox. Only the reading and sending layer does.</p>

<h2>Decisions I made on purpose</h2>

<h3>Autonomy is earned</h3>

<p>Most businesses aren't ready to let software send mail under their name on day one, and they shouldn't be. What they are ready for is something that drafts well and flags correctly, so they can watch it for a few weeks. Auto-sending can come later, starting with the narrowest category.</p>

<h3>Urgent mail gets no AI draft</h3>

<p>Being wrong on a legal or angry email is expensive, and the agent shouldn't be the one deciding what to say. Its job there is to make sure a person sees it fast.</p>

<h2>Sample run</h2>

<pre>
$ python process_inbox.py
[ROUTINE] What are your business hours? (from priya@customerco.com)
  Reason: Common question with a direct, standard answer available.
  Action: Answer found in FAQ. Drafted reply to priya@customerco.com

[URGENT] Cease and desist notice regarding trademark usage (from legal@somefirm.com)
  Reason: Legal threat requiring immediate human attention.
  Action: Flagged URGENT, needs a human today, no auto-reply sent.

[SPAM] You have WON a prize!!! Claim NOW (from winbig@totally-not-spam.biz)
  Reason: Promotional spam with urgency bait, not a real inquiry.
  Action: Marked as spam, archived, no reply needed.

Summary: {'routine': 2, 'urgent': 2, 'needs_human': 1, 'spam': 1}
</pre>

<h2>Quick start</h2>

<p>You need Python 3.12 or newer and an API key from OpenAI, Anthropic or Google Gemini.</p>

<pre>
pip install -r requirements.txt
cp .env.example .env        # on Windows: copy .env.example .env
# open .env and paste your API key
python app.py               # opens the inbox at http://localhost:8000
python process_inbox.py
</pre>

<h2>Configuration</h2>

<p>Everything is set in <code>.env</code>. Copy <code>.env.example</code> to start.</p>

<table>
  <tr><th align="left">Variable</th><th align="left">Required</th><th align="left">Purpose</th></tr>
  <tr><td><code>LLM_MODEL</code></td><td>Yes</td><td>Which model to use, as <code>provider:model</code>. Default <code>openai:gpt-5.5</code>. Also works with <code>anthropic:claude-opus-5-5</code> or <code>google_genai:gemini-3.5-flash</code>.</td></tr>
  <tr><td><code>OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY</code></td><td>One of them</td><td>The key for whichever provider you picked.</td></tr>
  <tr><td><code>SLACK_WEBHOOK_URL</code></td><td>No</td><td>Sends a Slack alert for every urgent email.</td></tr>
</table>

<h2>Project structure</h2>

<pre>
email-triage-agent/
  .env.example        # copy to .env and add your key
  case_study.md       # longer write-up of the design
  process_inbox.py    # triages the whole inbox and writes the log
  app.py            # browser inbox, the same agent with a UI
  README.md
  requirements.txt    # dependencies
  agent/
    llm.py            # picks the model from LLM_MODEL
    tools.py          # FAQ lookup, draft and Slack alert
    triage.py         # the classify and route pipeline
  data/
    faq.json          # answers the routine bucket draws from
    inbox.json        # sample inbox
  demo/               # recording of a live run (GIF, MP4 and a screenshot)
  tests/              # pytest suite, runs without any API key
  web/
    index.html          # the inbox, one file, no build step
</pre>

<h2>Built with</h2>

<p>Python &nbsp;&middot;&nbsp; LangGraph &nbsp;&middot;&nbsp; LangChain &nbsp;&middot;&nbsp; Pydantic &nbsp;&middot;&nbsp; Slack &nbsp;&middot;&nbsp; OpenAI / Anthropic / Gemini</p>

<h2>Tests</h2>

<pre>
pip install -r requirements-dev.txt
pytest
</pre>

<p>Five tests cover the FAQ matching, what each of the four buckets does, the optional Slack alert and the full pipeline with a stand-in model, plus the browser screen and its API. None of the tests call a model or need an API key, so they run on GitHub Actions on every push. The badge at the top shows the latest result.</p>

<h2>Roadmap</h2>

<p>What I would build next if a client took this into production:</p>
<ul>
  <li>Read and draft directly in Gmail or Outlook, with drafts saved in the mailbox for one-click sending</li>
  <li>A hard rules layer above the model: certain senders, refund requests and legal language always go to urgent</li>
  <li>Auto-send for the routine bucket only, once the classification has a proven track record</li>
</ul>

<h2>More from this series</h2>

<p>Nine production-minded AI agents, each solving one business problem properly.</p>

<table>
  <tr><td><a href="https://github.com/saqib-n/ai-research-report-agent"><b>Research Report Agent</b></a></td><td>Researches a topic, notices its own gaps, and writes a report with a source for every claim.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/ai-sales-outreach-agent"><b>AI Sales Outreach Agent</b></a></td><td>Personalised cold emails and follow-ups, with a human approving every send.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/ecommerce-automation-agent"><b>E-commerce Order and Inventory Agent</b></a></td><td>Shopify order, stock and returns assistant, plus a monitor that warns you before stock runs out.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/lead-qualification-crm-agent"><b>Lead Qualification Agent</b></a></td><td>Scores inbound leads against your own rubric and pushes the good ones to HubSpot.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/multi-agent-customer-support"><b>Multi-Agent Customer Support</b></a></td><td>A router plus specialist agents for orders, refunds, FAQs and human handoff.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/rag-knowledge-base-agent"><b>RAG Knowledge Base Agent</b></a></td><td>Answers questions from your own documents and names the source for every answer.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/recruiting-screening-agent"><b>Resume Screening Agent</b></a></td><td>Ranks resumes against a job description with evidence, and guards against common bias.</td></tr>
  <tr><td><a href="https://github.com/saqib-n/whatsapp-support-agent"><b>WhatsApp Support Agent</b></a></td><td>A WhatsApp Cloud API agent that checks orders, answers FAQs and escalates to a person.</td></tr>
</table>

<h2>Work with me</h2>

<p>I'm Saqib Nawaz, founder of WolfXense AI. I build AI agents and automations for businesses, with Python, LangChain, LangGraph and n8n, and connect them to the tools teams already use, like CRMs, Shopify, Slack, email and WhatsApp.</p>

<p>If your team loses hours every day sorting a shared inbox, I can connect this to your mailbox and your own FAQ and set the rules for what gets flagged.</p>

<p><a href="https://www.upwork.com/freelancers/~01de008504a38baf28"><b>Hire me on Upwork</b></a> &nbsp;|&nbsp; <a href="https://github.com/saqib-n"><b>More of my work on GitHub</b></a></p>

<hr>

<p><sub>Released under the <a href="LICENSE">MIT License</a>. A longer write-up of the design is in <a href="case_study.md">case_study.md</a>.</sub></p>
