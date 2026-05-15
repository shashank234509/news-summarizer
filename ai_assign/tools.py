"""
Tools available to the Newsletter Agent.

Each tool is a callable that the agent's executor can invoke.
Tools implemented:
    1. web_search_tool   – Search the web via DuckDuckGo
    2. summarize_tool    – Summarise a list of articles using the LLM
    3. html_generator    – Render a newsletter as styled HTML
"""

import os, json, datetime, textwrap
from typing import List, Dict

try:
    from ddgs import DDGS                       # new package name (pip install ddgs)
except ImportError:
    from duckduckgo_search import DDGS           # legacy fallback

from jinja2 import Template
import ollama

import config

# ═══════════════════════════════════════════════════════════════════════
# Tool 1 – Web Search (DuckDuckGo)
# ═══════════════════════════════════════════════════════════════════════

# Fallback sample articles used when live search returns nothing
_FALLBACK_ARTICLES = [
    {
        "title": "OpenAI Launches GPT-5 With Autonomous Agent Capabilities",
        "href": "https://openai.com/blog/gpt5-agents",
        "body": "OpenAI has unveiled GPT-5, featuring built-in agent capabilities that allow the model to browse the web, write and execute code, and manage multi-step tasks autonomously.",
    },
    {
        "title": "Google DeepMind Introduces Gemini Agent Framework",
        "href": "https://deepmind.google/discover/blog/gemini-agents",
        "body": "Google DeepMind released a new agent framework built on top of Gemini, enabling developers to create autonomous AI agents that can reason, plan, and use tools.",
    },
    {
        "title": "LangChain Releases LangGraph 2.0 for Stateful Agent Workflows",
        "href": "https://blog.langchain.dev/langgraph-2",
        "body": "LangGraph 2.0 introduces persistent state management and human-in-the-loop controls, making it easier to build production-grade AI agent pipelines.",
    },
    {
        "title": "Microsoft AutoGen Enables Multi-Agent Collaboration at Scale",
        "href": "https://www.microsoft.com/research/blog/autogen",
        "body": "Microsoft Research's AutoGen framework now supports scalable multi-agent collaboration, allowing teams of AI agents to solve complex tasks together.",
    },
    {
        "title": "CrewAI Raises $18M to Advance AI Agent Orchestration",
        "href": "https://techcrunch.com/crewai-funding",
        "body": "AI agent orchestration startup CrewAI has raised $18 million in Series A funding to expand its platform for building and managing teams of autonomous AI agents.",
    },
    {
        "title": "Anthropic Publishes Research on Safe Autonomous AI Agents",
        "href": "https://www.anthropic.com/research/safe-agents",
        "body": "Anthropic released a detailed research paper outlining new techniques for ensuring AI agent safety, including constitutional AI constraints and real-time monitoring.",
    },
    {
        "title": "Hugging Face Launches Open-Source Agent Toolkit SmolAgents",
        "href": "https://huggingface.co/blog/smolagents",
        "body": "Hugging Face announced SmolAgents, a lightweight open-source toolkit that lets developers build AI agents using any model on the Hub with minimal boilerplate code.",
    },
]


