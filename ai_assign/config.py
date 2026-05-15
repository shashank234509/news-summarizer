"""
Configuration for the Newsletter Agent.
"""

# ── Ollama / Mistral Settings ──────────────────────────────────────────
OLLAMA_MODEL = "mistral"
OLLAMA_HOST  = "http://localhost:11434"
API_KEY      = "39b7eb569b78442bb56ba8d56521ff25.6QW-plRzdiJwjLdNlMKz6ww_"

# ── Agent Settings ─────────────────────────────────────────────────────
MAX_ARTICLES       = 7          # top N articles to include
MIN_ARTICLES       = 5          # minimum articles
MAX_CRITIQUE_LOOPS = 2          # how many self-reflection passes
SEARCH_QUERIES     = [
    "latest AI agent news 2025",
    "autonomous AI agents developments",
    "AI agent frameworks updates",
]

# ── Output Settings ────────────────────────────────────────────────────
OUTPUT_DIR = "output"

# ── Memory / Archive Settings ──────────────────────────────────────────
MEMORY_DIR = "memory"         # persistent storage for news archive
