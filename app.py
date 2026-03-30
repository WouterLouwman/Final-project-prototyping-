import streamlit as st
import re
import datetime
from html import escape
from openai import OpenAI

st.set_page_config(
    page_title="TimeTravel · Temporal Trust Checker",
    page_icon="🕰️",
    layout="wide"
)

CURRENT_YEAR = datetime.datetime.now().year

# --------------------------------------------------
# OPENAI CLIENT
# --------------------------------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------------------------------
# STYLING
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: #f4f3ef;
        color: #0c0f1a;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    .hero {
        background: #0c0f1a;
        border-radius: 28px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.6rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(255,210,100,0.12) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #f0c95a;
        margin-bottom: 0.5rem;
    }
    .hero-title {
        font-family: 'Instrument Serif', serif;
        font-size: 2.8rem;
        font-weight: 400;
        line-height: 1.08;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .hero-sub {
        font-size: 0.97rem;
        line-height: 1.65;
        color: #8b92a8;
        max-width: 820px;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #e8e6e0;
        border-radius: 14px;
        padding: 4px;
        gap: 4px;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.5rem 1.4rem;
        font-weight: 600;
        font-size: 0.9rem;
        color: #64748b;
        background: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: #0c0f1a !important;
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

    .panel {
        background: #ffffff;
        border: 1px solid #e2ddd6;
        border-radius: 22px;
        padding: 1.3rem 1.4rem;
        box-shadow: 0 4px 18px rgba(12,15,26,0.05);
    }

    .section-label {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .article-box {
        background: #fafaf8;
        border: 1px solid #e2ddd6;
        border-radius: 18px;
        padding: 1.2rem 1.4rem;
        min-height: 180px;
        line-height: 2.1;
        color: #0c0f1a;
        font-size: 0.97rem;
    }

    .sentence { display: inline; padding: 3px 6px; border-radius: 7px; margin-right: 2px; }
    .safe { color: #0c0f1a; }
    .warning { background: #fef9e7; color: #7c5a00; border: 1px solid #f4de8a; }
    .danger  { background: #fdecea; color: #8b1e1e; border: 1px solid #f2b8b5; }

    .legend-wrap { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.9rem; }
    .legend-pill {
        background: #ffffff;
        border: 1px solid #e2ddd6;
        border-radius: 999px;
        padding: 0.38rem 0.85rem;
        font-size: 0.82rem;
        color: #64748b;
    }

    .detail-card {
        background: #ffffff;
        border: 1px solid #e2ddd6;
        border-radius: 22px;
        padding: 1.3rem 1.4rem;
        box-shadow: 0 4px 18px rgba(12,15,26,0.05);
    }

    .sentence-box {
        background: #f8f7f4;
        border: 1px solid #e2ddd6;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        color: #0c0f1a;
        line-height: 1.7;
        font-size: 0.97rem;
    }

    .pill-danger {
        display: inline-block;
        background: #fee2e2; color: #991b1b;
        border: 1px solid #fecaca;
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.76rem; font-weight: 700;
        margin-bottom: 0.8rem;
    }
    .pill-warning {
        display: inline-block;
        background: #fef3c7; color: #92400e;
        border: 1px solid #fde68a;
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.76rem; font-weight: 700;
        margin-bottom: 0.8rem;
    }
    .pill-ai {
        display: inline-block;
        background: #eff6ff; color: #1d4ed8;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.76rem; font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .metric-box {
        background: #ffffff;
        border: 1px solid #e2ddd6;
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 4px 16px rgba(12,15,26,0.04);
    }

    .progress-shell {
        background: #e8e6e0;
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    .progress-bar {
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%);
    }

    .info-box {
        background: #f8f7f4;
        border: 1px solid #e2ddd6;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        color: #64748b;
        line-height: 1.6;
        font-size: 0.92rem;
    }

    .ai-box {
        background: #f0f7ff;
        border: 1px solid #bfdbfe;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        color: #1e3a5f;
        line-height: 1.7;
        font-size: 0.95rem;
        margin-top: 0.4rem;
    }

    .chat-wrap {
        display: flex;
        flex-direction: column;
        gap: 0.9rem;
        padding: 0.5rem 0;
    }
    .chat-msg {
        max-width: 82%;
        padding: 0.85rem 1.1rem;
        border-radius: 18px;
        font-size: 0.95rem;
        line-height: 1.65;
    }
    .chat-user {
        background: #0c0f1a;
        color: #ffffff;
        align-self: flex-end;
        border-bottom-right-radius: 6px;
        margin-left: auto;
    }
    .chat-assistant {
        background: #ffffff;
        border: 1px solid #e2ddd6;
        color: #0c0f1a;
        align-self: flex-start;
        border-bottom-left-radius: 6px;
        box-shadow: 0 2px 10px rgba(12,15,26,0.05);
    }
    .chat-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .chat-label-user { color: #94a3b8; text-align: right; }
    .chat-label-assistant { color: #94a3b8; }

    textarea, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0c0f1a !important;
        border-radius: 14px !important;
        border: 1px solid #e2ddd6 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        padding: 0.55rem 1.1rem !important;
        border: 1px solid #cbd5e1 !important;
        background: #0c0f1a !important;
        color: white !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stButton > button:hover {
        background: #1e293b !important;
    }

    section[data-testid="stSidebar"] {
        background: #0c0f1a;
        border-right: 1px solid #1e2438;
    }
    section[data-testid="stSidebar"] * {
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: #1e2438 !important;
        border: 1px solid #2d3654 !important;
        color: #e2e8f0 !important;
    }

    [data-testid="stMetricValue"] {
        color: #0c0f1a;
        font-family: 'Instrument Serif', serif;
        font-size: 2rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.78rem !important;
    }

    .stSelectbox > div > div {
        border-radius: 12px !important;
        border: 1px solid #e2ddd6 !important;
        background: #ffffff !important;
    }

    hr { border-color: #e2ddd6; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# ANALYSIS FUNCTIONS
# --------------------------------------------------
def split_sentences(text: str):
    text = text.replace("\n", " ").strip()
    if not text:
        return []
    sentences = re.findall(r'[^.!?]+[.!?]+|[^.!?]+$', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_years(sentence: str):
    return [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', sentence)]

def contains_any(sentence: str, keywords):
    lower = sentence.lower()
    return any(keyword in lower for keyword in keywords)

def has_number(sentence: str):
    return bool(re.search(r'\b\d+(?:\.\d+)?%?\b', sentence))

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def analyze_sentence(sentence: str):
    score = 100
    reasons = []
    lower = sentence.lower()
    years = extract_years(sentence)

    time_sensitive_keywords = [
        "currently", "recently", "today", "now", "next year", "this year",
        "this month", "this week", "this summer", "this winter", "this quarter",
        "will", "planned", "expected to", "forecast", "soon", "upcoming"
    ]
    numeric_claim_keywords = [
        "inflation", "price", "prices", "market share", "interest rate",
        "unemployment", "gdp", "leader", "sales", "revenue", "ranked", "ranking"
    ]

    for year in years:
        age = CURRENT_YEAR - year
        if age >= 4:
            score -= 45
            reasons.append(f"Refers to {year}, which is {age} years ago — likely outdated.")
        elif age >= 2:
            score -= 28
            reasons.append(f"Refers to {year}, may need a freshness check.")
        elif age >= 1:
            score -= 12
            reasons.append(f"Includes a date from {year}, adding some temporal sensitivity.")

    if contains_any(sentence, time_sensitive_keywords):
        score -= 22
        reasons.append("Uses time-sensitive language such as 'currently', 'recently', or future-oriented wording.")

    if contains_any(sentence, numeric_claim_keywords) and has_number(sentence):
        score -= 18
        reasons.append("Includes a numerical claim tied to a topic that changes over time.")

    if ("next year" in lower or "will" in lower) and any(y < CURRENT_YEAR for y in years):
        score -= 18
        reasons.append("Combines future language with a past date — strongly suggests it is now outdated.")

    score = clamp(score, 5, 100)
    label = "danger" if score < 50 else "warning" if score < 80 else "safe"
    explanation = " ".join(reasons) if reasons else "No strong signs of temporal risk detected."

    return {
        "sentence": sentence,
        "score": score,
        "label": label,
        "explanation": explanation,
        "years": years
    }

def render_highlighted_article(results):
    html_parts = []
    for item in results:
        sentence_html = escape(item["sentence"])
        html_parts.append(f"<span class='sentence {item['label']}'>{sentence_html}</span>")
    return " ".join(html_parts)

# --------------------------------------------------
# OPENAI FUNCTIONS
# --------------------------------------------------
def ai_rewrite_and_sources(sentence: str) -> dict:
    prompt = f"""You are an editorial assistant helping journalists update outdated news articles.

A sentence has been flagged as potentially outdated or time-sensitive. Your job is to:
1. Rewrite the sentence to remove or flag the outdated claim, using neutral journalistic language.
2. Suggest 2-3 specific, reputable sources the journalist should check to verify current information.

Flagged sentence:
\"{sentence}\"

Respond in this exact format:
REWRITE: [your rewritten sentence]
SOURCES: [source 1] | [source 2] | [source 3]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4
    )

    text = response.choices[0].message.content.strip()
    rewrite = ""
    sources = []

    for line in text.split("\n"):
        if line.startswith("REWRITE:"):
            rewrite = line.replace("REWRITE:", "").strip()
        elif line.startswith("SOURCES:"):
            sources_raw = line.replace("SOURCES:", "").strip()
            sources = [s.strip() for s in sources_raw.split("|") if s.strip()]

    return {"rewrite": rewrite, "sources": sources}


def ai_chat(messages: list, article: str) -> str:
    system_prompt = f"""You are TimeTravel, an AI editorial assistant for a news agency.
Your job is to help journalists verify, update, and fact-check news articles.

You have access to the following article the journalist is currently working on:
---
{article if article.strip() else "No article has been pasted yet."}
---

Be concise, specific, and helpful. When suggesting sources, name real reputable outlets (Reuters, BBC, Eurostat, official government sites, etc.).
If asked to rewrite flagged sentences, do so in clear journalistic language."""

    openai_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        openai_messages.append({"role": msg["role"], "content": msg["content"]})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages,
        max_tokens=600,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

# --------------------------------------------------
# DEMO ARTICLE
# --------------------------------------------------
demo_article = (
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
if "article_text" not in st.session_state:
    st.session_state["article_text"] = demo_article
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "ai_results" not in st.session_state:
    st.session_state["ai_results"] = {}

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 🕰️ TimeTravel")
    st.markdown("<div style='color:#64748b;font-size:0.85rem;margin-bottom:1rem;'>Temporal credibility checker for editorial teams.</div>", unsafe_allow_html=True)

    if st.button("Load demo article", use_container_width=True):
        st.session_state["article_text"] = demo_article
        st.session_state["ai_results"] = {}

    if st.button("Clear article", use_container_width=True):
        st.session_state["article_text"] = ""
        st.session_state["ai_results"] = {}

    if st.button("Clear chat", use_container_width=True):
        st.session_state["chat_history"] = []

    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
- Splits article into sentences
- Detects old dates & time-sensitive wording
- Scores each sentence for freshness
- AI rewrites flagged sentences
- AI suggests sources to verify
- Chat assistant knows your article
    """)

    st.markdown("---")
    st.markdown("### Legend")
    st.markdown("""
🟡 **Yellow** — Review recommended  
🔴 **Red** — Likely outdated  
⚪ **White** — Looks current
    """)

# --------------------------------------------------
# HERO
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-label">Editorial AI · Prototype</div>
    <div class="hero-title">TimeTravel</div>
    <div class="hero-sub">
        Detect time-sensitive and outdated claims in news articles.
        Get AI-powered rewrites, source suggestions, and a live editorial assistant — all in one place.
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2 = st.tabs(["📋  Analyze Article", "💬  AI Assistant"])

# ==================================================
# TAB 1 — ANALYZE
# ==================================================
with tab1:
    left_col, right_col = st.columns([1.5, 1.0], gap="large")

    with left_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Article input</div>', unsafe_allow_html=True)
        article_text = st.text_area(
            "Paste article text",
            value=st.session_state["article_text"],
            height=240,
            label_visibility="collapsed"
        )
        st.session_state["article_text"] = article_text
        analyze_clicked = st.button("Analyze article", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">About this tool</div>', unsafe_allow_html=True)
        st.markdown("""
### Editorial support for aging information

This tool helps editors spot claims that may no longer be reliable because time has passed.

It highlights risky statements, scores them for freshness, and uses AI to suggest rewrites and sources to verify.
        """)
        st.markdown("""
<div class="info-box">
💡 Switch to the <strong>AI Assistant</strong> tab to chat directly about your article — request rewrites, find updated sources, or ask what needs updating.
</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # RESULTS
    if analyze_clicked or article_text.strip():
        sentences = split_sentences(article_text)
        results = [analyze_sentence(s) for s in sentences] if sentences else []

        if results:
            freshness_score = round(sum(item["score"] for item in results) / len(results))
            risky_results = [item for item in results if item["label"] != "safe"]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Article freshness score", f"{freshness_score}/100")
            with c2:
                st.metric("Flagged sentences", len(risky_results))
            with c3:
                st.metric("Total sentences", len(results))

            st.markdown('<div class="section-label" style="margin-top:1rem;">Overall freshness</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="progress-shell">
                <div class="progress-bar" style="width:{freshness_score}%;"></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">Highlighted article</div>', unsafe_allow_html=True)
            article_html = render_highlighted_article(results)
            st.markdown(f"<div class='article-box'>{article_html}</div>", unsafe_allow_html=True)
            st.markdown("""
            <div class="legend-wrap">
                <div class="legend-pill">🟡 Yellow = review recommended</div>
                <div class="legend-pill">🔴 Red = likely outdated</div>
                <div class="legend-pill">⚪ White = looks current</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">Inspect flagged sentences</div>', unsafe_allow_html=True)

            if risky_results:
                options = []
                for i, item in enumerate(risky_results, start=1):
                    short = item["sentence"][:88] + "..." if len(item["sentence"]) > 88 else item["sentence"]
                    options.append(f"{i}. [{item['score']}] {short}")

                selected_option = st.selectbox("Choose a flagged sentence", options, label_visibility="collapsed")
                selected_index = options.index(selected_option)
                selected_item = risky_results[selected_index]

                detail_col, side_col = st.columns([1.3, 0.7], gap="large")

                with detail_col:
                    pill_class = "pill-danger" if selected_item["label"] == "danger" else "pill-warning"
                    pill_text = "🔴 Likely outdated" if selected_item["label"] == "danger" else "🟡 Time-sensitive"

                    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="{pill_class}">{pill_text}</div>', unsafe_allow_html=True)

                    st.markdown('<div class="section-label">Selected sentence</div>', unsafe_allow_html=True)
                    st.markdown(f"<div class='sentence-box'>{escape(selected_item['sentence'])}</div>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<div class="section-label">Why flagged</div>', unsafe_allow_html=True)
                    st.write(selected_item["explanation"])

                    st.markdown("<br>", unsafe_allow_html=True)
                    ai_key = selected_item["sentence"][:60]

                    if st.button("✨ Get AI rewrite & sources", key=f"ai_{selected_index}"):
                        with st.spinner("Asking AI..."):
                            ai_result = ai_rewrite_and_sources(selected_item["sentence"])
                            st.session_state["ai_results"][ai_key] = ai_result

                    if ai_key in st.session_state["ai_results"]:
                        ai_data = st.session_state["ai_results"][ai_key]
                        st.markdown('<div class="pill-ai">✨ AI Suggestion</div>', unsafe_allow_html=True)

                        if ai_data.get("rewrite"):
                            st.markdown('<div class="section-label">AI rewrite</div>', unsafe_allow_html=True)
                            st.markdown(f"<div class='ai-box'>{escape(ai_data['rewrite'])}</div>", unsafe_allow_html=True)

                        if ai_data.get("sources"):
                            st.markdown('<div class="section-label" style="margin-top:0.8rem;">Suggested sources to verify</div>', unsafe_allow_html=True)
                            for source in ai_data["sources"]:
                                st.markdown(f"→ {source}")

                    st.markdown('</div>', unsafe_allow_html=True)

                with side_col:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    st.markdown('<div class="section-label">Freshness score</div>', unsafe_allow_html=True)
                    score_color = "#ef4444" if selected_item["score"] < 50 else "#f59e0b" if selected_item["score"] < 80 else "#22c55e"
                    st.markdown(f"<div style='font-size:2.6rem;font-weight:400;font-family:Instrument Serif,serif;color:{score_color};'>{selected_item['score']}</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="progress-shell">
                        <div class="progress-bar" style="width:{selected_item['score']}%;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    st.markdown('<div class="section-label">Detected signals</div>', unsafe_allow_html=True)
                    years_text = ", ".join(str(y) for y in selected_item["years"]) if selected_item["years"] else "None"
                    time_signal = "Yes" if contains_any(selected_item["sentence"], [
                        "currently", "recently", "today", "now", "next year", "this year",
                        "this month", "this week", "this summer", "this winter", "this quarter",
                        "will", "planned", "expected to", "forecast", "soon", "upcoming"
                    ]) else "No"
                    number_signal = "Yes" if has_number(selected_item["sentence"]) else "No"

                    st.markdown(f"**Years found:** {years_text}")
                    st.markdown(f"**Time-sensitive wording:** {time_signal}")
                    st.markdown(f"**Numerical claim:** {number_signal}")
                    st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.success("✅ No flagged sentences detected.")
        else:
            st.info("Paste an article above and click **Analyze article**.")
    else:
        st.info("Paste an article above and click **Analyze article**.")


# ==================================================
# TAB 2 — AI ASSISTANT
# ==================================================
with tab2:
    st.markdown('<div class="section-label">AI editorial assistant — always has your article in context</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="info-box" style="margin-bottom:1.2rem;">
Ask anything about your article — <strong>find updated sources</strong>, <strong>rewrite outdated sentences</strong>,
check facts, or ask what needs updating. Paste your article in the Analyze tab first.
</div>
    """, unsafe_allow_html=True)

    # CHAT HISTORY
    if st.session_state["chat_history"]:
        chat_html = '<div class="chat-wrap">'
        for msg in st.session_state["chat_history"]:
            if msg["role"] == "user":
                chat_html += f"""
                <div style="display:flex;flex-direction:column;align-items:flex-end;">
                    <div class="chat-label chat-label-user">You</div>
                    <div class="chat-msg chat-user">{escape(msg["content"])}</div>
                </div>"""
            else:
                content = msg["content"].replace("\n", "<br>")
                chat_html += f"""
                <div style="display:flex;flex-direction:column;align-items:flex-start;">
                    <div class="chat-label chat-label-assistant">TimeTravel AI</div>
                    <div class="chat-msg chat-assistant">{content}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 1rem;color:#94a3b8;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">💬</div>
            <div style="font-size:0.95rem;">No messages yet. Ask me anything about your article.</div>
            <div style="font-size:0.83rem;margin-top:0.4rem;">Try: <em>"Which sentences might be outdated?"</em> or <em>"Find me sources for the inflation claim."</em></div>
        </div>
        """, unsafe_allow_html=True)

    # INPUT ROW
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input(
            "Message",
            placeholder="Ask about your article, request rewrites, find sources...",
            label_visibility="collapsed",
            key="chat_input"
        )
    with chat_col2:
        send_clicked = st.button("Send →", use_container_width=True)

    if send_clicked and user_input.strip():
        st.session_state["chat_history"].append({"role": "user", "content": user_input.strip()})
        with st.spinner("Thinking..."):
            reply = ai_chat(st.session_state["chat_history"], st.session_state["article_text"])
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        st.rerun()

    # QUICK PROMPTS
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Quick prompts</div>', unsafe_allow_html=True)
    qc1, qc2, qc3 = st.columns(3)

    with qc1:
        if st.button("Which sentences might be outdated?", use_container_width=True):
            st.session_state["chat_history"].append({"role": "user", "content": "Which sentences in this article might be outdated?"})
            with st.spinner("Thinking..."):
                reply = ai_chat(st.session_state["chat_history"], st.session_state["article_text"])
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()

    with qc2:
        if st.button("Suggest sources to verify the article", use_container_width=True):
            st.session_state["chat_history"].append({"role": "user", "content": "Suggest reputable sources I should check to verify the key claims in this article."})
            with st.spinner("Thinking..."):
                reply = ai_chat(st.session_state["chat_history"], st.session_state["article_text"])
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()

    with qc3:
        if st.button("Rewrite the whole article", use_container_width=True):
            st.session_state["chat_history"].append({"role": "user", "content": "Please rewrite the entire article, updating or flagging any sentences that appear outdated or time-sensitive."})
            with st.spinner("Thinking..."):
                reply = ai_chat(st.session_state["chat_history"], st.session_state["article_text"])
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()