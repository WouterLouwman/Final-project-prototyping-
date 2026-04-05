import os
import streamlit as st
import re
import datetime
import json
from html import escape
from typing import Any, Dict, List, Optional

from openai import OpenAI
import streamlit.components.v1 as components

st.set_page_config(
    page_title="TimeTravel · Editorial AI",
    page_icon="🕰️",
    layout="wide"
)

CURRENT_YEAR = datetime.datetime.now().year

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = None

client = OpenAI(api_key=api_key)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
RESEARCH_MODEL = "gpt-4o-mini"
CHAT_MODEL = "gpt-4o-mini"
MAX_SOURCE_COUNT = 3
MIN_ACCEPT_CONFIDENCE = 0.70
RESEARCH_CONFIDENCE_RETRY_THRESHOLD = 0.65

PREFERRED_SOURCE_HINT = (
    "Prefer Reuters, AP, BBC, FT, official government/statistics sources, major company filings, "
    "or primary institutional sources when relevant. Avoid low-quality aggregators, SEO spam, and opinion blogs."
)

# --------------------------------------------------
# STYLING
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Base ─────────────────────────────────────── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #F5F1E8; color: #1C1C1C; }
    .block-container { max-width: 860px; padding-top: 0; padding-bottom: 5rem; }

    /* ── Topbar ───────────────────────────────────── */
    .topbar {
        background: #1C1C1C;
        padding: 0.85rem 2rem;
        display: flex; align-items: center; justify-content: space-between;
        margin: -4rem -4rem 3rem -4rem;
        border-bottom: 1px solid #2E2E2E;
    }
    .topbar-logo {
        font-family: 'Playfair Display', serif;
        font-size: 1.3rem; font-weight: 700; color: #F5F1E8;
        letter-spacing: 0.01em;
    }
    .topbar-logo span { color: #C9A84C; }
    .topbar-tag {
        font-size: 0.65rem; font-weight: 400;
        color: rgba(245,241,232,0.35);
        letter-spacing: 0.06em; font-style: italic;
    }

    /* ── Page header — pure typography, no box ────── */
    .page-header { margin-bottom: 2.5rem; padding-bottom: 1.75rem; border-bottom: 1px solid #DDD8CE; }
    .page-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.6rem; font-weight: 700;
        color: #1C1C1C; margin-bottom: 0.5rem; line-height: 1.15;
    }
    .page-sub { font-size: 0.88rem; color: #7A766E; line-height: 1.7; }

    /* ── Section label — sentence case, quiet ─────── */
    .slabel {
        font-size: 0.73rem; font-weight: 500;
        color: #A8A49C; margin-bottom: 0.5rem;
        letter-spacing: 0.02em;
        display: flex; align-items: center; gap: 0.35rem;
    }
    .slabel-dot { width: 5px; height: 5px; background: #C9A84C; border-radius: 50%; display: inline-block; }

    /* ── Cards — minimal, no heavy boxes ─────────── */
    .card {
        background: transparent; border: none; border-radius: 0;
        padding: 0; box-shadow: none; margin-bottom: 1.5rem;
    }

    /* ── Metric row — no boxes, numbers in a strip ── */
    .mcard {
        background: transparent; border: none;
        border-right: 1px solid #DDD8CE;
        border-radius: 0; padding: 0.5rem 2rem 0.5rem 0;
    }
    .mcard-accent {
        background: transparent; border: none;
        border-right: 1px solid #DDD8CE;
        border-radius: 0; padding: 0.5rem 2rem 0.5rem 0;
    }
    .mval {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem; font-weight: 700; line-height: 1; color: #1C1C1C;
    }
    .mval-gold { color: #8B6914; }
    .mval-red { color: #9B1C1C; }
    .mval-green { color: #14532D; }
    .mval-purple { color: #4C1D95; }
    .mlbl {
        font-size: 0.72rem; font-weight: 400;
        color: #A8A49C; margin-top: 0.3rem; letter-spacing: 0.01em;
    }
    .mlbl-light { color: #8B6914; }
    .prog { background: #E2DDD6; border-radius: 0; height: 2px; overflow: hidden; margin-top: 1rem; }
    .prog-bar { height: 2px; border-radius: 0; background: linear-gradient(90deg, #9B1C1C 0%, #8B6914 50%, #14532D 100%); }

    /* ── Sentence highlights ──────────────────────── */
    .s-safe { display: inline; color: #1C1C1C; }
    .s-rewritten {
        display: inline; background: #EEF7F1; color: #14532D;
        border-bottom: 1.5px solid #4ADE80;
        padding: 0 3px; font-weight: 500;
    }
    .s-warning {
        display: inline; background: #FEFCE8; color: #78350F;
        border-bottom: 1.5px solid #EAB308;
        padding: 0 3px; cursor: pointer; transition: background 0.1s;
    }
    .s-warning:hover { background: #FEF9C3; }
    .s-danger {
        display: inline; background: #FFF5F5; color: #7F1D1D;
        border-bottom: 1.5px solid #EF4444;
        padding: 0 3px; cursor: pointer; transition: background 0.1s;
    }
    .s-danger:hover { background: #FEE2E2; }
    .s-selected { outline: 1.5px solid #1C1C1C !important; outline-offset: 2px; border-radius: 2px; }

    /* ── Legend — plain text, no pills ───────────── */
    .legend { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-top: 0.75rem; align-items: center; border-top: 1px solid #DDD8CE; padding-top: 0.75rem; }
    .lpill { background: transparent; border: none; font-size: 0.75rem; color: #7A766E; font-weight: 400; }

    /* ── Inspector ────────────────────────────────── */
    .inspector-sentence {
        background: transparent; border-left: 2px solid #DDD8CE;
        padding: 0.4rem 1rem 0.4rem 1rem; font-size: 0.97rem;
        line-height: 1.8; color: #1C1C1C;
        margin-bottom: 1rem; font-style: italic;
    }
    .inspector-danger { border-left-color: #EF4444 !important; }
    .inspector-warning { border-left-color: #EAB308 !important; }

    /* ── Badges — restrained ──────────────────────── */
    .badge {
        display: inline-flex; align-items: center; border-radius: 3px;
        padding: 0.15rem 0.6rem; font-size: 0.7rem; font-weight: 500;
        margin-bottom: 0.75rem; letter-spacing: 0.02em;
    }
    .b-danger { background: #FFF5F5; color: #7F1D1D; border: 1px solid #FCA5A5; }
    .b-warning { background: #FEFCE8; color: #78350F; border: 1px solid #FDE68A; }
    .b-done { background: #EEF7F1; color: #14532D; border: 1px solid #86EFAC; }
    .b-review { background: #F5F3FF; color: #4C1D95; border: 1px solid #C4B5FD; }

    /* ── AI rewrite ───────────────────────────────── */
    .ai-new-sentence {
        background: #EEF7F1; border-left: 3px solid #22C55E;
        border-radius: 0 4px 4px 0;
        padding: 0.9rem 1.25rem; font-size: 0.95rem;
        line-height: 1.8; color: #14532D; margin-bottom: 1rem;
    }

    /* ── Source cards — borderless rows ──────────── */
    .source-card {
        background: transparent; border: none;
        border-top: 1px solid #DDD8CE;
        border-radius: 0; padding: 0.85rem 0; margin-bottom: 0;
    }
    .source-name { font-weight: 600; font-size: 0.87rem; color: #1C1C1C; margin-bottom: 0.2rem; }
    .source-desc { font-size: 0.8rem; color: #7A766E; line-height: 1.55; }

    /* ── Editorial Desk ───────────────────────────── */
    .chat-box {
        display: flex; flex-direction: column; gap: 0.75rem;
        max-height: 300px; overflow-y: auto; padding: 0.25rem 0 0.5rem;
    }
    .cb-user {
        background: #1C1C1C; color: #F5F1E8;
        border-radius: 14px 14px 3px 14px;
        padding: 0.6rem 1rem; font-size: 0.84rem;
        line-height: 1.6; max-width: 80%; margin-left: auto;
    }
    .cb-ai {
        background: #EDE9E2; color: #1C1C1C;
        border-radius: 3px 14px 14px 14px;
        padding: 0.6rem 1rem; font-size: 0.84rem;
        line-height: 1.6; max-width: 80%;
    }
    .cn { font-size: 0.63rem; font-weight: 500; color: #A8A49C; margin-bottom: 0.15rem; letter-spacing: 0.03em; }
    .cn-r { text-align: right; }
    .cn-ai { color: #8B6914 !important; }

    /* ── Inputs — editorial, paper-like ──────────── */
    textarea, .stTextArea textarea {
        background: #FAF7F0 !important; color: #1C1C1C !important;
        border-radius: 4px !important; border: 1px solid #DDD8CE !important;
        font-family: Georgia, 'Times New Roman', serif !important;
        font-size: 0.97rem !important; line-height: 1.8 !important;
        box-shadow: none !important; padding: 1rem 1.1rem !important;
    }
    textarea:focus, .stTextArea textarea:focus {
        border-color: #8B6914 !important; box-shadow: none !important; outline: none !important;
    }
    .stTextInput input {
        background: #FAF7F0 !important; color: #1C1C1C !important;
        border-radius: 4px !important; border: 1px solid #DDD8CE !important;
        box-shadow: none !important; font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }
    .stTextInput input:focus { border-color: #8B6914 !important; box-shadow: none !important; outline: none !important; }
    .stTextInput input::placeholder { color: #B8B3AB !important; }

    /* ── Buttons — one dark primary, rest subtle ──── */
    .stButton > button {
        border-radius: 4px !important; padding: 0.48rem 1rem !important;
        border: 1px solid #C8C3BB !important;
        background: #FAF7F0 !important; color: #4A4640 !important;
        font-weight: 500 !important; font-size: 0.83rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.15s; box-shadow: none !important;
    }
    .stButton > button:hover { background: #EDE9E2 !important; border-color: #A8A49C !important; }
    /* Primary — Analyze article */
    div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button[kind="primary"],
    button[key="analyze_btn"] { background: #1C1C1C !important; color: #F5F1E8 !important; border-color: #1C1C1C !important; }

    /* ── Sidebar ──────────────────────────────────── */
    section[data-testid="stSidebar"] { background: #1C1C1C; border-right: 1px solid #2A2A2A; }
    section[data-testid="stSidebar"] * { color: #D5D0C8 !important; }
    section[data-testid="stSidebar"] h3 { color: #F5F1E8 !important; font-family: 'Playfair Display', serif !important; }
    section[data-testid="stSidebar"] strong { color: #C9A84C !important; }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(245,241,232,0.05) !important; color: #C9C5BC !important;
        border: 1px solid rgba(245,241,232,0.12) !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(245,241,232,0.1) !important; transform: none;
    }

    /* ── Misc ─────────────────────────────────────── */
    .stSelectbox > div > div { border-radius: 4px !important; border: 1px solid #DDD8CE !important; background: #FAF7F0 !important; }
    hr { border-color: #DDD8CE !important; }
    .stExpander { border: 1px solid #DDD8CE !important; border-radius: 4px !important; background: transparent !important; box-shadow: none !important; }
    .diff-b { background: #FFF5F5; border-left: 2px solid #EF4444; padding: 0.75rem 1rem; font-size: 0.9rem; color: #7F1D1D; line-height: 1.65; margin-bottom: 0.5rem; }
    .diff-a { background: #EEF7F1; border-left: 2px solid #22C55E; padding: 0.75rem 1rem; font-size: 0.9rem; color: #14532D; line-height: 1.65; }
    .diff-lbl { font-size: 0.66rem; font-weight: 500; letter-spacing: 0.05em; margin-bottom: 0.3rem; color: #A8A49C; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CORE FUNCTIONS
# --------------------------------------------------
def split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ").strip()
    if not text:
        return []
    sentences = re.findall(r'[^.!?]+[.!?]+|[^.!?]+$', text)
    return [s.strip() for s in sentences if s.strip()]


def extract_years(s: str) -> List[int]:
    return [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', s)]


def contains_any(s: str, kws: List[str]) -> bool:
    lower = s.lower()
    return any(k in lower for k in kws)


def has_number(s: str) -> bool:
    return bool(re.search(r'\b\d+(?:\.\d+)?%?\b', s))


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(v, hi))


TIME_KW = [
    "currently", "recently", "today", "now", "next year", "this year", "this month",
    "this week", "this summer", "this winter", "this quarter", "will", "planned",
    "expected to", "forecast", "soon", "upcoming"
]
NUM_KW = [
    "inflation", "price", "prices", "market share", "interest rate", "unemployment",
    "gdp", "leader", "sales", "revenue", "ranked", "ranking"
]


def analyze_sentence(sentence: str) -> Dict[str, Any]:
    score = 100
    reasons = []
    lower = sentence.lower()
    years = extract_years(sentence)

    for year in years:
        age = CURRENT_YEAR - year
        if age >= 4:
            score -= 45
            reasons.append(f"References {year} ({age} years ago) — likely outdated.")
        elif age >= 2:
            score -= 28
            reasons.append(f"References {year} — may need a freshness check.")
        elif age >= 1:
            score -= 12
            reasons.append(f"Date from {year} adds temporal sensitivity.")

    if contains_any(sentence, TIME_KW):
        score -= 22
        reasons.append("Uses time-sensitive language like 'currently' or future-oriented wording.")

    if contains_any(sentence, NUM_KW) and has_number(sentence):
        score -= 18
        reasons.append("Numerical claim on a topic that changes over time.")

    if ("next year" in lower or "will" in lower) and any(y < CURRENT_YEAR for y in years):
        score -= 18
        reasons.append("Future language combined with a past date — strongly suggests it is outdated.")

    score = clamp(score, 5, 100)
    label = "danger" if score < 50 else "warning" if score < 72 else "safe"
    explanation = " ".join(reasons) if reasons else "No strong signs of temporal risk detected."

    return {
        "sentence": sentence,
        "score": score,
        "label": label,
        "explanation": explanation,
        "years": years,
    }


def render_article(results: List[Dict[str, Any]], rewrites: Dict[str, str], sel_original: Optional[str] = None) -> str:
    parts = []
    for i, item in enumerate(results):
        orig = item["sentence"]
        txt = escape(orig)

        if orig in rewrites:
            new_txt = escape(rewrites[orig])
            parts.append(f"<span class='s-rewritten'>{new_txt}</span> ")
            continue

        if item["label"] == "safe":
            parts.append(f"<span class='s-safe'>{txt} </span>")
        else:
            sel = " s-selected" if orig == sel_original else ""
            label = item["label"]
            parts.append(f"<span class='s-{label}{sel}' data-sent-idx='{i}' title='Click to inspect'>{txt}</span> ")

    return "".join(parts)

# --------------------------------------------------
# RESPONSES API HELPERS
# --------------------------------------------------
def response_output_text(resp: Any) -> str:
    text = getattr(resp, "output_text", None)
    if text:
        return text

    try:
        data = resp.model_dump()
        output = data.get("output", [])
        chunks = []
        for item in output:
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        chunks.append(content.get("text", ""))
        return "\n".join(chunks).strip()
    except Exception:
        return ""


def normalize_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"


def dedupe_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    cleaned = []
    for src in sources:
        key = (src.get("url", "").strip(), src.get("title", "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(src)
    return cleaned[:MAX_SOURCE_COUNT]


def build_research_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["outdated", "still_valid", "uncertain", "needs_manual_review"],
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "reason": {"type": "string"},
            "what_changed": {"type": "string"},
            "rewrite": {"type": "string"},
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "publisher": {"type": "string"},
                        "title": {"type": "string"},
                        "author": {"type": "string"},
                        "date": {"type": "string"},
                        "url": {"type": "string"},
                        "relevance": {"type": "string"},
                    },
                    "required": ["publisher", "title", "author", "date", "url", "relevance"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["status", "confidence", "reason", "what_changed", "rewrite", "sources"],
        "additionalProperties": False,
    }


def coerce_research_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    status = payload.get("status", "needs_manual_review")
    if status not in {"outdated", "still_valid", "uncertain", "needs_manual_review"}:
        status = "needs_manual_review"

    confidence = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    rewrite = (payload.get("rewrite") or "").strip()
    reason = (payload.get("reason") or "").strip()
    what_changed = (payload.get("what_changed") or "").strip()

    raw_sources = payload.get("sources") or []
    sources = []
    for src in raw_sources[:MAX_SOURCE_COUNT]:
        if not isinstance(src, dict):
            continue
        sources.append({
            "publisher": str(src.get("publisher", "Source")).strip(),
            "title": str(src.get("title", "Untitled source")).strip(),
            "author": str(src.get("author", "N/A")).strip(),
            "date": str(src.get("date", "")).strip(),
            "url": normalize_url(str(src.get("url", "")).strip()),
            "relevance": str(src.get("relevance", "Relevant supporting source.")).strip(),
        })

    sources = dedupe_sources(sources)

    if not reason:
        reason = "The model could not clearly justify this result, so manual review is recommended."
    if not what_changed:
        what_changed = "No clear change summary was returned."
    if not rewrite:
        rewrite = ""

    if status in {"uncertain", "needs_manual_review"} and confidence > 0.75:
        confidence = 0.75

    if not sources:
        status = "needs_manual_review"
        confidence = min(confidence, 0.5)
        reason = "No reliable recent sources were found to support an automatic update."

    return {
        "status": status,
        "confidence": confidence,
        "reason": reason,
        "what_changed": what_changed,
        "rewrite": rewrite,
        "sources": sources,
    }


def is_weak_result(result: Dict[str, Any]) -> bool:
    if not result:
        return True
    if result.get("status") in {"uncertain", "needs_manual_review"}:
        return True
    if float(result.get("confidence", 0.0)) < RESEARCH_CONFIDENCE_RETRY_THRESHOLD:
        return True
    if len(result.get("sources", [])) == 0:
        return True
    if len(result.get("rewrite", "").strip()) < 40:
        return True
    return False


def _run_research_pass(sentence: str, article_context: str, extra_instruction: str = "") -> Dict[str, Any]:
    prompt = f"""
You are an editorial research assistant for journalists.

Task:
Assess whether the selected sentence is outdated, still valid, uncertain, or needs manual review.
Use web search to gather recent reputable evidence before deciding.

Requirements:
- {PREFERRED_SOURCE_HINT}
- Use web search and base the answer on real recent reporting or official sources.
- Do not invent source details.
- Prefer specific, current rewrites over vague paraphrases.
- If the sentence is about a forecast, trend, market movement, inflation, energy prices, or policy outlook, rewrite it using the latest concrete direction or expectation supported by sources.
- If the sentence refers to an old future event, update it to what actually happened.
- Treat promotional claims like 'market leader' cautiously unless supported by a clearly attributable ranking or methodology.
- Remove vague temporal wording like 'currently', 'recently', 'next year', or 'this summer' unless the timing is clearly anchored.
- Keep rewrite to one sentence in neutral journalistic language.
- The rewrite must be more informative than the original and should mention the current development, latest estimate, or updated status when available.
- Include up to {MAX_SOURCE_COUNT} real sources with publisher, title, author, date, url, and relevance.
- If evidence is weak, conflicting, or vague, return status='needs_manual_review' or 'uncertain'.
- If the sentence is historical and still acceptable in context, do not rewrite it aggressively.
- For numerical or forecast claims, prioritize the most recent reliable source.
- If the first search results are weak or vague, refine the search and try again.

Additional instruction:
{extra_instruction or 'None'}

Article context:
{article_context}

Selected sentence:
{sentence}
""".strip()

    response = client.responses.create(
        model=RESEARCH_MODEL,
        tools=[{"type": "web_search"}],
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "sentence_refresh",
                "schema": build_research_schema(),
            }
        },
    )

    raw_text = response_output_text(response)

    try:
        payload = json.loads(raw_text)
    except Exception:
        return {
            "status": "needs_manual_review",
            "confidence": 0.0,
            "reason": "The model response could not be parsed into structured research output.",
            "what_changed": "No reliable automatic change summary was available.",
            "rewrite": "",
            "sources": [],
        }

    return coerce_research_result(payload)


@st.cache_data(show_spinner=False, ttl=3600)
def research_sentence(sentence: str, article_context: str) -> Dict[str, Any]:
    first_result = _run_research_pass(sentence, article_context)
    if is_weak_result(first_result):
        retry_instruction = (
            "The first pass was too weak or too vague. Search again more thoroughly. "
            "Focus on the latest reliable reporting, concrete 2025/2026 developments when relevant, "
            "official data, and a more specific updated sentence."
        )
        second_result = _run_research_pass(sentence, article_context, retry_instruction)
        if not is_weak_result(second_result) or float(second_result.get("confidence", 0.0)) >= float(first_result.get("confidence", 0.0)):
            return second_result
    return first_result


@st.cache_data(show_spinner=False, ttl=900)
def ask_editorial_chat(question: str, article: str) -> str:
    prompt = f"""
You are TimeTravel, an editorial AI assistant.

Answer the user's question about the article below.
If the question asks for up-to-date information, you may use web search.
Be concise, specific, and editor-friendly.
Use reputable sources and mention when something needs manual review.

Article:
{article.strip() if article.strip() else 'No article pasted yet.'}

User question:
{question}
""".strip()

    response = client.responses.create(
        model=CHAT_MODEL,
        tools=[{"type": "web_search"}],
        input=prompt,
    )
    return response_output_text(response) or "I couldn't generate a useful answer."

# --------------------------------------------------
# DEMO
# --------------------------------------------------
DEMO = (
    "In 2021, the company announced that it would launch its electric delivery fleet next year. "
    "The CEO currently says the business is the market leader in battery logistics. "
    "Inflation is 2.1% and energy prices are expected to fall this summer. "
    "The company opened three hubs in Germany in 2023. "
    "Analysts recently described the expansion strategy as highly effective. "
    "The government will introduce a subsidy program in 2024 to support infrastructure upgrades."
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
DEFAULT_STATE = {
    "article_text": "",
    "results": [],
    "analyzed": False,
    "selected_sentence": None,
    "rewrites": {},
    "research_result": None,
    "research_error": None,
    "chat_messages": [],
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --------------------------------------------------
# EDITORIAL DESK
# --------------------------------------------------
def _do_chat(question: str) -> None:
    st.session_state.chat_messages.append({"role": "user", "content": question})
    answer = ask_editorial_chat(question, st.session_state.article_text)
    st.session_state.chat_messages.append({"role": "assistant", "content": answer})


def _render_editorial_desk() -> None:
    st.markdown('<div class="card" style="border-top:3px solid #c9a84c;margin-top:1.2rem;">', unsafe_allow_html=True)
    st.markdown('<div class="slabel"><span class="slabel-dot"></span>Editorial Desk</div>', unsafe_allow_html=True)

    msgs = st.session_state.get("chat_messages", [])
    if msgs:
        parts = []
        for m in msgs[-8:]:
            if m["role"] == "user":
                parts.append(f"<div class='cn cn-r'>You</div><div class='cb-user'>{escape(m['content'])}</div>")
            else:
                parts.append(f"<div class='cn cn-ai'>TimeTravel</div><div class='cb-ai'>{escape(m['content'])}</div>")
        st.markdown(f"<div class='chat-box'>{''.join(parts)}</div>", unsafe_allow_html=True)

    ci1, ci2 = st.columns([5, 1])
    with ci1:
        user_q = st.text_input(
            "Ask", key="chat_input_field",
            label_visibility="collapsed",
            placeholder="Ask about this article...",
        )
    with ci2:
        send = st.button("Send", key="chat_send_btn", use_container_width=True)

    if send and user_q.strip():
        with st.spinner("Researching..."):
            _do_chat(user_q.strip())
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 🕰️ TimeTravel")
    st.markdown(
        "<div style='font-size:0.82rem;color:#94a3b8;margin-bottom:1.2rem;'>"
        "Editorial AI for temporal credibility.</div>",
        unsafe_allow_html=True,
    )

    if st.button("Load new PDF", use_container_width=True):
        st.session_state.update({
            "article_text": "",
            "results": [],
            "analyzed": False,
            "rewrites": {},
            "selected_sentence": None,
            "research_result": None,
            "research_error": None,
            "chat_messages": [],
        })

    st.markdown("---")
    st.markdown("### How it works")
    st.markdown(
        "1. Upload a **PDF article**\n"
        "2. Click **Analyze**\n"
        "3. **Click** a flagged sentence\n"
        "4. Click **Research latest evidence**\n"
        "5. Accept only strong rewrites"
    )
    st.markdown("---")
    st.markdown(
        "**🟡 Yellow** — review recommended  \n"
        "**🔴 Red** — likely outdated  \n"
        "**🟢 Green** — rewritten by AI"
    )

# --------------------------------------------------
# TOPBAR
# --------------------------------------------------
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">Time<span>Travel</span></div>
    <div class="topbar-tag">Editorial AI &nbsp;·&nbsp; Prototype</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <div class="page-title">Temporal Trust Checker</div>
    <div class="page-sub">Detect outdated claims, research the latest evidence, and replace risky wording with source-backed rewrites.</div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# UTILS FOR UI
# --------------------------------------------------
def status_badge(status: str) -> str:
    mapping = {
        "outdated": "<div class='badge b-danger'>🔴 Outdated</div>",
        "still_valid": "<div class='badge b-done'>🟢 Still valid</div>",
        "uncertain": "<div class='badge b-warning'>🟡 Uncertain</div>",
        "needs_manual_review": "<div class='badge b-review'>🟣 Manual review</div>",
    }
    return mapping.get(status, "<div class='badge b-review'>🟣 Review</div>")


def confidence_color(conf: float) -> str:
    if conf >= 0.8:
        return "#16a34a"
    if conf >= 0.6:
        return "#f59e0b"
    return "#ef4444"


def can_accept_result(result: Dict[str, Any]) -> bool:
    return (
        result.get("status") in {"outdated", "still_valid"}
        and bool(result.get("rewrite", "").strip())
        and float(result.get("confidence", 0)) >= MIN_ACCEPT_CONFIDENCE
        and len(result.get("sources", [])) > 0
    )


def source_cards_html(sources: List[Dict[str, Any]]) -> str:
    cards = []
    for src in sources[:MAX_SOURCE_COUNT]:
        publisher = escape(src.get("publisher", "Source"))
        title = escape(src.get("title", "Untitled source"))
        author = escape(src.get("author", "N/A"))
        date = escape(src.get("date", ""))
        url = escape(src.get("url", ""))
        relevance = escape(src.get("relevance", ""))
        link_html = f"<a href='{url}' target='_blank'>Open article</a>" if url else ""

        cards.append(
            f"""
            <div class='source-card'>
                <div class='source-name'>📰 {publisher}</div>
                <div class='source-desc'><strong>Title:</strong> {title}</div>
                <div class='source-desc'><strong>Author:</strong> {author}</div>
                <div class='source-desc'><strong>Date:</strong> {date}</div>
                <div class='source-desc' style='margin-top:0.3rem;'>{relevance}</div>
                <div class='source-desc' style='margin-top:0.35rem;'>{link_html}</div>
            </div>
            """
        )
    return "".join(cards)

# --------------------------------------------------
# ARTICLE INPUT
# --------------------------------------------------
if True:
    if not st.session_state.article_text:
        import pypdf, io, urllib.request
        st.markdown("""
        <div style='padding:2.5rem 0 1.75rem;border-bottom:1px solid #DDD8CE;margin-bottom:1.75rem;'>
            <div style='font-family:"Playfair Display",serif;font-size:2rem;font-weight:700;color:#1C1C1C;margin-bottom:0.4rem;line-height:1.2;'>Load your article</div>
            <div style='font-size:0.87rem;color:#7A766E;line-height:1.65;'>Paste a URL to fetch from the web, or upload a PDF.</div>
        </div>
        """, unsafe_allow_html=True)

        url_col, pdf_col = st.columns(2, gap="large")

        with url_col:
            st.markdown("<p style='font-size:0.78rem;font-weight:400;color:#7A766E;margin:0 0 0.5rem;'>Article URL</p>", unsafe_allow_html=True)
            url_input = st.text_input("URL", label_visibility="collapsed", placeholder="https://...", key="url_input")
            if st.button("Fetch article", use_container_width=True, key="fetch_url_btn"):
                if url_input.strip():
                    try:
                        from html.parser import HTMLParser
                        class _TextExtractor(HTMLParser):
                            def __init__(self):
                                super().__init__()
                                self._skip = False
                                self.chunks = []
                            def handle_starttag(self, tag, _attrs):
                                if tag in ("script", "style", "nav", "header", "footer", "aside"):
                                    self._skip = True
                            def handle_endtag(self, tag):
                                if tag in ("script", "style", "nav", "header", "footer", "aside"):
                                    self._skip = False
                            def handle_data(self, data):
                                if not self._skip and data.strip():
                                    self.chunks.append(data.strip())
                        req = urllib.request.Request(url_input.strip(), headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=10) as r:
                            raw = r.read()
                        parser = _TextExtractor()
                        parser.feed(raw.decode("utf-8", errors="replace"))
                        fetched = " ".join(parser.chunks).strip()
                        if fetched:
                            st.session_state.article_text = fetched
                            st.session_state.analyzed = False
                            st.session_state.results = []
                            st.session_state.rewrites = {}
                            st.session_state.selected_sentence = None
                            st.session_state.research_result = None
                            st.rerun()
                        else:
                            st.error("Could not extract text from that URL.")
                    except Exception as e:
                        st.error(f"Could not fetch URL: {e}")

        with pdf_col:
            st.markdown("<p style='font-size:0.78rem;font-weight:400;color:#7A766E;margin:0 0 0.5rem;'>Upload PDF</p>", unsafe_allow_html=True)
            uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed", key="pdf_upload")
            if uploaded_pdf is not None:
                try:
                    reader = pypdf.PdfReader(io.BytesIO(uploaded_pdf.read()))
                    pages_text = [page.extract_text() or "" for page in reader.pages]
                    full_text = " ".join(pages_text).strip()
                    if full_text:
                        st.session_state.article_text = full_text
                        st.session_state.analyzed = False
                        st.session_state.results = []
                        st.session_state.rewrites = {}
                        st.session_state.selected_sentence = None
                        st.session_state.research_result = None
                        st.rerun()
                    else:
                        st.error("Could not extract text — PDF may be scanned/image-based.")
                except Exception as e:
                    st.error(f"Could not read PDF: {e}")

    article_text = st.text_area(
        "Article",
        value=st.session_state.article_text,
        height=130,
        label_visibility="collapsed",
        placeholder="Paste your article here, or load one above…",
    )
    st.session_state.article_text = article_text

    bcol, _ = st.columns([1, 3])
    with bcol:
        st.markdown('<style>button[kind="secondaryFormSubmit"], .stButton button { } #analyze_btn, [data-testid="stButton"]:has([data-testid="baseButton-secondary"][key="analyze_btn"]) button { background: #1C1C1C !important; color: #F5F1E8 !important; border-color: #1C1C1C !important; font-weight: 600 !important; padding: 0.6rem 1.25rem !important; font-size: 0.88rem !important; letter-spacing: 0.02em !important; } </style>', unsafe_allow_html=True)
        if st.button("Analyze article", use_container_width=True, key="analyze_btn"):
            if article_text.strip():
                sents = split_sentences(article_text)
                st.session_state.results = [analyze_sentence(s) for s in sents]
                st.session_state.analyzed = True
                st.session_state.selected_sentence = None
                st.session_state.research_result = None
                st.session_state.research_error = None
                st.session_state.rewrites = {}

    results = st.session_state.results
    risky = [
        r for r in results
        if r["label"] != "safe" and r["sentence"] not in st.session_state.rewrites
    ]

    if st.session_state.analyzed and results:
        freshness = round(sum(r["score"] for r in results) / len(results))
        rewrites_done = len(st.session_state.rewrites)

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(
                f"""<div class="mcard-accent">
                    <div class="mval mval-gold">{freshness}</div>
                    <div class="mlbl mlbl-light">Freshness Score</div>
                    <div class="prog"><div class="prog-bar" style="width:{freshness}%;"></div></div>
                </div>""",
                unsafe_allow_html=True,
            )
        with mc2:
            st.markdown(
                f"""<div class="mcard">
                    <div class="mval mval-red">{len(risky)}</div>
                    <div class="mlbl">Still Flagged</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with mc3:
            st.markdown(
                f"""<div class="mcard">
                    <div class="mval mval-purple">{len(results)}</div>
                    <div class="mlbl">Total Sentences</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with mc4:
            st.markdown(
                f"""<div class="mcard">
                    <div class="mval mval-green">{rewrites_done}</div>
                    <div class="mlbl">Accepted</div>
                </div>""",
                unsafe_allow_html=True,
            )

        _render_editorial_desk()

        if True:
            st.markdown('<div style="position:fixed;top:-9999px;left:-9999px;opacity:0;pointer-events:none;">', unsafe_allow_html=True)
            btn_clicks = [st.button(f"§{i}§", key=f"hbtn_{i}") for i in range(len(results))]
            st.markdown("</div>", unsafe_allow_html=True)

            for i, clicked in enumerate(btn_clicks):
                if clicked and results[i]["label"] != "safe" and results[i]["sentence"] not in st.session_state.rewrites:
                    if results[i]["sentence"] != st.session_state.selected_sentence:
                        st.session_state.selected_sentence = results[i]["sentence"]
                    else:
                        st.session_state.selected_sentence = None
                    st.session_state.research_result = None
                    st.session_state.research_error = None
                    st.rerun()

            article_html = render_article(results, st.session_state.rewrites, st.session_state.selected_sentence)
            component_html = f"""<!DOCTYPE html><html><head><style>
                body{{margin:0;padding:1.5rem 1.75rem;font-family:Georgia,'Times New Roman',serif;font-size:1rem;line-height:2;color:#1C1C1C;background:#FAF7F0;}}
                .s-safe{{display:inline;color:#1C1C1C;}}
                .s-rewritten{{display:inline;background:#EEF7F1;color:#14532D;border-bottom:1.5px solid #4ADE80;padding:0 3px;font-weight:500;}}
                .s-warning{{display:inline;background:#FEFCE8;color:#78350F;border-bottom:1.5px solid #EAB308;padding:0 3px;cursor:pointer;transition:background 0.1s;}}
                .s-warning:hover{{background:#FEF9C3;}}
                .s-danger{{display:inline;background:#FFF5F5;color:#7F1D1D;border-bottom:1.5px solid #EF4444;padding:0 3px;cursor:pointer;transition:background 0.1s;}}
                .s-danger:hover{{background:#FEE2E2;}}
                .s-selected{{outline:1.5px solid #1C1C1C!important;outline-offset:2px;border-radius:2px;}}
            </style></head><body>{article_html}<script>
                function hideSecretBtns() {{
                    try {{
                        window.parent.document.querySelectorAll('button').forEach(function(btn) {{
                            if (/^§\d+§$/.test(btn.innerText.trim())) {{
                                btn.style.position = 'fixed';
                                btn.style.top = '-9999px';
                                btn.style.left = '-9999px';
                                btn.style.width = '1px';
                                btn.style.height = '1px';
                                btn.style.opacity = '0';
                                btn.style.pointerEvents = 'none';
                                var p = btn.parentElement;
                                if (p) {{ p.style.position = 'fixed'; p.style.top = '-9999px'; p.style.left = '-9999px'; }}
                            }}
                        }});
                    }} catch(e) {{}}
                }}
                hideSecretBtns();
                setInterval(hideSecretBtns, 300);

                document.querySelectorAll('[data-sent-idx]').forEach(function(el){{
                    el.addEventListener('click', function(){{
                        var idx = this.getAttribute('data-sent-idx');
                        try {{
                            var btns = window.parent.document.querySelectorAll('button');
                            for (var b = 0; b < btns.length; b++) {{
                                if (btns[b].innerText.trim() === '§' + idx + '§') {{
                                    btns[b].click();
                                    return;
                                }}
                            }}
                        }} catch(e) {{}}
                    }});
                }});
            </script></body></html>"""
            components.html(component_html, height=260, scrolling=True)

            st.markdown(
                """<div class="legend">
                    <div class="lpill">🟡 Yellow — review recommended</div>
                    <div class="lpill">🔴 Red — likely outdated</div>
                    <div class="lpill">🟢 Green — accepted rewrite</div>
                </div>""",
                unsafe_allow_html=True,
            )

            if not risky:
                st.markdown(
                    "<div style='margin-top:0.75rem;font-size:0.85rem;color:#16A34A;font-weight:500;'>✅ All flagged sentences have been handled.</div>",
                    unsafe_allow_html=True,
                )

            sel_sentence = st.session_state.selected_sentence
            sel_item = next((r for r in results if r["sentence"] == sel_sentence), None)

            if sel_item:
                st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)
                badge_cls = "b-danger" if sel_item["label"] == "danger" else "b-warning"
                badge_txt = "🔴 Likely outdated" if sel_item["label"] == "danger" else "🟡 Time-sensitive"
                q_cls = "inspector-danger" if sel_item["label"] == "danger" else "inspector-warning"
                sc_color = "#ef4444" if sel_item["score"] < 50 else "#f59e0b"

                hc1, hc2 = st.columns([3, 1])
                with hc1:
                    st.markdown(f'<div class="badge {badge_cls}">{badge_txt}</div>', unsafe_allow_html=True)
                with hc2:
                    st.markdown(
                        f"<div style='text-align:right;font-family:Playfair Display,serif;font-size:1.9rem;font-weight:700;color:{sc_color};'>{sel_item['score']}</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown(f"<div class='inspector-sentence {q_cls}'>{escape(sel_item['sentence'])}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='font-size:0.84rem;color:#64748b;line-height:1.6;margin-bottom:1rem;'>{escape(sel_item['explanation'])}</div>",
                    unsafe_allow_html=True,
                )

                if st.button("🌐  Research latest evidence", use_container_width=True, key="research_btn"):
                    try:
                        with st.spinner("Searching the web and comparing sources..."):
                            st.session_state.research_result = research_sentence(
                                sel_item["sentence"],
                                st.session_state.article_text,
                            )
                            st.session_state.research_error = None
                    except Exception as e:
                        st.session_state.research_result = None
                        st.session_state.research_error = str(e)

                if st.session_state.research_error:
                    st.error(f"Research failed: {st.session_state.research_error}")

                result = st.session_state.research_result
                if result:
                    conf = float(result.get("confidence", 0.0))
                    st.markdown(status_badge(result.get("status", "needs_manual_review")), unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='font-size:0.84rem;color:#64748b;line-height:1.6;margin-bottom:0.8rem;'><strong>Reason:</strong> {escape(result.get('reason', ''))}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='font-size:0.84rem;color:#64748b;line-height:1.6;margin-bottom:0.8rem;'><strong>What changed:</strong> {escape(result.get('what_changed', ''))}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='margin-bottom:0.8rem;font-size:0.85rem;color:{confidence_color(conf)};font-weight:700;'>Confidence: {round(conf * 100)}%</div>",
                        unsafe_allow_html=True,
                    )

                    if result.get("rewrite"):
                        st.markdown('<div class="slabel">Suggested updated sentence</div>', unsafe_allow_html=True)
                        st.markdown(f"<div class='ai-new-sentence'>{escape(result['rewrite'])}</div>", unsafe_allow_html=True)

                    st.markdown('<div class="slabel">Supporting sources</div>', unsafe_allow_html=True)
                    st.markdown(source_cards_html(result.get("sources", [])), unsafe_allow_html=True)

                    allow_accept = can_accept_result(result)
                    if not allow_accept:
                        st.info(
                            "This result is not strong enough for automatic replacement yet. "
                            "You can keep it for editor review or research again with more context."
                        )

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(
                            "✅  Accept & replace sentence",
                            use_container_width=True,
                            key="accept_btn",
                            disabled=not allow_accept,
                        ):
                            orig = sel_item["sentence"]
                            new = result["rewrite"].strip() or orig
                            st.session_state.rewrites[orig] = new
                            st.session_state.selected_sentence = None
                            st.session_state.research_result = None
                            st.session_state.research_error = None
                            st.rerun()
                    with c2:
                        if st.button("↩️  Clear research result", use_container_width=True, key="clear_research_btn"):
                            st.session_state.research_result = None
                            st.session_state.research_error = None
                            st.rerun()


    else:
        st.markdown(
            """
            <div style='padding:3rem 0;border-top:1px solid #DDD8CE;'>
                <div style='font-size:0.95rem;color:#A8A49C;line-height:1.7;'>
                    Once you load an article and click <em>Analyze article</em>, flagged sentences will appear highlighted below.
                    Select one to inspect it, research the latest evidence, and accept a source-backed rewrite.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==================================================
