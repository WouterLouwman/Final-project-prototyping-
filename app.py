import streamlit as st
import re
import datetime
from html import escape
from openai import OpenAI

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

    .stApp { background: #fafaf7; color: #1a1a2e; }
    .block-container { max-width: 1480px; padding-top: 0; padding-bottom: 2rem; }

    /* TOP NAV BAR */
    .topbar {
        background: #1a1a2e;
        padding: 0.85rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -1rem -1rem 1.5rem -1rem;
        border-bottom: 3px solid #f0c95a;
    }
    .topbar-logo {
        font-family: 'Playfair Display', serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: #fff;
        letter-spacing: -0.01em;
    }
    .topbar-logo span { color: #f0c95a; }
    .topbar-tag {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #94a3b8;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 999px;
        padding: 0.25rem 0.75rem;
    }

    /* PAGE TITLE */
    .page-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        line-height: 1.15;
        margin-bottom: 0.3rem;
    }
    .page-sub {
        font-size: 0.92rem;
        color: #64748b;
        line-height: 1.6;
        max-width: 560px;
        margin-bottom: 1.4rem;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        background: #efefeb;
        border-radius: 12px;
        padding: 3px;
        gap: 3px;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px;
        padding: 0.45rem 1.3rem;
        font-weight: 600;
        font-size: 0.87rem;
        color: #64748b;
        background: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: #1a1a2e !important;
        color: #fff !important;
    }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

    /* CARDS */
    .card {
        background: #ffffff;
        border: 1px solid #e8e5e0;
        border-radius: 20px;
        padding: 1.3rem 1.4rem;
        box-shadow: 0 2px 12px rgba(26,26,46,0.05);
    }
    .card-accent {
        background: #1a1a2e;
        border-radius: 20px;
        padding: 1.3rem 1.4rem;
    }

    /* METRIC CARDS */
    .metric-row { display: flex; gap: 0.8rem; margin-bottom: 1.2rem; }
    .metric-card {
        flex: 1;
        background: #fff;
        border: 1px solid #e8e5e0;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 10px rgba(26,26,46,0.04);
    }
    .metric-card-accent {
        flex: 1;
        background: #1a1a2e;
        border-radius: 16px;
        padding: 1rem 1.2rem;
    }
    .metric-val {
        font-family: 'Playfair Display', serif;
        font-size: 2.4rem;
        font-weight: 700;
        line-height: 1;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .metric-val-light {
        font-family: 'Playfair Display', serif;
        font-size: 2.4rem;
        font-weight: 700;
        line-height: 1;
        color: #f0c95a;
        margin-bottom: 0.2rem;
    }
    .metric-lbl {
        font-size: 0.71rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #94a3b8;
    }
    .metric-lbl-light {
        font-size: 0.71rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #4a5568;
    }

    /* SECTION LABELS */
    .slabel {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        color: #94a3b8;
        margin-bottom: 0.5rem;
    }

    /* PROGRESS */
    .prog-shell {
        background: #efefeb;
        border-radius: 999px;
        height: 6px;
        overflow: hidden;
        margin-top: 0.4rem;
    }
    .prog-bar {
        height: 6px;
        border-radius: 999px;
        background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%);
    }

    /* ARTICLE BOX */
    .article-box {
        background: #fdfcfa;
        border: 1px solid #e8e5e0;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        min-height: 160px;
        line-height: 2.25;
        font-size: 0.97rem;
        color: #1a1a2e;
        font-family: 'Inter', sans-serif;
    }

    /* SENTENCE STYLES */
    .s-safe { display: inline; color: #1a1a2e; }
    .s-warning {
        display: inline;
        background: #fffbeb;
        color: #78450a;
        border: 1.5px solid #fde68a;
        border-radius: 6px;
        padding: 2px 7px;
        margin: 1px;
        cursor: pointer;
        transition: all 0.12s;
    }
    .s-warning:hover { background: #fef3c7; box-shadow: 0 2px 8px rgba(245,158,11,0.25); }
    .s-danger {
        display: inline;
        background: #fff5f5;
        color: #7f1d1d;
        border: 1.5px solid #fca5a5;
        border-radius: 6px;
        padding: 2px 7px;
        margin: 1px;
        cursor: pointer;
        transition: all 0.12s;
    }
    .s-danger:hover { background: #fee2e2; box-shadow: 0 2px 8px rgba(239,68,68,0.25); }
    .s-selected { outline: 2.5px solid #1a1a2e !important; outline-offset: 2px; }

    /* LEGEND */
    .legend { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.8rem; }
    .legend-item {
        background: #fff;
        border: 1px solid #e8e5e0;
        border-radius: 999px;
        padding: 0.3rem 0.8rem;
        font-size: 0.78rem;
        color: #64748b;
    }

    /* INSPECTOR */
    .inspector-quote {
        background: #fdfcfa;
        border-left: 4px solid #e8e5e0;
        border-radius: 0 14px 14px 0;
        padding: 0.9rem 1.1rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1a1a2e;
        font-style: italic;
        margin-bottom: 1rem;
    }
    .inspector-quote-danger { border-left-color: #ef4444; }
    .inspector-quote-warning { border-left-color: #f59e0b; }

    .badge {
        display: inline-block;
        border-radius: 999px;
        padding: 0.26rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
    }
    .badge-danger { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .badge-warning { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-ai { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-done { background: #dcfce7; color: #166534; border: 1px solid #86efac; }

    /* AI RESULT */
    .ai-box {
        background: #f0f7ff;
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        color: #1e3a5f;
        line-height: 1.7;
        font-size: 0.93rem;
    }
    .source-list {
        background: #f8fbff;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 0.5rem 0.9rem;
    }
    .source-row {
        font-size: 0.86rem;
        color: #1d4ed8;
        padding: 0.28rem 0;
        border-bottom: 1px solid #e0eeff;
    }
    .source-row:last-child { border-bottom: none; }

    /* CHAT */
    .chat-scroll {
        display: flex;
        flex-direction: column;
        gap: 0.7rem;
        max-height: 300px;
        overflow-y: auto;
        padding: 0.2rem 0;
    }
    .cbubble-user {
        background: #1a1a2e;
        color: #fff;
        border-radius: 16px 16px 4px 16px;
        padding: 0.65rem 0.9rem;
        font-size: 0.86rem;
        line-height: 1.55;
        max-width: 86%;
        margin-left: auto;
    }
    .cbubble-ai {
        background: #fff;
        border: 1px solid #e8e5e0;
        color: #1a1a2e;
        border-radius: 16px 16px 16px 4px;
        padding: 0.65rem 0.9rem;
        font-size: 0.86rem;
        line-height: 1.55;
        max-width: 86%;
        box-shadow: 0 1px 6px rgba(26,26,46,0.06);
    }
    .cname {
        font-size: 0.63rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-bottom: 0.2rem;
    }
    .cname-right { text-align: right; }

    /* CHANGES LOG */
    .change-card {
        background: #fff;
        border: 1px solid #e8e5e0;
        border-radius: 18px;
        padding: 1.2rem 1.3rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(26,26,46,0.04);
    }
    .diff-before {
        background: #fff5f5;
        border-left: 4px solid #ef4444;
        border-radius: 0 10px 10px 0;
        padding: 0.7rem 0.9rem;
        font-size: 0.89rem;
        color: #7f1d1d;
        line-height: 1.65;
        margin-bottom: 0.5rem;
    }
    .diff-after {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        border-radius: 0 10px 10px 0;
        padding: 0.7rem 0.9rem;
        font-size: 0.89rem;
        color: #14532d;
        line-height: 1.65;
    }
    .diff-label {
        font-size: 0.67rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-bottom: 0.3rem;
    }

    /* INPUTS */
    textarea, .stTextArea textarea {
        background: #fff !important;
        color: #1a1a2e !important;
        border-radius: 12px !important;
        border: 1.5px solid #e8e5e0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.94rem !important;
    }
    .stTextInput input {
        background: #fff !important;
        color: #1a1a2e !important;
        border-radius: 12px !important;
        border: 1.5px solid #e8e5e0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stButton > button {
        border-radius: 10px !important;
        padding: 0.52rem 1.1rem !important;
        border: none !important;
        background: #1a1a2e !important;
        color: #fff !important;
        font-weight: 600 !important;
        font-size: 0.86rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: background 0.15s, transform 0.1s;
    }
    .stButton > button:hover {
        background: #2d2d4e !important;
        transform: translateY(-1px);
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid #e8e5e0;
    }
    section[data-testid="stSidebar"] * { color: #64748b !important; }
    section[data-testid="stSidebar"] h3 { color: #1a1a2e !important; }
    section[data-testid="stSidebar"] strong { color: #1a1a2e !important; }
    section[data-testid="stSidebar"] .stButton > button {
        background: #f5f4f1 !important;
        color: #1a1a2e !important;
        border: 1px solid #e8e5e0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #efefeb !important;
    }

    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1.5px solid #e8e5e0 !important;
        background: #fff !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stMetricValue"] { font-family: 'Playfair Display', serif !important; }
    hr { border-color: #e8e5e0 !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.55rem; }

    /* EMPTY STATE */
    .empty-state {
        text-align: center;
        padding: 3.5rem 1rem;
        color: #94a3b8;
    }
    .empty-icon { font-size: 2.8rem; margin-bottom: 0.6rem; }
    .empty-title { font-size: 1rem; font-weight: 600; color: #64748b; margin-bottom: 0.3rem; }
    .empty-sub { font-size: 0.85rem; }

    /* DECORATIVE DOTS */
    .dot-accent {
        display: inline-block;
        width: 8px; height: 8px;
        background: #f0c95a;
        border-radius: 50%;
        margin-right: 0.4rem;
        vertical-align: middle;
    }
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
    lower = s.lower()
    return any(k in lower for k in kws)

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
        score -= 22; reasons.append("Uses time-sensitive language like 'currently' or 'will'.")
    if contains_any(sentence, NUM_KW) and has_number(sentence):
        score -= 18; reasons.append("Numerical claim on a topic that changes over time.")
    if ("next year" in lower or "will" in lower) and any(y < CURRENT_YEAR for y in years):
        score -= 18; reasons.append("Future language combined with a past date — strongly outdated.")
    score = clamp(score, 5, 100)
    label = "danger" if score < 50 else "warning" if score < 80 else "safe"
    explanation = " ".join(reasons) if reasons else "No strong signs of temporal risk detected."
    return {"sentence": sentence, "score": score, "label": label, "explanation": explanation, "years": years}

def render_article(results, sel_idx=None):
    parts = []; risky_i = 0
    for item in results:
        txt = escape(item["sentence"])
        if item["label"] == "safe":
            parts.append(f"<span class='s-safe'>{txt} </span>")
        else:
            sel = " s-selected" if risky_i == sel_idx else ""
            parts.append(f"<span class='s-{item['label']}{sel}'>{txt}</span> ")
            risky_i += 1
    return "".join(parts)

# --------------------------------------------------
# OPENAI
# --------------------------------------------------
def ai_rewrite(sentence):
    prompt = f"""You are an editorial assistant helping journalists update outdated news articles.

Flagged sentence: \"{sentence}\"

1. Rewrite it removing or flagging the outdated claim, in neutral journalistic language.
2. Suggest 2-3 specific reputable sources to verify current information.

Respond EXACTLY in this format:
REWRITE: [rewritten sentence]
SOURCES: [source 1] | [source 2] | [source 3]"""
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=300, temperature=0.4
    )
    text = r.choices[0].message.content.strip()
    rewrite, sources = "", []
    for line in text.split("\n"):
        if line.startswith("REWRITE:"): rewrite = line.replace("REWRITE:","").strip()
        elif line.startswith("SOURCES:"): sources = [s.strip() for s in line.replace("SOURCES:","").strip().split("|") if s.strip()]
    return {"rewrite": rewrite, "sources": sources}

def ai_chat(messages, article):
    sys = f"""You are TimeTravel, an AI editorial assistant for a news agency.
Help journalists verify, update, and fact-check articles.

Article being edited:
---
{article.strip() if article.strip() else "No article pasted yet."}
---
Be concise and specific. Name real reputable sources."""
    msgs = [{"role":"system","content":sys}] + [{"role":m["role"],"content":m["content"]} for m in messages]
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
for k, v in [("article_text", DEMO), ("chat_history", []), ("ai_results", {}),
             ("changes_log", []), ("sel_idx", 0), ("results", []), ("analyzed", False)]:
    if k not in st.session_state: st.session_state[k] = v

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 🕰️ TimeTravel")
    st.markdown("<div style='font-size:0.82rem;color:#94a3b8;margin-bottom:1.2rem;'>Editorial AI for temporal credibility.</div>", unsafe_allow_html=True)
    if st.button("Load demo article", use_container_width=True):
        st.session_state.update({"article_text": DEMO, "results": [], "analyzed": False, "ai_results": {}, "sel_idx": 0})
    if st.button("Clear article", use_container_width=True):
        st.session_state.update({"article_text": "", "results": [], "analyzed": False, "ai_results": {}, "sel_idx": 0})
    if st.button("Clear chat", use_container_width=True):
        st.session_state.chat_history = []
    if st.button("Clear changes log", use_container_width=True):
        st.session_state.changes_log = []
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("1. Paste article & analyze\n2. Click a flagged sentence\n3. Get AI rewrite + sources\n4. Review all changes in tab 2")
    st.markdown("---")
    st.markdown("**🟡 Yellow** — review recommended  \n**🔴 Red** — likely outdated")

# --------------------------------------------------
# TOP NAV
# --------------------------------------------------
st.markdown("""
<div class="topbar">
    <div class="topbar-logo">Time<span>Travel</span></div>
    <div class="topbar-tag">Editorial AI · Prototype</div>
</div>
""", unsafe_allow_html=True)

# PAGE HEADER
st.markdown("""
<div class="page-title">Temporal Trust Checker</div>
<div class="page-sub">Detect outdated claims in news articles. Get AI-powered rewrites, source suggestions, and editorial support — all in one workspace.</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2 = st.tabs(["📋  Analyze & Edit", "📝  Changes Log"])

# ==================================================
# TAB 1
# ==================================================
with tab1:

    # INPUT ROW
    in1, in2 = st.columns([5.5, 1], gap="small")
    with in1:
        article_text = st.text_area("Article", value=st.session_state.article_text,
                                    height=115, label_visibility="collapsed",
                                    placeholder="Paste your article here and click Analyze...")
        st.session_state.article_text = article_text
    with in2:
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        analyze_clicked = st.button("🔍 Analyze", use_container_width=True)
        st.markdown("<div style='font-size:0.72rem;color:#94a3b8;text-align:center;margin-top:0.4rem;'>Analyze<br>article</div>", unsafe_allow_html=True)

    if analyze_clicked and article_text.strip():
        sents = split_sentences(article_text)
        st.session_state.results = [analyze_sentence(s) for s in sents]
        st.session_state.analyzed = True
        st.session_state.sel_idx = 0
        st.session_state.ai_results = {}

    results = st.session_state.results
    risky = [r for r in results if r["label"] != "safe"]

    if st.session_state.analyzed and results:
        freshness = round(sum(r["score"] for r in results) / len(results))
        score_color = "#ef4444" if freshness < 50 else "#f59e0b" if freshness < 75 else "#22c55e"

        # METRICS
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="metric-card-accent">
                <div class="metric-val-light">{freshness}</div>
                <div class="metric-lbl-light">Freshness Score</div>
                <div class="prog-shell" style="background:rgba(255,255,255,0.1);">
                    <div class="prog-bar" style="width:{freshness}%;"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-val" style="color:#ef4444;">{len(risky)}</div>
                <div class="metric-lbl">Flagged</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-val">{len(results)}</div>
                <div class="metric-lbl">Sentences</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-val" style="color:#22c55e;">{len(st.session_state.changes_log)}</div>
                <div class="metric-lbl">Rewrites Saved</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

        # MAIN LAYOUT
        left, right = st.columns([1.45, 1.0], gap="large")

        # LEFT — ARTICLE
        with left:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="slabel"><span class="dot-accent"></span>Highlighted Article — select a flagged sentence below</div>', unsafe_allow_html=True)
            article_html = render_article(results, st.session_state.sel_idx)
            st.markdown(f"<div class='article-box'>{article_html}</div>", unsafe_allow_html=True)
            st.markdown("""<div class="legend">
                <div class="legend-item">🟡 Yellow — review recommended</div>
                <div class="legend-item">🔴 Red — likely outdated</div>
            </div>""", unsafe_allow_html=True)

            if risky:
                st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
                st.markdown('<div class="slabel">Select flagged sentence to inspect</div>', unsafe_allow_html=True)
                opts = []
                for i, item in enumerate(risky):
                    icon = "🔴" if item["label"] == "danger" else "🟡"
                    short = item["sentence"][:72] + "..." if len(item["sentence"]) > 72 else item["sentence"]
                    opts.append(f"{icon} Score {item['score']} — {short}")
                sel = st.selectbox("Select", opts, index=st.session_state.sel_idx, label_visibility="collapsed")
                new_idx = opts.index(sel)
                if new_idx != st.session_state.sel_idx:
                    st.session_state.sel_idx = new_idx
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # RIGHT — INSPECTOR + CHAT
        with right:

            # INSPECTOR
            st.markdown('<div class="card" style="margin-bottom:0.8rem;">', unsafe_allow_html=True)
            st.markdown('<div class="slabel"><span class="dot-accent"></span>Sentence Inspector</div>', unsafe_allow_html=True)

            if risky:
                item = risky[st.session_state.sel_idx]
                ai_key = item["sentence"][:60]
                badge_cls = "badge-danger" if item["label"] == "danger" else "badge-warning"
                badge_txt = "🔴 Likely outdated" if item["label"] == "danger" else "🟡 Time-sensitive"
                q_cls = "inspector-quote-danger" if item["label"] == "danger" else "inspector-quote-warning"
                sc_color = "#ef4444" if item["score"] < 50 else "#f59e0b" if item["score"] < 80 else "#22c55e"

                hdr1, hdr2 = st.columns([3,1])
                with hdr1:
                    st.markdown(f'<div class="badge {badge_cls}">{badge_txt}</div>', unsafe_allow_html=True)
                with hdr2:
                    st.markdown(f"<div style='text-align:right;font-family:Playfair Display,serif;font-size:2rem;font-weight:700;color:{sc_color};line-height:1;'>{item['score']}</div>", unsafe_allow_html=True)

                st.markdown(f"<div class='inspector-quote {q_cls}'>{escape(item['sentence'])}</div>", unsafe_allow_html=True)
                st.markdown('<div class="slabel">Why flagged</div>', unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.86rem;color:#475569;line-height:1.65;margin-bottom:0.9rem;'>{item['explanation']}</div>", unsafe_allow_html=True)

                if st.button("✨  Get AI rewrite & sources", use_container_width=True):
                    with st.spinner("Asking AI..."):
                        res = ai_rewrite(item["sentence"])
                        st.session_state.ai_results[ai_key] = res
                        if res.get("rewrite") and not any(c["original"] == item["sentence"] for c in st.session_state.changes_log):
                            st.session_state.changes_log.append({
                                "original": item["sentence"], "rewrite": res["rewrite"],
                                "sources": res.get("sources", []), "label": item["label"], "score": item["score"]
                            })

                if ai_key in st.session_state.ai_results:
                    res = st.session_state.ai_results[ai_key]
                    st.markdown('<div class="badge badge-ai" style="margin-top:0.6rem;">✨ AI Suggestion</div>', unsafe_allow_html=True)
                    if res.get("rewrite"):
                        st.markdown('<div class="slabel">Rewritten sentence</div>', unsafe_allow_html=True)
                        st.markdown(f"<div class='ai-box'>{escape(res['rewrite'])}</div>", unsafe_allow_html=True)
                    if res.get("sources"):
                        st.markdown('<div class="slabel" style="margin-top:0.7rem;">Sources to verify</div>', unsafe_allow_html=True)
                        src = "<div class='source-list'>" + "".join(f"<div class='source-row'>→ {escape(s)}</div>" for s in res["sources"]) + "</div>"
                        st.markdown(src, unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-title">No flagged sentences</div><div class="empty-sub">All sentences look current.</div></div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # CHAT
            st.markdown('<div class="card-accent">', unsafe_allow_html=True)
            st.markdown('<div class="slabel" style="color:#4a5568;"><span class="dot-accent"></span>AI Assistant</div>', unsafe_allow_html=True)

            if st.session_state.chat_history:
                chat_html = '<div class="chat-scroll">'
                for msg in st.session_state.chat_history[-8:]:
                    if msg["role"] == "user":
                        chat_html += f'<div><div class="cname cname-right">You</div><div class="cbubble-user">{escape(msg["content"])}</div></div>'
                    else:
                        chat_html += f'<div><div class="cname">TimeTravel AI</div><div class="cbubble-ai">{msg["content"].replace(chr(10),"<br>")}</div></div>'
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center;padding:0.8rem 0;font-size:0.82rem;color:#4a5568;">Ask anything about your article</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
            ci, cb = st.columns([4,1], gap="small")
            with ci:
                user_msg = st.text_input("msg", placeholder="Ask about your article...", label_visibility="collapsed", key="chat_in")
            with cb:
                send = st.button("→", use_container_width=True, key="send")
            if send and user_msg.strip():
                st.session_state.chat_history.append({"role":"user","content":user_msg.strip()})
                with st.spinner(""):
                    reply = ai_chat(st.session_state.chat_history, st.session_state.article_text)
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()

            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            q1, q2 = st.columns(2)
            with q1:
                if st.button("What's outdated?", use_container_width=True, key="qp1"):
                    st.session_state.chat_history.append({"role":"user","content":"Which sentences in this article might be outdated?"})
                    with st.spinner(""):
                        reply = ai_chat(st.session_state.chat_history, st.session_state.article_text)
                    st.session_state.chat_history.append({"role":"assistant","content":reply})
                    st.rerun()
            with q2:
                if st.button("Suggest sources", use_container_width=True, key="qp2"):
                    st.session_state.chat_history.append({"role":"user","content":"Suggest reputable sources to verify the key claims in this article."})
                    with st.spinner(""):
                        reply = ai_chat(st.session_state.chat_history, st.session_state.article_text)
                    st.session_state.chat_history.append({"role":"assistant","content":reply})
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🕰️</div>
            <div class="empty-title">Paste an article and click Analyze</div>
            <div class="empty-sub">Flagged sentences will appear highlighted.<br>Click any to inspect and get an AI rewrite.</div>
        </div>""", unsafe_allow_html=True)

# ==================================================
# TAB 2 — CHANGES LOG
# ==================================================
with tab2:
    st.markdown('<div class="page-title" style="font-size:1.6rem;margin-bottom:0.3rem;">Changes Log</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub" style="margin-bottom:1.2rem;">{len(st.session_state.changes_log)} AI rewrite(s) generated this session. Every time you click ✨ AI rewrite, it appears here as a before/after comparison.</div>', unsafe_allow_html=True)

    if st.session_state.changes_log:
        for i, c in enumerate(st.session_state.changes_log):
            icon = "🔴" if c["label"] == "danger" else "🟡"
            sc_color = "#ef4444" if c["score"] < 50 else "#f59e0b"
            st.markdown(f"""
            <div class="change-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
                    <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:600;color:#1a1a2e;">Rewrite {i+1} {icon}</div>
                    <div style="font-size:0.75rem;font-weight:700;color:{sc_color};background:#fafaf7;border:1px solid #e8e5e0;border-radius:999px;padding:0.2rem 0.6rem;">Score: {c['score']}</div>
                </div>
                <div class="diff-label" style="color:#ef4444;">Before</div>
                <div class="diff-before">{escape(c['original'])}</div>
                <div class="diff-label" style="color:#16a34a;margin-top:0.5rem;">After</div>
                <div class="diff-after">{escape(c['rewrite'])}</div>
            """, unsafe_allow_html=True)
            if c.get("sources"):
                st.markdown('<div class="diff-label" style="color:#1d4ed8;margin-top:0.7rem;">Sources to verify</div>', unsafe_allow_html=True)
                for src in c["sources"]:
                    st.markdown(f"<div style='font-size:0.85rem;color:#1d4ed8;padding:0.2rem 0;'>→ {escape(src)}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📝</div>
            <div class="empty-title">No changes yet</div>
            <div class="empty-sub">Go to the Analyze tab, select a flagged sentence,<br>and click ✨ AI rewrite — it will appear here.</div>
        </div>""", unsafe_allow_html=True)
            