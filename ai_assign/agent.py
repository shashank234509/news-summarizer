"""
Newsletter Agent – autonomous multi-step agent.

Pipeline:  Plan → Research → Summarise → Draft → Self-Critique → Output

Usage:
    from agent import run_newsletter_agent
    run_newsletter_agent("Create a weekly newsletter on latest AI agent news …")

Modes:
    autonomous=True   →  runs end-to-end without pausing
    autonomous=False  →  pauses after each phase for human approval
"""

import json, os, datetime, textwrap
from typing import List, Dict

import ollama
import config
from tools import web_search_tool, summarize_tool, html_generator_tool, send_email_tool
from memory import deduplicate_articles, archive_articles

# ── Helpers ────────────────────────────────────────────────────────────

def _llm(prompt: str) -> str:
    """Send a single-turn prompt to the Ollama Mistral model."""
    resp = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp["message"]["content"]


def _pause(phase: str, autonomous: bool):
    """In human-in-the-loop mode, pause and wait for approval."""
    if autonomous:
        return
    print(f"\n⏸  Phase '{phase}' complete. Press Enter to continue or 'q' to quit: ", end="")
    ans = input()
    if ans.strip().lower() == "q":
        print("🛑  Agent stopped by user.")
        raise SystemExit(0)


def _parse_json_from_llm(text: str) -> List[Dict]:
    """Best-effort extraction of a JSON array from LLM output."""
    # Find the first '[' and last ']'
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    # Fallback: return empty
    return []


# ── Agent Phases ───────────────────────────────────────────────────────

def phase_plan(goal: str) -> Dict:
    """Phase 1 – Plan: break the goal into sub-tasks."""
    print("\n" + "═" * 60)
    print("📋  PHASE 1 / 5 — PLANNING")
    print("═" * 60)

    prompt = textwrap.dedent(f"""\
    You are an AI planning agent. Given the following goal, produce a
    concise step-by-step plan in JSON with keys "steps" (a list of
    short action strings).

    Goal: {goal}
    """)
    raw = _llm(prompt)
    print(f"  Plan output:\n{raw}\n")

    steps = _parse_json_from_llm(raw)
    if not steps:
        # fallback plan
        steps = [
            {"step": "Search for latest AI agent news"},
            {"step": "Select top 5-7 most relevant articles"},
            {"step": "Summarise each article"},
            {"step": "Generate HTML newsletter"},
            {"step": "Review and critique the newsletter"},
            {"step": "Save / send the newsletter"},
        ]
    return {"goal": goal, "plan": steps}


