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
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0f9ff 100%); color: #1a1a2e; }
    .block-container { max-width: 1200px; padding-top: 0; padding-bottom: 3rem; }

    .topbar {
        background: linear-gradient(135deg, #1a1a2e 0%, #2d1b69 50%, #1a1a2e 100%);
        padding: 1rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -4rem -4rem 2rem -4rem;
        border-bottom: 3px solid #f0c95a;
        box-shadow: 0 4px 20px rgba(26,26,46,0.3);
    }
    .topbar-logo {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem; font-weight: 700; color: #fff;
    }
    .topbar-logo span { color: #f0c95a; }
    .topbar-tag {
        font-size: 0.68rem; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase;
        color: #c4b5fd; background: rgba(167,139,250,0.15);
        border: 1px solid rgba(167,139,250,0.3);
        border-radius: 999px; padding: 0.28rem 0.8rem;
    }

    .page-header { margin-bottom: 1.8rem; }
    .page-title {
        font-family: 'Playfair Display', serif;
        font-size: 2rem; font-weight: 700;
        color: #1a1a2e; margin-bottom: 0.3rem;
    }
    .page-sub { font-size: 0.9rem; color: #64748b; line-height: 1.6; }

    .stTabs [data-baseweb="tab-list"] {
        background: #ede9f8; border-radius: 12px;
        padding: 3px; gap: 3px; border: none;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px; padding: 0.45rem 1.3rem;
        font-weight: 600; font-size: 0.87rem;
        color: #64748b; background: transparent; border: none;
    }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg,#2d1b69,#1a1a2e) !important; color: #fff !important; }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

    .card {
        background: #fff;
        border: 1px solid #e8e4f3;
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 4px 24px rgba(109,40,217,0.07), 0 1px 4px rgba(26,26,46,0.05);
    }

    .slabel {
        font-size: 0.67rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.11em;
        color: #94a3b8; margin-bottom: 0.6rem;
        display: flex; align-items: center; gap: 0.4rem;
    }
    .slabel-dot {
        width: 7px; height: 7px;
        background: #f0c95a; border-radius: 50%;
        display: inline-block;
    }

    .mcard {
        flex: 1; background: #fff;
        border: 1px solid #e8e4f3;
        border-radius: 16px; padding: 1rem 1.2rem;
        box-shadow: 0 4px 16px rgba(109,40,217,0.06);
    }
    .mcard-accent {
        flex: 1; background: linear-gradient(135deg, #1a1a2e 0%, #2d1b69 100%);
        border-radius: 16px; padding: 1rem 1.2rem;
        box-shadow: 0 4px 16px rgba(45,27,105,0.3);
    }
    .mval {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem; font-weight: 700;
        line-height: 1; color: #1a1a2e;
    }
    .mval-gold { color: #f0c95a; }
    .mval-red { color: #ef4444; }
    .mval-green { color: #22c55e; }
    .mlbl {
        font-size: 0.69rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.09em;
        color: #64748b; margin-top: 0.2rem;
    }
    .mlbl-light { color: #94a3b8; }

    .prog { background: rgba(255,255,255,0.12); border-radius: 999px; height: 5px; overflow: hidden; margin-top: 0.5rem; }
    .prog-bar { height: 5px; border-radius: 999px; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%); }

    .s-safe { display: inline; color: #1a1a2e; text-decoration: none; }
    .s-rewritten {
        display: inline;
        background: #f0fdf4;
        color: #14532d;
        border: 1.5px solid #86efac;
        border-radius: 6px;
        padding: 2px 8px; margin: 1px;
        font-weight: 500; text-decoration: none;
    }
    .s-warning {
        display: inline;
        background: #fffbeb; color: #78450a;
        border: 1.5px solid #fcd34d;
        border-radius: 6px;
        padding: 2px 8px; margin: 1px;
        text-decoration: none; cursor: pointer;
        transition: all 0.15s;
    }
    .s-warning:hover { background: #fef3c7; border-color: #f59e0b; box-shadow: 0 2px 8px rgba(245,158,11,0.25); }
    .s-danger {
        display: inline;
        background: #fff1f1; color: #7f1d1d;
        border: 1.5px solid #fca5a5;
        border-radius: 6px;
        padding: 2px 8px; margin: 1px;
        text-decoration: none; cursor: pointer;
        transition: all 0.15s;
    }
    .s-danger:hover { background: #fee2e2; border-color: #ef4444; box-shadow: 0 2px 8px rgba(239,68,68,0.25); }
    .s-selected {
        outline: 2.5px solid #1a1a2e !important;
        outline-offset: 2px;
        box-shadow: 0 2px 12px rgba(26,26,46,0.22) !important;
    }

    .legend { display: flex; gap: 0.45rem; flex-wrap: wrap; margin-top: 0.8rem; }
    .lpill {
        background: #fff; border: 1px solid #dde3ec;
        border-radius: 999px; padding: 0.28rem 0.75rem;
        font-size: 0.76rem; color: #64748b;
    }

    .inspector-sentence {
        background: #fafbfc;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        font-size: 0.97rem;
        line-height: 1.75;
        color: #1a1a2e;
        border-left: 4px solid #dde3ec;
        margin-bottom: 1rem;
        font-style: italic;
    }
    .inspector-danger { border-left-color: #ef4444; }
    .inspector-warning { border-left-color: #f59e0b; }

    .badge {
        display: inline-block; border-radius: 999px;
        padding: 0.24rem 0.7rem;
        font-size: 0.71rem; font-weight: 700;
        margin-bottom: 0.7rem;
    }
    .b-danger { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .b-warning { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .b-done { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
    .b-review { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }

    .ai-new-sentence {
        background: #f0fdf4;
        border: 1.5px solid #86efac;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        font-size: 0.96rem;
        line-height: 1.75;
        color: #14532d;
        margin-bottom: 0.8rem;
    }
    .source-card {
        background: linear-gradient(135deg, #f8fbff 0%, #f5f3ff 100%);
        border: 1px solid #c4b5fd;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }
    .source-name {
        font-weight: 700; font-size: 0.9rem;
        color: #5b21b6; margin-bottom: 0.2rem;
    }
    .source-desc { font-size: 0.82rem; color: #475569; line-height: 1.5; }

    .chat-box {
        display: flex; flex-direction: column;
        gap: 0.6rem; max-height: 260px;
        overflow-y: auto; padding: 0.2rem 0 0.4rem 0;
    }
    .cb-user {
        background: #1a1a2e; color: #fff;
        border-radius: 16px 16px 4px 16px;
        padding: 0.65rem 1rem; font-size: 0.85rem;
        line-height: 1.55; max-width: 85%; margin-left: auto;
    }
    .cb-ai {
        background: #f1f4f8;
        border: 1px solid #dde3ec;
        color: #1a1a2e;
        border-radius: 16px 16px 16px 4px;
        padding: 0.65rem 1rem; font-size: 0.85rem;
        line-height: 1.55; max-width: 85%;
    }
    .cn { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 0.2rem; }
    .cn-r { text-align: right; color: #94a3b8; }
    .cn-ai { color: #1a1a2e !important; }

    .chat-input-row {
        display: flex; align-items: center; gap: 0.5rem;
        background: #f1f4f8; border: 1.5px solid #dde3ec;
        border-radius: 14px; padding: 0.3rem 0.4rem 0.3rem 1rem;
        margin-top: 0.7rem;
    }

    .chip-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.6rem; }
    .chip button {
        background: #fff !important; color: #1a1a2e !important;
        border: 1.5px solid #dde3ec !important;
        border-radius: 999px !important;
        font-size: 0.78rem !important; font-weight: 500 !important;
        padding: 0.3rem 0.85rem !important;
    }
    .chip button:hover { background: #f1f4f8 !important; border-color: #94a3b8 !important; }

    .clog-card {
        background: #fff; border: 1px solid #e4e1db;
        border-radius: 18px; padding: 1.3rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(26,26,46,0.04);
    }
    .diff-b {
        background: #fff5f5; border-left: 4px solid #ef4444;
        border-radius: 0 12px 12px 0;
        padding: 0.75rem 1rem; font-size: 0.9rem;
        color: #7f1d1d; line-height: 1.65; margin-bottom: 0.5rem;
    }
    .diff-a {
        background: #f0fdf4; border-left: 4px solid #22c55e;
        border-radius: 0 12px 12px 0;
        padding: 0.75rem 1rem; font-size: 0.9rem;
        color: #14532d; line-height: 1.65;
    }
    .diff-lbl {
        font-size: 0.66rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.09em;
        margin-bottom: 0.3rem;
    }

    textarea, .stTextArea textarea {
        background: #fff !important; color: #1a1a2e !important;
        border-radius: 14px !important; border: 1.5px solid #e4e1db !important;
        font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important;
    }
    .stTextInput input {
        background: transparent !important;
        color: #1a1a2e !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: none !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput input::placeholder { color: #94a3b8 !important; }

    .stButton > button {
        border-radius: 10px !important; padding: 0.55rem 1.1rem !important;
        border: none !important;
        background: linear-gradient(135deg, #2d1b69 0%, #1a1a2e 100%) !important;
        color: #fff !important; font-weight: 600 !important;
        font-size: 0.87rem !important; font-family: 'Inter', sans-serif !important;
        transition: all 0.2s; box-shadow: 0 2px 8px rgba(45,27,105,0.25) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3d2b89 0%, #2d2d4e 100%) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(45,27,105,0.4) !important;
    }

    section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e4e1db; }
    section[data-testid="stSidebar"] * { color: #64748b !important; }
    section[data-testid="stSidebar"] h3 { color: #1a1a2e !important; font-family: 'Playfair Display', serif !important; }
    section[data-testid="stSidebar"] strong { color: #1a1a2e !important; }
    section[data-testid="stSidebar"] .stButton > button {
        background: #f7f6f2 !important; color: #1a1a2e !important;
        border: 1px solid #e4e1db !important;
    }

    .stSelectbox > div > div {
        border-radius: 10px !important; border: 1.5px solid #e4e1db !important;
        background: #fff !important;
    }
    hr { border-color: #e4e1db !important; }
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
    label = "danger" if score < 50 else "warning" if score < 80 else "safe"
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
    "article_text": DEMO,
    "chat_history": [],
    "results": [],
    "analyzed": False,
    "selected_sentence": None,
    "rewrites": {},
    "research_result": None,
    "research_error": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

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

    if st.button("Load demo article", use_container_width=True):
        st.session_state.update({
            "article_text": DEMO,
            "results": [],
            "analyzed": False,
            "rewrites": {},
            "selected_sentence": None,
            "research_result": None,
            "research_error": None,
        })

    if st.button("Clear article", use_container_width=True):
        st.session_state.update({
            "article_text": "",
            "results": [],
            "analyzed": False,
            "rewrites": {},
            "selected_sentence": None,
            "research_result": None,
            "research_error": None,
        })

    if st.button("Clear chat", use_container_width=True):
        st.session_state.chat_history = []

    st.markdown("---")
    st.markdown("### How it works")
    st.markdown(
        "1. Paste article & **Analyze**\n"
        "2. **Click** a flagged sentence\n"
        "3. Click **Research latest evidence**\n"
        "4. Review status, confidence, and sources\n"
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
    <div class="topbar-tag">Editorial AI · Prototype</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <div class="page-title">Temporal Trust Checker</div>
    <div class="page-sub">Detect outdated claims, research the latest evidence on the web, and replace risky wording with source-backed updates.</div>
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
# TABS
# --------------------------------------------------
if True:
    inc, btnc = st.columns([5.5, 1], gap="small")
    with inc:
        article_text = st.text_area(
            "Article",
            value=st.session_state.article_text,
            height=110,
            label_visibility="collapsed",
            placeholder="Paste your article here...",
        )
        st.session_state.article_text = article_text

    with btnc:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("🔍 Analyze", use_container_width=True):
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
                    <div class="mval">{len(results)}</div>
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

        st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
        art_col, chat_col = st.columns([1.6, 1.0], gap="large")

        with art_col:
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

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                '<div class="slabel"><span class="slabel-dot"></span>Analysed Article — click a highlighted sentence</div>',
                unsafe_allow_html=True,
            )

            article_html = render_article(results, st.session_state.rewrites, st.session_state.selected_sentence)
            component_html = f"""<!DOCTYPE html><html><head><style>
                body{{margin:0;padding:1rem 1.2rem;font-family:'Inter',system-ui,sans-serif;font-size:0.97rem;line-height:2.2;color:#1a1a2e;background:transparent;}}
                .s-safe{{display:inline;color:#1a1a2e;}}
                .s-rewritten{{display:inline;background:#f0fdf4;color:#14532d;border:1.5px solid #86efac;border-radius:6px;padding:2px 8px;margin:1px;font-weight:500;}}
                .s-warning{{display:inline;background:#fffbeb;color:#78450a;border:1.5px solid #fcd34d;border-radius:6px;padding:2px 8px;margin:1px;cursor:pointer;transition:all 0.15s;}}
                .s-warning:hover{{background:#fef3c7;border-color:#f59e0b;box-shadow:0 2px 8px rgba(245,158,11,0.3);}}
                .s-danger{{display:inline;background:#fff1f1;color:#7f1d1d;border:1.5px solid #fca5a5;border-radius:6px;padding:2px 8px;margin:1px;cursor:pointer;transition:all 0.15s;}}
                .s-danger:hover{{background:#fee2e2;border-color:#ef4444;box-shadow:0 2px 8px rgba(239,68,68,0.3);}}
                .s-selected{{outline:2.5px solid #1a1a2e!important;outline-offset:2px;box-shadow:0 2px 12px rgba(26,26,46,0.22)!important;}}
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
                    "<div style='margin-top:0.8rem;font-size:0.88rem;color:#22c55e;font-weight:600;'>✅ All flagged sentences have been handled.</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

            sel_sentence = st.session_state.selected_sentence
            sel_item = next((r for r in results if r["sentence"] == sel_sentence), None)

            if sel_item:
                st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)
                st.markdown('<div class="card">', unsafe_allow_html=True)
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

                st.markdown("</div>", unsafe_allow_html=True)

        with chat_col:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="slabel"><span class="slabel-dot"></span>AI Assistant</div>', unsafe_allow_html=True)
            if st.session_state.chat_history:
                chat_html = '<div class="chat-box">'
                for msg in st.session_state.chat_history[-8:]:
                    if msg["role"] == "user":
                        chat_html += f'<div><div class="cn cn-r">You</div><div class="cb-user">{escape(msg["content"])}</div></div>'
                    else:
                        chat_html += f'<div><div class="cn cn-ai">TimeTravel AI</div><div class="cb-ai">{escape(msg["content"]).replace(chr(10), "<br>")}</div></div>'
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center;padding:1rem 0 0.5rem;font-size:0.84rem;color:#94a3b8;">Ask anything about your article</div>', unsafe_allow_html=True)

            st.markdown("<div class='chat-input-row'>", unsafe_allow_html=True)
            ci, cb = st.columns([5, 1], gap="small")
            with ci:
                user_msg = st.text_input("msg", placeholder="Ask a question...", label_visibility="collapsed", key="chat_in")
            with cb:
                send = st.button("Send", use_container_width=True, key="send_btn")
            st.markdown("</div>", unsafe_allow_html=True)

            if send and user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_msg.strip()})
                try:
                    with st.spinner(""):
                        reply = ask_editorial_chat(user_msg.strip(), st.session_state.article_text)
                except Exception as e:
                    reply = f"I couldn't complete that research request: {e}"
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

            st.markdown("<div class='chip-row'>", unsafe_allow_html=True)
            q1, q2 = st.columns(2)
            with q1:
                st.markdown("<div class='chip'>", unsafe_allow_html=True)
                if st.button("What's outdated?", use_container_width=True, key="qp1"):
                    question = "Which sentences in this article might be outdated, and why?"
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    try:
                        with st.spinner(""):
                            reply = ask_editorial_chat(question, st.session_state.article_text)
                    except Exception as e:
                        reply = f"I couldn't complete that request: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with q2:
                st.markdown("<div class='chip'>", unsafe_allow_html=True)
                if st.button("Suggest sources", use_container_width=True, key="qp2"):
                    question = "Suggest reputable sources to verify the key claims in this article."
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    try:
                        with st.spinner(""):
                            reply = ask_editorial_chat(question, st.session_state.article_text)
                    except Exception as e:
                        reply = f"I couldn't complete that request: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown(
            """
            <div style='text-align:center;padding:4rem 1rem;color:#94a3b8;'>
                <div style='font-size:2.5rem;margin-bottom:0.6rem;'>🕰️</div>
                <div style='font-size:1rem;font-weight:600;color:#64748b;margin-bottom:0.3rem;'>Paste an article and click Analyze</div>
                <div style='font-size:0.87rem;'>Flagged sentences will be highlighted in yellow and red.<br>Select one, research the latest evidence, and accept a source-backed rewrite.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==================================================
