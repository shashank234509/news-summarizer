# news-summarizer


# 🤖 Newsletter Agent

An autonomous AI agent that researches, summarises, and generates a professional newsletter — powered by **Ollama + Mistral**. Features persistent memory to prevent duplicate articles across runs.

## Architecture

```
run_newsletter_agent(goal)
        │
        ▼
┌──────────────┐
│  1. PLAN     │  LLM breaks goal into sub-tasks
└──────┬───────┘
       ▼
┌──────────────┐
│  2. RESEARCH │  Tool: DuckDuckGo web search
│              │  🧠 Memory: deduplicate against archive
└──────┬───────┘
       ▼
┌──────────────┐
│  3. SUMMARISE│  Tool: LLM-based summariser
└──────┬───────┘
       ▼
┌──────────────┐
│  4. CRITIQUE │  Self-reflection & improvement loop
└──────┬───────┘
       ▼
┌──────────────┐
│  5. OUTPUT   │  Tool: HTML/Markdown generator + simulated email send
│              │  🧠 Memory: archive new articles for next run
└──────────────┘
```

## Tools Used

| # | Tool | Purpose |
|---|------|---------|
| 1 | `web_search_tool` | Search the web via DuckDuckGo |
| 2 | `summarize_tool` | LLM-powered article summarisation |
| 3 | `html_generator_tool` | Jinja2-based styled HTML newsletter |
| 4 | `send_email_tool` | Simulated email sender (saves email file + prints to console) |

## 🧠 Memory & Deduplication

The agent maintains a **persistent archive** at `memory/news_archive.json`. Each time it runs:

1. **Before summarising** — the agent checks every researched article against the archive
2. **Duplicate detection** — matches by exact URL **or** fuzzy title similarity (≥ 80%)
3. **Skips duplicates** — previously covered articles are filtered out with a log message
4. **After output** — new articles are appended to the archive with their `covered_date`

```
# Example: run the agent twice
python agent.py --mode auto          # 1st run: 7 articles → all new
python agent.py --mode auto          # 2nd run: same 7 skipped as duplicates!
```

Archive schema (`memory/news_archive.json`):
```json
[
  {
    "title": "OpenAI Launches GPT-5 ...",
    "url": "https://openai.com/blog/gpt5-agents",
    "summary": "OpenAI has unveiled GPT-5 ...",
    "covered_date": "2025-05-14"
  }
]
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Make sure Ollama is running with Mistral
ollama pull mistral

# 3. Start the Web UI (Recommended)
uvicorn app:app --port 8000
# Then open http://localhost:8000 in your browser

# 4. Or run via CLI in autonomous mode
python agent.py --mode auto

# 5. Or run via CLI in human-in-the-loop mode
python agent.py --mode hitl

# 6. Custom CLI goal
python agent.py --goal "Create a newsletter about LLM breakthroughs"
```

## Modes

- **`auto`** — Fully autonomous. One call does everything.
- **`hitl`** — Human-in-the-loop. Pauses after each phase for your approval (press Enter to continue, `q` to quit).

## Output

After running, check the generated files:

| File | Description |
|------|-------------|
| `output/newsletter.html` | Styled HTML email |
| `output/newsletter.md` | Markdown version |
| `output/email_simulation.txt` | Simulated email with headers + plain-text body |
| `memory/news_archive.json` | Persistent archive of all covered articles |

## Project Structure

```
├── app.py            # FastAPI Web Server
├── static/           # Web UI Frontend (HTML, CSS, JS)
├── agent.py          # Core agent pipeline (5 phases)
├── tools.py          # Tool implementations (search, summarise, HTML, email)
├── memory.py         # Persistent memory & duplicate detection
├── config.py         # Configuration (model, search queries, limits)
├── requirements.txt  # Dependencies
├── output/           # Generated newsletters + simulated email
└── memory/           # Persistent news archive (auto-created)
```