def phase_research() -> List[Dict]:
    """Phase 2 – Research: search the web for articles."""
    print("\n" + "═" * 60)
    print("🔎  PHASE 2 / 5 — RESEARCH")
    print("═" * 60)

    all_results: List[Dict] = []
    seen_urls = set()

    for q in config.SEARCH_QUERIES:
        results = web_search_tool(q, max_results=5)
        for r in results:
            url = r.get("href", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    print(f"\n  📰  Collected {len(all_results)} unique articles")

    # ── Memory: filter out previously covered articles ──
    print("\n  🧠  Checking memory for duplicates …")
    all_results = deduplicate_articles(all_results)

    # Trim to max
    all_results = all_results[: config.MAX_ARTICLES]
    print(f"  📰  Final count: {len(all_results)} articles after dedup")
    return all_results


def phase_summarise(articles: List[Dict]) -> List[Dict]:
    """Phase 3 – Summarise: produce concise summaries via LLM."""
    print("\n" + "═" * 60)
    print("✍️   PHASE 3 / 5 — SUMMARISING")
    print("═" * 60)

    raw = summarize_tool(articles)
    parsed = _parse_json_from_llm(raw)

    if not parsed:
        # Fallback: use raw bodies
        parsed = [
            {"title": a.get("title", ""), "url": a.get("href", ""),
             "summary": a.get("body", "")}
            for a in articles
        ]

    print(f"  ✅  {len(parsed)} article summaries ready")
    return parsed


def phase_critique(articles: List[Dict]) -> List[Dict]:
    """Phase 4 – Self-Critique: LLM evaluates and improves summaries."""
    print("\n" + "═" * 60)
    print("🔍  PHASE 4 / 5 — SELF-CRITIQUE & REFINEMENT")
    print("═" * 60)

    for iteration in range(1, config.MAX_CRITIQUE_LOOPS + 1):
        print(f"\n  🔄  Critique iteration {iteration}/{config.MAX_CRITIQUE_LOOPS}")

        articles_json = json.dumps(articles, indent=2)
        prompt = textwrap.dedent(f"""\
        You are a senior newsletter editor reviewing article summaries.
        Evaluate the following summaries for:
        1. Clarity and engagement
        2. Accuracy and informativeness
        3. Consistent tone and length

        First, provide a brief critique. Then return an IMPROVED version
        as a JSON array with the same keys: "title", "url", "summary".

        Summaries:
        {articles_json}
        """)

        raw = _llm(prompt)
        print(f"  Critique output (first 300 chars):\n  {raw[:300]}…\n")

        improved = _parse_json_from_llm(raw)
        if improved and len(improved) >= len(articles):
            articles = improved[: len(articles)]
            print(f"  ✅  Improved {len(articles)} summaries")
        else:
            print("  ℹ️  Keeping previous version (critique produced no valid JSON)")

    return articles


def phase_output(articles: List[Dict], goal: str) -> str:
    """Phase 5 – Output: generate HTML, save, and simulate sending."""
    print("\n" + "═" * 60)
    print("📤  PHASE 5 / 5 — GENERATING & SENDING")
    print("═" * 60)

    subject = "🤖 Weekly AI Agent Digest"
    html = html_generator_tool(subject, articles)

    # Also save a Markdown version
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    md_path = os.path.join(config.OUTPUT_DIR, "newsletter.md")
    with open(md_path, "w") as f:
        f.write(f"# {subject}\n\n")
        f.write(f"*{datetime.datetime.now().strftime('%B %d, %Y')}*\n\n")
        for a in articles:
            f.write(f"## {a.get('title','Untitled')}\n")
            f.write(f"🔗 {a.get('url','')}\n\n")
            f.write(f"{a.get('summary','')}\n\n---\n\n")
    print(f"  💾  Markdown saved to {md_path}")

    # Simulate email sending (saves to file + prints to console)
    send_email_tool(subject, articles)

    # ── Memory: archive articles so they won't repeat next run ──
    print("\n  🧠  Saving to memory archive …")
    archive_articles(articles)

    return html


# ── Main Entry Point ──────────────────────────────────────────────────

def run_newsletter_agent(goal: str, autonomous: bool = True):
    """
    Execute the full newsletter agent pipeline.

    Args:
        goal:       Plain-English description of what to produce.
        autonomous: True  = fully autonomous (no pauses)
                    False = human-in-the-loop (pauses after each phase)
    """
    mode = "🤖 FULLY AUTONOMOUS" if autonomous else "🧑‍💻 HUMAN-IN-THE-LOOP"
    print("\n" + "╔" + "═" * 58 + "╗")
    print(f"║  NEWSLETTER AGENT — {mode:^36} ║")
    print("╚" + "═" * 58 + "╝")
    print(f"\n  Goal: {goal}\n")

    # Phase 1 – Plan
    plan = phase_plan(goal)
    _pause("Planning", autonomous)

    # Phase 2 – Research
    articles_raw = phase_research()
    if not articles_raw:
        print("❌  No articles found. Aborting.")
        return
    _pause("Research", autonomous)

    # Phase 3 – Summarise
    articles = phase_summarise(articles_raw)
    _pause("Summarisation", autonomous)

    # Phase 4 – Self-Critique
    articles = phase_critique(articles)
    _pause("Critique", autonomous)

    # Phase 5 – Output
    html = phase_output(articles, goal)
    _pause("Output", autonomous)

    print("\n✅  Newsletter Agent finished successfully!\n")
    return html


# ── CLI Entry ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Newsletter Agent")
    parser.add_argument(
        "--goal",
        default="Create a weekly newsletter on latest AI agent news and send it to our subscribers.",
        help="Plain-English goal for the agent",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "hitl"],
        default="auto",
        help="auto = fully autonomous, hitl = human-in-the-loop",
    )
    args = parser.parse_args()

    run_newsletter_agent(goal=args.goal, autonomous=(args.mode == "auto"))
