import streamlit as st
import re
import datetime
from html import escape
from openai import OpenAI
import streamlit.components.v1 as components

st.set_page_config(
    page_title="TimeTravel · Editorial AI",
    page_icon="🕰️",
    layout="wide"
)

CURRENT_YEAR = datetime.datetime.now().year
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------------------------------
# STYLING
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f4f6f9; color: #1a1a2e; }
    .block-container { max-width: 1200px; padding-top: 0; padding-bottom: 3rem; }

    /* TOPBAR */
    .topbar {
        background: #1a1a2e;
        padding: 1rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -4rem -4rem 2rem -4rem;
        border-bottom: 3px solid #f0c95a;
    }
    .topbar-logo {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem; font-weight: 700; color: #fff;
    }
    .topbar-logo span { color: #f0c95a; }
    .topbar-tag {
        font-size: 0.68rem; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase;
        color: #94a3b8; background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 999px; padding: 0.28rem 0.8rem;
    }

    /* PAGE HEADER */
    .page-header { margin-bottom: 1.8rem; }
    .page-title {
        font-family: 'Playfair Display', serif;
        font-size: 2rem; font-weight: 700;
        color: #1a1a2e; margin-bottom: 0.3rem;
    }
    .page-sub { font-size: 0.9rem; color: #64748b; line-height: 1.6; }

    /* ARTICLE META HEADER */
    .article-meta-header {
        background: #1a1a2e;
        border-radius: 14px;
        padding: 1rem 1.4rem;
        margin-bottom: 0.8rem;
    }
    .article-meta-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.15rem; font-weight: 700;
        color: #ffffff; line-height: 1.4; margin-bottom: 0.25rem;
    }
    .article-meta-year {
        font-size: 0.78rem; font-weight: 600;
        color: #f0c95a; letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        background: #e2e8f0; border-radius: 12px;
        padding: 3px; gap: 3px; border: none;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px; padding: 0.45rem 1.3rem;
        font-weight: 600; font-size: 0.87rem;
        color: #64748b; background: transparent; border: none;
    }
    .stTabs [aria-selected="true"] { background: #1a1a2e !important; color: #fff !important; }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

    /* CARDS */
    .card {
        background: #fff;
        border: 1px solid #dde3ec;
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 2px 12px rgba(26,26,46,0.06);
    }
    .card-dark {
        background: #1a1a2e;
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
    }

    /* SLABEL */
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

    /* METRICS */
    .mcard {
        flex: 1; background: #fff;
        border: 1px solid #dde3ec;
        border-radius: 16px; padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(26,26,46,0.05);
    }
    .mcard-accent {
        flex: 1; background: #1a1a2e;
        border-radius: 16px; padding: 1rem 1.2rem;
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

    /* PROGRESS */
    .prog { background: rgba(255,255,255,0.12); border-radius: 999px; height: 5px; overflow: hidden; margin-top: 0.5rem; }
    .prog-bar { height: 5px; border-radius: 999px; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%); }

    /* ARTICLE */
    .article-display {
        background: #fafbfc;
        border: 1px solid #dde3ec;
        border-radius: 16px;
        padding: 1.3rem 1.5rem;
        line-height: 2.2;
        font-size: 0.97rem;
        color: #1a1a2e;
        min-height: 140px;
    }

    /* SENTENCE STYLES */
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
    a.s-warning, .s-warning {
        display: inline;
        background: #fffbeb; color: #78450a;
        border: 1.5px solid #fcd34d;
        border-radius: 6px;
        padding: 2px 8px; margin: 1px;
        text-decoration: none; cursor: pointer;
        transition: all 0.15s;
    }
    a.s-warning:hover { background: #fef3c7; border-color: #f59e0b; box-shadow: 0 2px 8px rgba(245,158,11,0.25); }
    a.s-danger, .s-danger {
        display: inline;
        background: #fff1f1; color: #7f1d1d;
        border: 1.5px solid #fca5a5;
        border-radius: 6px;
        padding: 2px 8px; margin: 1px;
        text-decoration: none; cursor: pointer;
        transition: all 0.15s;
    }
    a.s-danger:hover { background: #fee2e2; border-color: #ef4444; box-shadow: 0 2px 8px rgba(239,68,68,0.25); }
    .s-selected {
        outline: 2.5px solid #1a1a2e !important;
        outline-offset: 2px;
        box-shadow: 0 2px 12px rgba(26,26,46,0.22) !important;
    }

    /* SENTENCE BUTTONS */
    .sent-btn-danger button {
        background: #fff1f1 !important; color: #7f1d1d !important;
        border: 1.5px solid #fca5a5 !important;
        border-radius: 10px !important;
        font-size: 0.84rem !important; font-weight: 500 !important;
        text-align: left !important; justify-content: flex-start !important;
        padding: 0.5rem 0.9rem !important;
        transition: all 0.12s !important;
    }
    .sent-btn-danger button:hover { background: #fee2e2 !important; border-color: #ef4444 !important; }
    .sent-btn-warning button {
        background: #fffbeb !important; color: #78450a !important;
        border: 1.5px solid #fcd34d !important;
        border-radius: 10px !important;
        font-size: 0.84rem !important; font-weight: 500 !important;
        text-align: left !important; justify-content: flex-start !important;
        padding: 0.5rem 0.9rem !important;
        transition: all 0.12s !important;
    }
    .sent-btn-warning button:hover { background: #fef3c7 !important; border-color: #f59e0b !important; }
    .sent-btn-selected button {
        outline: 2px solid #1a1a2e !important;
        box-shadow: 0 2px 10px rgba(26,26,46,0.15) !important;
    }

    /* LEGEND */
    .legend { display: flex; gap: 0.45rem; flex-wrap: wrap; margin-top: 0.8rem; }
    .lpill {
        background: #fff; border: 1px solid #dde3ec;
        border-radius: 999px; padding: 0.28rem 0.75rem;
        font-size: 0.76rem; color: #64748b;
    }

    /* INSPECTOR PANEL */
    .inspector-empty {
        text-align: center; padding: 2.5rem 1rem;
        color: #94a3b8;
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
    .b-ai { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .b-done { background: #dcfce7; color: #166534; border: 1px solid #86efac; }

    /* AI RESULT */
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
        background: #f8fbff;
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 0.8rem 1rem;
    }
    .source-name {
        font-weight: 700; font-size: 0.9rem;
        color: #1d4ed8; margin-bottom: 0.2rem;
    }
    .source-desc { font-size: 0.82rem; color: #475569; line-height: 1.5; }

    /* CHAT */
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

    /* CHAT INPUT ROW */
    .chat-input-row {
        display: flex; align-items: center; gap: 0.5rem;
        background: #f1f4f8; border: 1.5px solid #dde3ec;
        border-radius: 14px; padding: 0.3rem 0.4rem 0.3rem 1rem;
        margin-top: 0.7rem;
    }

    /* QUICK CHIPS */
    .chip-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.6rem; }
    .chip button {
        background: #fff !important; color: #1a1a2e !important;
        border: 1.5px solid #dde3ec !important;
        border-radius: 999px !important;
        font-size: 0.78rem !important; font-weight: 500 !important;
        padding: 0.3rem 0.85rem !important;
    }
    .chip button:hover { background: #f1f4f8 !important; border-color: #94a3b8 !important; }

    /* CHANGES LOG */
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

    /* INPUTS */
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
        border: none !important; background: #1a1a2e !important;
        color: #fff !important; font-weight: 600 !important;
        font-size: 0.87rem !important; font-family: 'Inter', sans-serif !important;
        transition: all 0.15s;
    }
    .stButton > button:hover { background: #2d2d4e !important; transform: translateY(-1px); }

    /* SENTENCE BADGE BUTTONS */
    div.badge-danger .stButton > button {
        background: #fff1f1 !important; color: #7f1d1d !important;
        border: 1.5px solid #fca5a5 !important;
        border-radius: 999px !important;
        font-size: 0.78rem !important; font-weight: 700 !important;
        padding: 0.25rem 0.65rem !important;
        min-width: 2rem !important; transform: none !important;
    }
    div.badge-danger .stButton > button:hover { background: #fee2e2 !important; border-color: #ef4444 !important; }
    div.badge-warning .stButton > button {
        background: #fffbeb !important; color: #78450a !important;
        border: 1.5px solid #fcd34d !important;
        border-radius: 999px !important;
        font-size: 0.78rem !important; font-weight: 700 !important;
        padding: 0.25rem 0.65rem !important;
        min-width: 2rem !important; transform: none !important;
    }
    div.badge-warning .stButton > button:hover { background: #fef3c7 !important; border-color: #f59e0b !important; }
    div.badge-selected .stButton > button {
        outline: 2.5px solid #1a1a2e !important; outline-offset: 1px !important;
        font-weight: 800 !important;
    }

    /* SIDEBAR */
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

    /* HIDDEN SENTENCE SELECTOR INPUT */
    div.hidden-sent-input { visibility:hidden !important; height:0 !important; overflow:hidden !important; margin:0 !important; padding:0 !important; }
    div.hidden-sent-input * { height:0 !important; min-height:0 !important; padding:0 !important; margin:0 !important; border:none !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CORE FUNCTIONS
# --------------------------------------------------
def split_sentences(text):
    text = text.replace("\n", " ").strip()
    if not text: return []
    sentences = re.findall(r'[^.!?]+[.!?]+|[^.!?]+$', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_years(s):
    return [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', s)]

def contains_any(s, kws):
    return any(k in s.lower() for k in kws)

def has_number(s):
    return bool(re.search(r'\b\d+(?:\.\d+)?%?\b', s))

def clamp(v, lo, hi): return max(lo, min(v, hi))

TIME_KW = ["currently","recently","today","now","next year","this year","this month",
           "this week","this summer","this winter","this quarter","will","planned",
           "expected to","forecast","soon","upcoming"]
NUM_KW  = ["inflation","price","prices","market share","interest rate","unemployment",
           "gdp","leader","sales","revenue","ranked","ranking"]

def analyze_sentence(sentence):
    score = 100; reasons = []; lower = sentence.lower()
    years = extract_years(sentence)
    for year in years:
        age = CURRENT_YEAR - year
        if age >= 4:   score -= 45; reasons.append(f"References {year} ({age} years ago) — likely outdated.")
        elif age >= 2: score -= 28; reasons.append(f"References {year} — may need a freshness check.")
        elif age >= 1: score -= 12; reasons.append(f"Date from {year} adds temporal sensitivity.")
    if contains_any(sentence, TIME_KW):
        score -= 22; reasons.append("Uses time-sensitive language like 'currently' or future-oriented wording.")
    if contains_any(sentence, NUM_KW) and has_number(sentence):
        score -= 18; reasons.append("Numerical claim on a topic that changes over time.")
    if ("next year" in lower or "will" in lower) and any(y < CURRENT_YEAR for y in years):
        score -= 18; reasons.append("Future language combined with a past date — strongly suggests it is outdated.")
    score = clamp(score, 5, 100)
    label = "danger" if score < 50 else "warning" if score < 80 else "safe"
    explanation = " ".join(reasons) if reasons else "No strong signs of temporal risk detected."
    return {"sentence": sentence, "score": score, "label": label, "explanation": explanation, "years": years}

def render_article(results, rewrites, sel_original=None):
    """Render article with clickable highlighted sentences (via data-sent-idx)."""
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
# OPENAI
# --------------------------------------------------
def ai_rewrite(sentence):
    prompt = f"""You are an editorial assistant helping journalists update outdated news articles.

The following sentence has been flagged as potentially outdated or time-sensitive:
"{sentence}"

Your tasks:
1. Write an improved, accurate replacement sentence in neutral journalistic language. Remove vague time references and outdated claims.
2. Suggest ONE specific reputable source article the journalist should check to verify the updated claim.

Respond EXACTLY in this format with no extra text:
REWRITE: [the new sentence]
SOURCE_NAME: [publication name, e.g. Reuters, Eurostat, BBC News]
SOURCE_ARTICLE: [title of a specific article or report to look for, or "N/A"]
SOURCE_AUTHOR: [author name if known, or "N/A"]
SOURCE_YEAR: [year of the recommended source, or "N/A"]
SOURCE_WHAT: [one sentence explaining what to look for there]"""

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400, temperature=0.4
    )
    text = r.choices[0].message.content.strip()
    rewrite, source_name, source_article, source_author, source_year, source_what = "", "", "", "", "", ""
    for line in text.split("\n"):
        if line.startswith("REWRITE:"): rewrite = line.replace("REWRITE:", "").strip()
        elif line.startswith("SOURCE_NAME:"): source_name = line.replace("SOURCE_NAME:", "").strip()
        elif line.startswith("SOURCE_ARTICLE:"): source_article = line.replace("SOURCE_ARTICLE:", "").strip()
        elif line.startswith("SOURCE_AUTHOR:"): source_author = line.replace("SOURCE_AUTHOR:", "").strip()
        elif line.startswith("SOURCE_YEAR:"): source_year = line.replace("SOURCE_YEAR:", "").strip()
        elif line.startswith("SOURCE_WHAT:"): source_what = line.replace("SOURCE_WHAT:", "").strip()
    return {"rewrite": rewrite, "source_name": source_name, "source_article": source_article,
            "source_author": source_author, "source_year": source_year, "source_what": source_what}

def ai_chat(messages, article):
    sys = f"""You are TimeTravel, an AI editorial assistant for a news agency.
Help journalists verify, update, and fact-check articles.

Article being edited:
---
{article.strip() if article.strip() else "No article pasted yet."}
---
Be concise and specific. Name real reputable sources."""
    msgs = [{"role": "system", "content": sys}] + [{"role": m["role"], "content": m["content"]} for m in messages]
    r = client.chat.completions.create(model="gpt-4o-mini", messages=msgs, max_tokens=600, temperature=0.5)
    return r.choices[0].message.content.strip()

# --------------------------------------------------
# DEMO
# --------------------------------------------------
DEMO = ("In 2021, the company announced that it would launch its electric delivery fleet next year. "
        "The CEO currently says the business is the market leader in battery logistics. "
        "Inflation is 2.1% and energy prices are expected to fall this summer. "
        "The company opened three hubs in Germany in 2023. "
        "Analysts recently described the expansion strategy as highly effective. "
        "The government will introduce a subsidy program in 2024 to support infrastructure upgrades.")

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
for k, v in [
    ("article_text", DEMO), ("chat_history", []),
    ("changes_log", []), ("results", []), ("analyzed", False),
    ("selected_sentence", None), ("rewrites", {}), ("ai_result", None),
]:
    if k not in st.session_state: st.session_state[k] = v

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 🕰️ TimeTravel")
    st.markdown("<div style='font-size:0.82rem;color:#94a3b8;margin-bottom:1.2rem;'>Editorial AI for temporal credibility.</div>", unsafe_allow_html=True)
    if st.button("Load demo article", use_container_width=True):
        st.session_state.update({"article_text": DEMO, "results": [], "analyzed": False,
                                  "rewrites": {}, "selected_sentence": None, "ai_result": None})
    if st.button("Clear article", use_container_width=True):
        st.session_state.update({"article_text": "", "results": [], "analyzed": False,
                                  "rewrites": {}, "selected_sentence": None, "ai_result": None})
    if st.button("Clear chat", use_container_width=True):
        st.session_state.chat_history = []
    if st.button("Clear changes", use_container_width=True):
        st.session_state.changes_log = []
        st.session_state.rewrites = {}
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("1. Paste article & **Analyze**\n2. **Click** a flagged sentence\n3. Click **Rewrite** — AI replaces it\n4. Repeat for each sentence\n5. See all changes in **Changes Log**")
    st.markdown("---")
    st.markdown("**🟡 Yellow** — review recommended  \n**🔴 Red** — likely outdated  \n**🟢 Green** — rewritten by AI")

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
    <div class="page-sub">Detect outdated claims, select flagged sentences, and get AI-powered rewrites with verified sources.</div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2 = st.tabs(["📋  Analyze & Rewrite", "📝  Changes Log"])

# ==================================================
# TAB 1
# ==================================================
with tab1:

    # INPUT
    inc, btnc = st.columns([5.5, 1], gap="small")
    with inc:
        article_text = st.text_area("Article", value=st.session_state.article_text,
                                    height=110, label_visibility="collapsed",
                                    placeholder="Paste your article here...")
        st.session_state.article_text = article_text
    with btnc:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("🔍 Analyze", use_container_width=True):
            if article_text.strip():
                sents = split_sentences(article_text)
                st.session_state.results = [analyze_sentence(s) for s in sents]
                st.session_state.analyzed = True
                st.session_state.selected_sentence = None
                st.session_state.ai_result = None
                st.session_state.rewrites = {}

    results = st.session_state.results
    risky = [r for r in results if r["label"] != "safe" and r["sentence"] not in st.session_state.rewrites]

    if st.session_state.analyzed and results:
        freshness = round(sum(r["score"] for r in results) / len(results))
        rewrites_done = len(st.session_state.rewrites)

        # METRICS
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(f"""<div class="mcard-accent">
                <div class="mval mval-gold">{freshness}</div>
                <div class="mlbl mlbl-light">Freshness Score</div>
                <div class="prog">
                    <div class="prog-bar" style="width:{freshness}%;"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""<div class="mcard">
                <div class="mval mval-red">{len(risky)}</div>
                <div class="mlbl">Still Flagged</div>
            </div>""", unsafe_allow_html=True)
        with mc3:
            st.markdown(f"""<div class="mcard">
                <div class="mval">{len(results)}</div>
                <div class="mlbl">Total Sentences</div>
            </div>""", unsafe_allow_html=True)
        with mc4:
            st.markdown(f"""<div class="mcard">
                <div class="mval mval-green">{rewrites_done}</div>
                <div class="mlbl">Rewritten</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

        # MAIN LAYOUT — article left, chat right
        art_col, chat_col = st.columns([1.6, 1.0], gap="large")

        with art_col:
            # Hidden buttons — JS clicks these to trigger Streamlit reruns reliably
            st.markdown('<div style="visibility:hidden;position:absolute;width:0;height:0;overflow:hidden;">', unsafe_allow_html=True)
            btn_clicks = [st.button(f"§{i}§", key=f"hbtn_{i}") for i in range(len(results))]
            st.markdown('</div>', unsafe_allow_html=True)

            for i, clicked in enumerate(btn_clicks):
                if clicked and results[i]["label"] != "safe" and results[i]["sentence"] not in st.session_state.rewrites:
                    if results[i]["sentence"] != st.session_state.selected_sentence:
                        st.session_state.selected_sentence = results[i]["sentence"]
                    else:
                        st.session_state.selected_sentence = None
                    st.session_state.ai_result = None
                    st.rerun()

            # ARTICLE
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="slabel"><span class="slabel-dot"></span>Analysed Article — click a highlighted sentence</div>', unsafe_allow_html=True)

            article_html = render_article(results, st.session_state.rewrites, st.session_state.selected_sentence)
            component_html = f"""<!DOCTYPE html><html><head><style>
  body{{margin:0;padding:1rem 1.2rem;font-family:'Inter',system-ui,sans-serif;
       font-size:0.97rem;line-height:2.2;color:#1a1a2e;background:transparent;}}
  .s-safe{{display:inline;color:#1a1a2e;}}
  .s-rewritten{{display:inline;background:#f0fdf4;color:#14532d;border:1.5px solid #86efac;border-radius:6px;padding:2px 8px;margin:1px;font-weight:500;}}
  .s-warning{{display:inline;background:#fffbeb;color:#78450a;border:1.5px solid #fcd34d;border-radius:6px;padding:2px 8px;margin:1px;cursor:pointer;transition:all 0.15s;}}
  .s-warning:hover{{background:#fef3c7;border-color:#f59e0b;box-shadow:0 2px 8px rgba(245,158,11,0.3);}}
  .s-danger{{display:inline;background:#fff1f1;color:#7f1d1d;border:1.5px solid #fca5a5;border-radius:6px;padding:2px 8px;margin:1px;cursor:pointer;transition:all 0.15s;}}
  .s-danger:hover{{background:#fee2e2;border-color:#ef4444;box-shadow:0 2px 8px rgba(239,68,68,0.3);}}
  .s-selected{{outline:2.5px solid #1a1a2e!important;outline-offset:2px;box-shadow:0 2px 12px rgba(26,26,46,0.22)!important;}}
</style></head><body>{article_html}<script>
  document.querySelectorAll('[data-sent-idx]').forEach(function(el){{
    el.addEventListener('click',function(){{
      var idx=this.getAttribute('data-sent-idx');
      try{{
        var btns=window.parent.document.querySelectorAll('button');
        for(var b=0;b<btns.length;b++){{
          if(btns[b].innerText.trim()==='§'+idx+'§'){{
            btns[b].click();
            return;
          }}
        }}
      }}catch(e){{}}
    }});
  }});
</script></body></html>"""
            components.html(component_html, height=260, scrolling=True)

            st.markdown("""<div class="legend">
                <div class="lpill">🟡 Yellow — review recommended</div>
                <div class="lpill">🔴 Red — likely outdated</div>
                <div class="lpill">🟢 Green — rewritten</div>
            </div>""", unsafe_allow_html=True)
            if not risky:
                st.markdown("<div style='margin-top:0.8rem;font-size:0.88rem;color:#22c55e;font-weight:600;'>✅ All flagged sentences have been rewritten!</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # INSPECTOR — pops up below article when sentence is selected
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
                    st.markdown(f"<div style='text-align:right;font-family:Playfair Display,serif;font-size:1.9rem;font-weight:700;color:{sc_color};'>{sel_item['score']}</div>", unsafe_allow_html=True)

                st.markdown(f"<div class='inspector-sentence {q_cls}'>{escape(sel_item['sentence'])}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.84rem;color:#64748b;line-height:1.6;margin-bottom:1rem;'>{sel_item['explanation']}</div>", unsafe_allow_html=True)

                if st.button("✨  Rewrite this sentence", use_container_width=True, key="rewrite_btn"):
                    with st.spinner("AI is rewriting..."):
                        st.session_state.ai_result = ai_rewrite(sel_item["sentence"])

                if st.session_state.ai_result:
                    res = st.session_state.ai_result
                    st.markdown('<div class="badge b-ai">✨ AI Suggestion</div>', unsafe_allow_html=True)
                    if res.get("rewrite"):
                        st.markdown('<div class="slabel">New sentence</div>', unsafe_allow_html=True)
                        st.markdown(f"<div class='ai-new-sentence'>{escape(res['rewrite'])}</div>", unsafe_allow_html=True)
                    if res.get("source_name"):
                        st.markdown('<div class="slabel">Verify here</div>', unsafe_allow_html=True)
                        src_article = res.get("source_article", "")
                        src_author  = res.get("source_author", "")
                        src_year    = res.get("source_year", "")
                        meta_parts = []
                        if src_author and src_author != "N/A": meta_parts.append(f"<span style='font-weight:600;'>{escape(src_author)}</span>")
                        if src_year   and src_year   != "N/A": meta_parts.append(f"<span style='color:#64748b;'>{escape(src_year)}</span>")
                        meta_line = " · ".join(meta_parts)
                        article_line = (f"<div style='font-size:0.87rem;font-style:italic;color:#1a1a2e;margin:0.25rem 0;'>&ldquo;{escape(src_article)}&rdquo;</div>" if src_article and src_article != "N/A" else "")
                        st.markdown(f"""<div class="source-card">
                            <div class="source-name">→ {escape(res['source_name'])}</div>
                            {article_line}
                            <div style='font-size:0.78rem;color:#64748b;margin-top:0.1rem;'>{meta_line}</div>
                            <div class="source-desc" style='margin-top:0.4rem;'>{escape(res.get('source_what',''))}</div>
                        </div>""", unsafe_allow_html=True)
                    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                    if st.button("✅  Accept & replace sentence", use_container_width=True, key="accept_btn"):
                        orig = sel_item["sentence"]
                        new = res["rewrite"]
                        st.session_state.rewrites[orig] = new
                        st.session_state.changes_log.append({
                            "original": orig, "rewrite": new,
                            "source_name": res.get("source_name",""),
                            "source_article": res.get("source_article",""),
                            "source_author": res.get("source_author",""),
                            "source_year": res.get("source_year",""),
                            "source_what": res.get("source_what",""),
                            "label": sel_item["label"], "score": sel_item["score"]
                        })
                        st.session_state.selected_sentence = None
                        st.session_state.ai_result = None
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with chat_col:
            # CHAT
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="slabel"><span class="slabel-dot"></span>AI Assistant</div>', unsafe_allow_html=True)
            if st.session_state.chat_history:
                chat_html = '<div class="chat-box">'
                for msg in st.session_state.chat_history[-8:]:
                    if msg["role"] == "user":
                        chat_html += f'<div><div class="cn cn-r">You</div><div class="cb-user">{escape(msg["content"])}</div></div>'
                    else:
                        chat_html += f'<div><div class="cn cn-ai">TimeTravel AI</div><div class="cb-ai">{msg["content"].replace(chr(10),"<br>")}</div></div>'
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
                with st.spinner(""):
                    reply = ai_chat(st.session_state.chat_history, st.session_state.article_text)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()
            st.markdown("<div class='chip-row'>", unsafe_allow_html=True)
            q1, q2 = st.columns(2)
            with q1:
                st.markdown("<div class='chip'>", unsafe_allow_html=True)
                if st.button("What's outdated?", use_container_width=True, key="qp1"):
                    st.session_state.chat_history.append({"role": "user", "content": "Which sentences in this article might be outdated?"})
                    with st.spinner(""):
                        reply = ai_chat(st.session_state.chat_history, st.session_state.article_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with q2:
                st.markdown("<div class='chip'>", unsafe_allow_html=True)
                if st.button("Suggest sources", use_container_width=True, key="qp2"):
                    st.session_state.chat_history.append({"role": "user", "content": "Suggest reputable sources to verify the key claims in this article."})
                    with st.spinner(""):
                        reply = ai_chat(st.session_state.chat_history, st.session_state.article_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style='text-align:center;padding:4rem 1rem;color:#94a3b8;'>
            <div style='font-size:2.5rem;margin-bottom:0.6rem;'>🕰️</div>
            <div style='font-size:1rem;font-weight:600;color:#64748b;margin-bottom:0.3rem;'>Paste an article and click Analyze</div>
            <div style='font-size:0.87rem;'>Flagged sentences will be highlighted in yellow and red.<br>Select one, get an AI rewrite, and accept it to replace the original.</div>
        </div>""", unsafe_allow_html=True)

# ==================================================
# TAB 2 — CHANGES LOG
# ==================================================
with tab2:
    st.markdown('<div class="page-title" style="font-size:1.7rem;margin-bottom:0.3rem;">Changes Log</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub" style="margin-bottom:1.5rem;">{len(st.session_state.changes_log)} sentence(s) rewritten this session.</div>', unsafe_allow_html=True)

    if st.session_state.changes_log:
        for i, c in enumerate(st.session_state.changes_log):
            icon = "🔴" if c["label"] == "danger" else "🟡"
            sc_color = "#ef4444" if c["score"] < 50 else "#f59e0b"
            st.markdown(f"""
            <div class="clog-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.9rem;">
                    <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:600;color:#1a1a2e;">Sentence {i+1} {icon}</div>
                    <div style="font-size:0.73rem;font-weight:700;color:{sc_color};background:#fafaf7;border:1px solid #e4e1db;border-radius:999px;padding:0.2rem 0.65rem;">Original score: {c['score']}</div>
                </div>
                <div class="diff-lbl" style="color:#ef4444;">Original</div>
                <div class="diff-b">{escape(c['original'])}</div>
                <div class="diff-lbl" style="color:#16a34a;margin-top:0.5rem;">Rewritten</div>
                <div class="diff-a">{escape(c['rewrite'])}</div>
            """, unsafe_allow_html=True)
            if c.get("source_name"):
                src_art = c.get("source_article", "")
                src_aut = c.get("source_author", "")
                src_yr  = c.get("source_year", "")
                art_line = f"<div style='font-size:0.86rem;font-style:italic;color:#1a1a2e;margin:0.25rem 0;'>&ldquo;{escape(src_art)}&rdquo;</div>" if src_art and src_art != "N/A" else ""
                meta_bits = []
                if src_aut and src_aut != "N/A": meta_bits.append(f"<strong>{escape(src_aut)}</strong>")
                if src_yr  and src_yr  != "N/A": meta_bits.append(escape(src_yr))
                meta_str = " · ".join(meta_bits)
                st.markdown(f"""
                <div style="margin-top:0.8rem;">
                    <div class="diff-lbl" style="color:#1d4ed8;">Suggested source</div>
                    <div style="background:#f8fbff;border:1px solid #bfdbfe;border-radius:12px;padding:0.7rem 0.9rem;margin-top:0.3rem;">
                        <div style="font-weight:700;font-size:0.88rem;color:#1d4ed8;">→ {escape(c['source_name'])}</div>
                        {art_line}
                        <div style="font-size:0.78rem;color:#64748b;margin-top:0.1rem;">{meta_str}</div>
                        <div style="font-size:0.81rem;color:#475569;margin-top:0.3rem;">{escape(c.get('source_what',''))}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:center;padding:4rem 1rem;color:#94a3b8;'>
            <div style='font-size:2.5rem;margin-bottom:0.6rem;'>📝</div>
            <div style='font-size:1rem;font-weight:600;color:#64748b;margin-bottom:0.3rem;'>No changes yet</div>
            <div style='font-size:0.87rem;'>Go to Analyze & Rewrite, select a flagged sentence,<br>get an AI rewrite, and click Accept — it will appear here.</div>
        </div>""", unsafe_allow_html=True)