def web_search_tool(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search the web for *query* and return a list of result dicts.
    Each dict has keys: title, href, body.
    Falls back to curated sample articles when live search returns nothing.
    """
    print(f"  🔍  Searching: {query!r}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if results:
            print(f"  ✅  Found {len(results)} results")
            return results
        print("  ⚠️  Search returned 0 results — using fallback articles")
        return _FALLBACK_ARTICLES
    except Exception as e:
        print(f"  ⚠️  Search failed ({e}) — using fallback articles")
        return _FALLBACK_ARTICLES


# ═══════════════════════════════════════════════════════════════════════
# Tool 2 – LLM Summariser
# ═══════════════════════════════════════════════════════════════════════

def summarize_tool(articles: List[Dict]) -> str:
    """
    Given raw article dicts (title, href, body), ask the LLM to produce
    concise summaries suitable for a newsletter.
    """
    print(f"  📝  Summarising {len(articles)} articles …")

    bullet_list = "\n".join(
        f"- **{a.get('title','')}** ({a.get('href','')})\n  {a.get('body','')}"
        for a in articles
    )

    prompt = textwrap.dedent(f"""\
    You are a professional newsletter editor.
    Below are raw search results about AI agents. For each article,
    write a 2-3 sentence summary that is engaging and informative.
    Keep the original title and URL.
    Return your answer as a JSON array of objects with keys:
    "title", "url", "summary".

    Articles:
    {bullet_list}
    """)

    try:
        resp = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["message"]["content"]
    except Exception as e:
        print(f"  ⚠️  Summarisation failed: {e}")
        return json.dumps([
            {"title": a.get("title",""), "url": a.get("href",""),
             "summary": a.get("body","")}
            for a in articles
        ])


# ═══════════════════════════════════════════════════════════════════════
# Tool 3 – HTML Newsletter Generator
# ═══════════════════════════════════════════════════════════════════════

_HTML_TEMPLATE = Template(textwrap.dedent("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ subject }}</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f8;
         margin: 0; padding: 0; }
  .container { max-width: 640px; margin: 30px auto; background: #fff;
               border-radius: 12px; overflow: hidden;
               box-shadow: 0 4px 24px rgba(0,0,0,.08); }
  .header { background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: #fff; padding: 36px 32px; }
  .header h1 { margin: 0 0 6px; font-size: 26px; }
  .header p  { margin: 0; opacity: .85; font-size: 14px; }
  .body { padding: 28px 32px; }
  .article { margin-bottom: 24px; padding-bottom: 20px;
             border-bottom: 1px solid #eee; }
  .article:last-child { border-bottom: none; }
  .article h2 { font-size: 18px; margin: 0 0 6px; }
  .article h2 a { color: #4f46e5; text-decoration: none; }
  .article h2 a:hover { text-decoration: underline; }
  .article p { color: #555; font-size: 14px; line-height: 1.6; margin: 0; }
  .footer { background: #fafafa; text-align: center; padding: 20px 32px;
            font-size: 12px; color: #999; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{{ subject }}</h1>
    <p>{{ date }} &mdash; Your weekly dose of AI agent news</p>
  </div>
  <div class="body">
    {% for a in articles %}
    <div class="article">
      <h2><a href="{{ a.url }}">{{ a.title }}</a></h2>
      <p>{{ a.summary }}</p>
    </div>
    {% endfor %}
  </div>
  <div class="footer">
    You received this because you subscribed to the AI Agent Newsletter.<br>
    &copy; {{ year }} Newsletter Agent &bull; <a href="#">Unsubscribe</a>
  </div>
</div>
</body>
</html>
"""))


def html_generator_tool(subject: str, articles: List[Dict]) -> str:
    """
    Render a styled HTML newsletter from structured article data.
    Returns the HTML string and also saves it to the output dir.
    """
    print("  🎨  Generating HTML newsletter …")
    now = datetime.datetime.now()
    html = _HTML_TEMPLATE.render(
        subject=subject,
        date=now.strftime("%B %d, %Y"),
        year=now.year,
        articles=articles,
    )

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    path = os.path.join(config.OUTPUT_DIR, "newsletter.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"  💾  Saved to {path}")
    return html


# ═══════════════════════════════════════════════════════════════════════
# Tool 4 – Simulated Email Sender
# ═══════════════════════════════════════════════════════════════════════

def send_email_tool(
    subject: str,
    articles: List[Dict],
    recipients: str = "subscribers@example.com",
    sender: str = "newsletter-agent@example.com",
) -> str:
    """
    Simulate sending the newsletter via email.
    Saves a complete email file (headers + plain-text body) to the output
    directory and prints the full email content to the console.
    Returns the path to the saved email file.
    """
    now = datetime.datetime.now()
    date_str = now.strftime("%B %d, %Y")
    timestamp = now.strftime("%a, %d %b %Y %H:%M:%S %z") or now.strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Build plain-text body from article summaries
    body_lines = [f"{'=' * 60}", f"  {subject}", f"  {date_str}", f"{'=' * 60}", ""]
    for i, a in enumerate(articles, 1):
        body_lines.append(f"  {i}. {a.get('title', 'Untitled')}")
        body_lines.append(f"     🔗 {a.get('url', 'N/A')}")
        body_lines.append(f"     {a.get('summary', '')}")
        body_lines.append("")
    body_lines.append(f"{'─' * 60}")
    body_lines.append("You received this because you subscribed to the AI Agent Newsletter.")
    body_lines.append("To unsubscribe, reply with 'UNSUBSCRIBE'.")
    body_lines.append(f"{'─' * 60}")
    body_text = "\n".join(body_lines)

    # Compose full email with headers
    email_content = (
        f"From:    {sender}\n"
        f"To:      {recipients}\n"
        f"Date:    {timestamp}\n"
        f"Subject: {subject}\n"
        f"Content-Type: text/plain; charset=UTF-8\n"
        f"\n{body_text}\n"
    )

    # Save to file
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    email_path = os.path.join(config.OUTPUT_DIR, "email_simulation.txt")
    with open(email_path, "w") as f:
        f.write(email_content)

    # Print to console
    print("\n" + "─" * 60)
    print("📧  SIMULATED EMAIL SEND")
    print("─" * 60)
    print(email_content)
    print(f"  💾  Email saved to {email_path}")
    print(f"  Status:  ✅ Sent successfully (simulated)")
    print("─" * 60)

    return email_path
