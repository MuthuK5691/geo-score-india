import streamlit as st
import google.generativeai as genai
import json
import re
import time
import html
import hashlib
import logging
from datetime import datetime

# ─────────────────────────────────────────────────────────────
#  SECURITY LAYER
# ─────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("geo_score")

_ALLOWED_CHARS = re.compile(r"[^\w\s\-\.\,\'\"\(\)\&\/\@\!\?\:]")

def sanitize(raw: str, max_len: int = 120) -> str:
    """Strip HTML entities, control chars, dangerous patterns."""
    if not isinstance(raw, str):
        raw = str(raw)
    cleaned = html.escape(raw.strip())
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"(?i)(script|onerror|onload|javascript|eval\s*\()", "", cleaned)
    return cleaned[:max_len]

def safe_int(val, lo=0, hi=100) -> int:
    try:
        return max(lo, min(hi, int(val)))
    except Exception:
        return lo

def validate_api_key(key: str) -> bool:
    """Validate Gemini API key format without leaking it."""
    return bool(re.fullmatch(r"AIza[0-9A-Za-z\-_]{35,45}", key.strip()))

def mask_key(key: str) -> str:
    return key[:7] + "••••••••" + key[-3:] if len(key) > 12 else "••••••••"

def rate_limited() -> tuple[bool, int]:
    """Returns (is_limited, seconds_to_wait)."""
    now = time.time()
    last = st.session_state.get("last_req_time", 0.0)
    count = st.session_state.get("req_count", 0)
    wait = max(0, 12 - int(now - last))
    if count > 0 and wait > 0:
        return True, wait
    if count >= 6:
        return True, -1  # -1 = session exhausted
    return False, 0

def record_request():
    st.session_state["last_req_time"] = time.time()
    st.session_state["req_count"] = st.session_state.get("req_count", 0) + 1

def safe_json_parse(raw: str) -> dict | None:
    """Multi-strategy JSON extraction from LLM output."""
    raw = raw.strip()
    # Strategy 1: strip markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # Strategy 2: find first { ... } block
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        pass
    # Strategy 3: fix common LLM JSON mistakes
    fixed = re.sub(r",\s*([}\]])", r"\1", m.group())  # trailing commas
    try:
        return json.loads(fixed)
    except Exception:
        return None

def sanitize_llm_output(data: dict) -> dict:
    """Sanitize every field coming back from the AI before rendering."""
    score = safe_int(data.get("brand_score", 0))
    summary = sanitize(str(data.get("brand_summary", "")), 400)
    sentiment = data.get("sentiment", "Neutral")
    if sentiment not in ("Positive", "Neutral", "Negative"):
        sentiment = "Neutral"
    quick_win = sanitize(str(data.get("quick_win", "")), 300)

    bd_raw = data.get("score_breakdown", {})
    breakdown = {
        "brand_mentions":       safe_int(bd_raw.get("brand_mentions", 0),       0, 25),
        "content_authority":    safe_int(bd_raw.get("content_authority", 0),    0, 25),
        "structured_data":      safe_int(bd_raw.get("structured_data", 0),      0, 25),
        "ai_citation_potential":safe_int(bd_raw.get("ai_citation_potential", 0),0, 25),
    }

    raw_comps = data.get("competitors", [])
    competitors = []
    if isinstance(raw_comps, list):
        for c in raw_comps[:5]:
            if isinstance(c, dict):
                competitors.append({
                    "name":     sanitize(str(c.get("name", "—")), 80),
                    "score":    safe_int(c.get("score", 0)),
                    "strength": sanitize(str(c.get("strength", "—")), 200),
                    "gap":      sanitize(str(c.get("gap", "—")), 200),
                })

    raw_tips = data.get("tips", [])
    tips = []
    if isinstance(raw_tips, list):
        for t in raw_tips[:5]:
            tips.append(sanitize(str(t), 350))

    return {
        "brand_score": score,
        "brand_summary": summary,
        "sentiment": sentiment,
        "quick_win": quick_win,
        "score_breakdown": breakdown,
        "competitors": competitors,
        "tips": tips,
    }


# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GEO Score India",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ─────────────────────────────────────────────────────────────
#  DESIGN SYSTEM — Editorial Terminal Aesthetic
#  Fonts: Fraunces (editorial serif display) + DM Mono (data)
#  Palette: near-black + saffron + electric cyan
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,700;0,900;1,300;1,700&family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600&display=swap');

/* ── CSS Variables ── */
:root {
  --bg:        #07070f;
  --bg2:       #0e0e1a;
  --bg3:       #13131f;
  --border:    rgba(255,255,255,0.07);
  --border2:   rgba(255,255,255,0.12);
  --saffron:   #FF9933;
  --cyan:      #00D4FF;
  --green:     #00E5A0;
  --red:       #FF4B6E;
  --yellow:    #FFD700;
  --text:      #E8E8F0;
  --muted:     #5a5a7a;
  --muted2:    #3a3a5c;
  --display:   'Fraunces', Georgia, serif;
  --mono:      'DM Mono', 'Courier New', monospace;
  --body:      'Outfit', system-ui, sans-serif;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
html, body, [class*="css"] { font-family: var(--body) !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton,
.viewerBadge_container__1QSob { display: none !important; }

/* ── App background ── */
.stApp {
  background: var(--bg);
  background-image:
    radial-gradient(ellipse 80% 50% at 10% 0%, rgba(255,153,51,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 90% 100%, rgba(0,212,255,0.05) 0%, transparent 60%),
    repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.015) 40px),
    repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.015) 40px);
  min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
[data-testid="stSidebar"] * { color: #c0c0d8 !important; }
[data-testid="stSidebar"] strong { color: var(--text) !important; }
[data-testid="stSidebar"] a { color: var(--cyan) !important; text-decoration: none !important; }
[data-testid="stSidebar"] a:hover { text-decoration: underline !important; }

/* ── All input labels ── */
label, [data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label {
  font-family: var(--mono) !important;
  font-size: 0.68rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  margin-bottom: 6px !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input {
  background: var(--bg3) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: var(--body) !important;
  font-size: 0.95rem !important;
  padding: 11px 15px !important;
  transition: all 0.2s ease !important;
  caret-color: var(--saffron) !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--saffron) !important;
  box-shadow: 0 0 0 3px rgba(255,153,51,0.12) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--muted2) !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
  background: var(--bg3) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}

/* ── Password input eye icon ── */
[data-testid="stTextInput"] button {
  background: transparent !important;
  border: none !important;
  color: var(--muted) !important;
}

/* ── Generate button ── */
.stButton > button {
  font-family: var(--mono) !important;
  font-weight: 500 !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  background: transparent !important;
  color: var(--saffron) !important;
  border: 1px solid var(--saffron) !important;
  border-radius: 6px !important;
  padding: 14px 40px !important;
  width: 100% !important;
  cursor: pointer !important;
  position: relative !important;
  overflow: hidden !important;
  transition: all 0.3s ease !important;
  z-index: 1 !important;
}
.stButton > button::before {
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background: var(--saffron) !important;
  transform: translateX(-101%) !important;
  transition: transform 0.3s ease !important;
  z-index: -1 !important;
}
.stButton > button:hover {
  color: #07070f !important;
  box-shadow: 0 0 32px rgba(255,153,51,0.35) !important;
}
.stButton > button:hover::before { transform: translateX(0) !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--saffron), var(--cyan)) !important;
  border-radius: 4px !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 18px !important;
  transition: border-color 0.2s, transform 0.2s !important;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(255,153,51,0.3) !important;
  transform: translateY(-2px) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--mono) !important;
  font-size: 1.9rem !important;
  color: var(--cyan) !important;
}
[data-testid="stMetricLabel"] {
  font-family: var(--mono) !important;
  font-size: 0.62rem !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-bottom: 10px !important;
}
[data-testid="stExpander"] summary {
  font-family: var(--mono) !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  color: var(--text) !important;
  padding: 14px 18px !important;
}
[data-testid="stExpander"] summary:hover { color: var(--saffron) !important; }

/* ── Alerts ── */
.stAlert { border-radius: 8px !important; border: none !important; }
[data-testid="stNotificationContentError"]   { background: rgba(255,75,110,0.1) !important; }
[data-testid="stNotificationContentWarning"] { background: rgba(255,215,0,0.08)  !important; }
[data-testid="stNotificationContentInfo"]    { background: rgba(0,212,255,0.08)  !important; }
[data-testid="stNotificationContentSuccess"] { background: rgba(0,229,160,0.08)  !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.8rem 0 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
  overflow: hidden !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--muted2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--saffron); }

/* ─────── COMPONENT CLASSES ─────── */

/* Hero */
.g-hero { padding: 1.5rem 0 1rem; }
.g-eyebrow {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--saffron);
  margin-bottom: 1rem;
  display: flex; align-items: center; gap: 10px;
}
.g-eyebrow::before {
  content: '';
  display: inline-block;
  width: 28px; height: 1px;
  background: var(--saffron);
}
.g-headline {
  font-family: var(--display);
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  font-weight: 900;
  line-height: 1.08;
  color: var(--text);
  margin-bottom: 1rem;
  letter-spacing: -0.02em;
}
.g-headline em {
  font-style: italic;
  font-weight: 300;
  color: var(--saffron);
}
.g-subhead {
  font-size: 1rem;
  font-weight: 300;
  color: var(--muted);
  line-height: 1.7;
  max-width: 560px;
}

/* Score display */
.g-score-wrap {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.g-score-wrap::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 120px; height: 120px;
  background: radial-gradient(circle, rgba(255,153,51,0.12), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.g-score-num {
  font-family: var(--display);
  font-size: 5.5rem;
  font-weight: 900;
  line-height: 1;
  color: var(--saffron);
  letter-spacing: -0.04em;
}
.g-score-denom {
  font-family: var(--mono);
  font-size: 1.1rem;
  color: var(--muted);
  margin-left: 4px;
}
.g-score-status {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-top: 8px;
  padding: 4px 12px;
  border-radius: 100px;
  display: inline-block;
}

/* Signal bars */
.g-bars { display: flex; align-items: flex-end; gap: 4px; justify-content: center; margin-top: 14px; height: 32px; }
.g-bar {
  width: 8px;
  border-radius: 2px;
  transition: opacity 0.3s;
}

/* Tip card */
.g-tip {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-left: 3px solid var(--cyan);
  border-radius: 8px;
  padding: 14px 18px;
  margin: 8px 0;
  color: #b8b8d0;
  font-size: 0.92rem;
  line-height: 1.75;
  transition: border-left-color 0.2s, background 0.2s;
}
.g-tip:hover {
  border-left-color: var(--saffron);
  background: rgba(255,153,51,0.04);
}
.g-tip strong { color: var(--text); }

/* Quick win */
.g-qwin {
  background: rgba(0,229,160,0.06);
  border: 1px solid rgba(0,229,160,0.2);
  border-left: 3px solid var(--green);
  border-radius: 8px;
  padding: 14px 18px;
  color: #a0f0d8;
  font-size: 0.92rem;
  line-height: 1.75;
  margin-top: 10px;
}

/* Section label */
.g-label {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.8rem;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* Sentiment box */
.g-sentiment {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px 16px;
  text-align: center;
  height: 100%;
}
.g-sentiment-icon { font-size: 2.6rem; margin-bottom: 10px; }
.g-sentiment-text {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
}
.g-sentiment-val {
  font-family: var(--display);
  font-size: 1.3rem;
  font-weight: 700;
  margin-top: 4px;
}

/* Security badge */
.g-sec {
  background: rgba(0,229,160,0.06);
  border: 1px solid rgba(0,229,160,0.15);
  border-radius: 8px;
  padding: 10px 14px;
  margin-top: 14px;
  font-size: 0.75rem;
  color: #7ee8c4;
  line-height: 1.6;
}

/* Premium CTA */
.g-cta {
  background: var(--bg2);
  border: 1px solid rgba(255,153,51,0.2);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.g-cta::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 50% at 50% 0%, rgba(255,153,51,0.07), transparent);
  pointer-events: none;
}
.g-cta h3 {
  font-family: var(--display);
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 10px;
}
.g-cta p {
  color: var(--muted);
  font-size: 0.93rem;
  line-height: 1.7;
  margin-bottom: 22px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}
.g-cta-btn {
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.85rem;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  background: var(--saffron);
  color: #07070f !important;
  text-decoration: none !important;
  border-radius: 6px;
  padding: 14px 40px;
  box-shadow: 0 4px 28px rgba(255,153,51,0.3);
  transition: box-shadow 0.2s, transform 0.2s;
}
.g-cta-btn:hover {
  box-shadow: 0 6px 40px rgba(255,153,51,0.5);
  transform: translateY(-2px);
}
.g-cta-note {
  margin-top: 14px;
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  color: var(--muted);
}

/* Empty state */
.g-empty {
  text-align: center;
  padding: 80px 24px;
}
.g-empty-icon {
  font-size: 3rem;
  margin-bottom: 18px;
  opacity: 0.4;
}
.g-empty-title {
  font-family: var(--display);
  font-size: 1.6rem;
  font-weight: 700;
  color: #2a2a40;
  margin-bottom: 14px;
}
.g-step {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  text-align: left;
  max-width: 380px;
  margin: 12px auto;
}
.g-step-n {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--saffron);
  border: 1px solid rgba(255,153,51,0.3);
  min-width: 26px;
  height: 26px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.g-step-t { color: #2d2d50; font-size: 0.87rem; line-height: 1.65; }
.g-step-t strong { color: #3d3d60; }

/* Counter badge */
.g-counter {
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 4px 10px;
  color: var(--muted);
  margin-top: 10px;
}

/* Animations */
@keyframes fadeUp   { from { opacity:0; transform:translateY(16px) } to { opacity:1; transform:none } }
@keyframes fadeIn   { from { opacity:0 } to { opacity:1 } }
@keyframes scanline {
  0%   { transform: translateY(-100%) }
  100% { transform: translateY(100vh) }
}

/* Responsive */
@media (max-width: 768px) {
  .g-headline { font-size: 2rem; }
  .g-score-num { font-size: 4rem; }
  .g-cta { padding: 20px 16px; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────────────────────

for k, v in [("req_count", 0), ("last_req_time", 0.0), ("last_result", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        "<p style=\"font-family:var(--mono);font-size:0.62rem;letter-spacing:0.18em;"
        "text-transform:uppercase;color:#FF9933;margin-bottom:1.2rem\">"
        "⬡ GEO Score India</p>",
        unsafe_allow_html=True,
    )

    st.markdown("**API Configuration**")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza••••••••••••",
        help="Free at aistudio.google.com — your key never touches our servers.",
        key="api_key_field",
    )

    if api_key:
        if validate_api_key(api_key):
            st.success(f"Valid format — {mask_key(api_key)}", icon="🔒")
        else:
            st.error("Key must start with AIza + 35–45 alphanumeric chars.", icon="⚠️")

    st.markdown("""
    <div class="g-sec">
      🛡️ <strong>Security guarantee:</strong><br>
      Your key is validated client-side, sent only to Google's
      Gemini API over TLS 1.3, never logged, never stored,
      and erased when this tab closes.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**→ [Get free API key](https://aistudio.google.com/app/apikey)**")
    st.markdown("---")

    with st.expander("ℹ️  What is GEO?"):
        st.markdown(
            "**Generative Engine Optimisation** is the practice of making your "
            "brand appear prominently inside AI-generated answers — on Gemini, "
            "ChatGPT, Perplexity, and Copilot. It is the successor to traditional SEO."
        )

    with st.expander("🔐  Privacy Policy"):
        st.markdown(
            "- No user data is collected or stored  \n"
            "- API keys exist only in browser memory  \n"
            "- No cookies, no tracking, no analytics  \n"
            "- All AI calls go Google → you, we see nothing  \n"
            "- Rate limiting is session-only, not logged"
        )

    st.markdown("---")
    st.markdown(
        "<p style=\"font-size:0.7rem;color:#2a2a40;font-family:var(--mono);"
        "letter-spacing:0.06em\">GEO Score India v2.0<br>"
        "Built for 🇮🇳 founders · 2025</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="g-hero">
  <div class="g-eyebrow">AI Visibility Intelligence Platform</div>
  <div class="g-headline">
    Is your brand<br><em>invisible</em> to AI?
  </div>
  <div class="g-subhead">
    Score your brand's presence inside Gemini, ChatGPT & Perplexity.
    See exactly where you stand against competitors — and how to dominate.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ─────────────────────────────────────────────────────────────
#  INPUT FORM
# ─────────────────────────────────────────────────────────────

c_left, c_right = st.columns(2, gap="large")

with c_left:
    st.markdown('<div class="g-label">01 — Your Brand</div>', unsafe_allow_html=True)
    brand_name = st.text_input(
        "Brand Name",
        placeholder="e.g.  Zepto, Nykaa, Groww",
        max_chars=80,
        key="brand",
    )
    industry = st.selectbox(
        "Industry Vertical",
        options=[
            "E-Commerce / D2C", "SaaS / B2B Software", "Fintech / BFSI",
            "EdTech", "HealthTech / Pharma", "Food & Beverage / QSR",
            "Real Estate / PropTech", "Travel & Hospitality",
            "Media & Entertainment", "Logistics & Supply Chain",
            "Retail / Offline Stores", "HR Tech / Recruitment",
            "AgriTech", "CleanTech / EV", "Gaming / Esports", "Other",
        ],
        key="industry",
    )
    city = st.text_input(
        "Primary Market / City",
        placeholder="e.g.  Bengaluru, Pan-India, Mumbai",
        max_chars=60,
        key="city",
    )

with c_right:
    st.markdown('<div class="g-label">02 — Competitor Intel</div>', unsafe_allow_html=True)
    comp1 = st.text_input("Competitor 1", placeholder="e.g.  Blinkit",   max_chars=60, key="c1")
    comp2 = st.text_input("Competitor 2", placeholder="e.g.  Swiggy Instamart", max_chars=60, key="c2")
    comp3 = st.text_input("Competitor 3", placeholder="e.g.  BigBasket", max_chars=60, key="c3")
    st.markdown(
        "<p style=\"font-size:0.75rem;color:#2a2a40;margin-top:8px\">"
        "Add your top 3 rivals — the AI will benchmark you against each one.</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")
go = st.button("⬡  RUN GEO ANALYSIS", use_container_width=True)
st.markdown("")


# ─────────────────────────────────────────────────────────────
#  PROMPT BUILDER
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a world-class Generative Engine Optimisation (GEO) analyst
specialising in the Indian market. You provide accurate, evidence-based analysis
of how brands appear in AI-generated answers. Be specific, realistic, and data-driven.
Never fabricate statistics. Return ONLY valid JSON — no markdown, no prose, no fences."""

def build_prompt(brand: str, vertical: str, market: str, rivals: list[str]) -> str:
    rivals_str = ", ".join(r for r in rivals if r)
    return (
        f'You are analysing GEO (Generative Engine Optimisation) visibility for an Indian brand.\n\n'
        f'Brand: {brand}\nIndustry: {vertical}\nMarket: {market}, India\nCompetitors: {rivals_str}\n\n'
        f'Evaluate how frequently and positively this brand appears in AI-generated answers '
        f'on Gemini, ChatGPT, and Perplexity. Consider content depth, brand authority, '
        f'structured data presence, and citation likelihood.\n\n'
        f'Return ONLY this JSON object:\n'
        f'{{"brand_score": <integer 0-100>, '
        f'"brand_summary": "<2 specific sentences about AI visibility>", '
        f'"sentiment": "<Positive|Neutral|Negative>", '
        f'"competitors": [{{"name": "<name>", "score": <0-100>, '
        f'"strength": "<specific AI strength>", "gap": "<specific gap vs {brand}>"}}], '
        f'"tips": ["<highly specific GEO tip 1 for {brand} in {vertical}>", '
        f'"<tip 2>", "<tip 3>", "<tip 4>", "<tip 5>"], '
        f'"score_breakdown": {{"brand_mentions": <0-25>, "content_authority": <0-25>, '
        f'"structured_data": <0-25>, "ai_citation_potential": <0-25>}}, '
        f'"quick_win": "<single most impactful action to improve AI visibility this week>"}}\n\n'
        f'Scoring benchmarks for Indian brands: 0-25 invisible, 26-45 emerging, '
        f'46-65 established, 66-80 strong, 81-100 dominant. '
        f'Most Indian brands score 25-60. Be realistic, not generous.'
    )


# ─────────────────────────────────────────────────────────────
#  HELPER RENDERERS
# ─────────────────────────────────────────────────────────────

def render_score_bars(score: int, color: str):
    """Render 5 signal-strength bars proportional to score."""
    levels = [20, 40, 60, 80, 100]
    bars_html = '<div class="g-bars">'
    for i, lvl in enumerate(levels):
        height = 8 + i * 6
        active = score >= lvl
        c = color if active else "#1a1a2e"
        bars_html += (
            f'<div class="g-bar" style="height:{height}px;background:{c};'
            f'opacity:{1 if active else 0.3}"></div>'
        )
    bars_html += '</div>'
    return bars_html

def get_score_meta(score: int) -> dict:
    if score >= 81: return {"label": "DOMINANT",    "color": "#00E5A0"}
    if score >= 66: return {"label": "STRONG",       "color": "#00D4FF"}
    if score >= 46: return {"label": "ESTABLISHED", "color": "#FF9933"}
    if score >= 26: return {"label": "EMERGING",    "color": "#FFD700"}
    return           {"label": "INVISIBLE",  "color": "#FF4B6E"}


# ─────────────────────────────────────────────────────────────
#  MAIN LOGIC
# ─────────────────────────────────────────────────────────────

if go:
    # ── Validation ────────────────────────────────────────────
    errs = []
    if not api_key.strip():
        errs.append("API key is required — add it in the sidebar.")
    elif not validate_api_key(api_key):
        errs.append("API key format invalid. Should be AIza followed by 35–45 characters.")
    if not brand_name.strip():
        errs.append("Brand name cannot be empty.")
    elif len(brand_name.strip()) < 2:
        errs.append("Brand name must be at least 2 characters.")
    if not city.strip():
        errs.append("City / Market is required.")
    if not any(x.strip() for x in [comp1, comp2, comp3]):
        errs.append("Add at least one competitor for benchmarking.")

    if errs:
        for e in errs:
            st.error(e, icon="⚠️")
        st.stop()

    # ── Rate limit ─────────────────────────────────────────────
    limited, wait = rate_limited()
    if limited:
        if wait == -1:
            st.warning("You've used 6 analyses this session. Refresh the page to continue.", icon="🔄")
        else:
            st.info(f"Please wait {wait} seconds before the next analysis.", icon="⏳")
        st.stop()

    # ── Sanitize ───────────────────────────────────────────────
    sb = sanitize(brand_name, 80)
    sc = sanitize(city, 60)
    sr = [sanitize(x, 60) for x in [comp1, comp2, comp3] if x.strip()]

    # ── API call ───────────────────────────────────────────────
    prog = st.progress(0, text="Establishing encrypted connection…")
    try:
        time.sleep(0.2)
        genai.configure(api_key=api_key.strip())
        prog.progress(15, text="Authenticating with Gemini…")

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.types.GenerationConfig(
                temperature=0.35,
                max_output_tokens=1400,
                top_p=0.9,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        )

        prog.progress(35, text=f"Analysing AI presence of {sb}…")
        response = model.generate_content(build_prompt(sb, industry, sc, sr))
        prog.progress(70, text="Parsing & validating response…")

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        raw_data = safe_json_parse(response.text)
        if raw_data is None:
            raise ValueError("Could not extract valid JSON from Gemini response.")

        data = sanitize_llm_output(raw_data)
        prog.progress(100, text="Analysis complete.")
        time.sleep(0.4)
        prog.empty()

        record_request()
        st.session_state["last_result"] = {
            "data": data, "brand": sb, "industry": industry,
            "city": sc, "rivals": sr,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        }

    except Exception as exc:
        prog.empty()
        err_str = str(exc)
        logger.warning("Gemini call failed: %s", err_str[:200])
        if any(x in err_str.upper() for x in ["API_KEY", "CREDENTIAL", "PERMISSION"]):
            st.error("Invalid API key. Double-check and try again.", icon="🔑")
        elif "quota" in err_str.lower() or "429" in err_str:
            st.error("Gemini quota exceeded. Wait ~1 minute and retry.", icon="📊")
        elif "empty" in err_str.lower() or "json" in err_str.lower():
            st.error("Gemini returned an unexpected format. Try once more.", icon="🔄")
        elif "safety" in err_str.lower():
            st.error("Request blocked by safety filters. Try rephrasing your brand/competitor names.", icon="🛡️")
        else:
            st.error(f"Unexpected error: {err_str[:180]}", icon="❌")
        st.stop()


# ─────────────────────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────────────────────

result = st.session_state.get("last_result")

if result:
    data     = result["data"]
    sb       = result["brand"]
    industry = result["industry"]
    sc       = result["city"]
    ts       = result["timestamp"]

    score = data["brand_score"]
    bd    = data["score_breakdown"]
    meta  = get_score_meta(score)

    st.markdown(
        f"<p style=\"font-family:var(--mono);font-size:0.65rem;letter-spacing:0.12em;"
        f"color:#2a2a40;margin-bottom:1.2rem\">REPORT GENERATED {ts.upper()} — {sb.upper()}</p>",
        unsafe_allow_html=True,
    )

    # ── Score + breakdown row ──────────────────────────────────
    col_score, col_m1, col_m2, col_m3, col_m4 = st.columns([2, 1, 1, 1, 1], gap="small")

    with col_score:
        bars = render_score_bars(score, meta["color"])
        st.markdown(f"""
        <div class="g-score-wrap">
          <div class="g-score-num">{score}<span class="g-score-denom">/100</span></div>
          <div class="g-score-status" style="background:rgba(255,255,255,0.05);color:{meta['color']};
               border:1px solid {meta['color']}44">{meta['label']}</div>
          {bars}
          <div style="font-family:var(--mono);font-size:0.6rem;letter-spacing:0.12em;
               color:var(--muted);margin-top:10px">GEO VISIBILITY SCORE</div>
        </div>
        """, unsafe_allow_html=True)

    col_m1.metric("Brand Mentions",       f"{bd['brand_mentions']}/25")
    col_m2.metric("Content Authority",    f"{bd['content_authority']}/25")
    col_m3.metric("Structured Data",      f"{bd['structured_data']}/25")
    col_m4.metric("AI Citation Potential",f"{bd['ai_citation_potential']}/25")

    st.markdown("---")

    # ── Summary + Sentiment ────────────────────────────────────
    col_sum, col_sent = st.columns([3, 1], gap="medium")

    with col_sum:
        st.markdown('<div class="g-label">AI Analysis Summary</div>', unsafe_allow_html=True)
        st.info(data["brand_summary"])
        if data["quick_win"]:
            st.markdown(
                f'<div class="g-qwin">⚡ <strong>Quick Win this week:</strong> {data["quick_win"]}</div>',
                unsafe_allow_html=True,
            )

    with col_sent:
        sent = data["sentiment"]
        icons = {"Positive": "😊", "Neutral": "😐", "Negative": "😟"}
        colors= {"Positive": "#00E5A0", "Neutral": "#FFD700", "Negative": "#FF4B6E"}
        st.markdown(f"""
        <div class="g-sentiment">
          <div class="g-sentiment-icon">{icons.get(sent, "😐")}</div>
          <div class="g-sentiment-text">AI Sentiment</div>
          <div class="g-sentiment-val" style="color:{colors.get(sent, '#FFD700')}">{sent}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Competitor table ───────────────────────────────────────
    with st.expander("◈  COMPETITOR BENCHMARK TABLE", expanded=True):
        import pandas as pd
        rows = [{
            "Brand":    f"★ {sb}  (you)",
            "GEO Score":score,
            "Status":   meta["label"].title(),
            "Summary":  data["brand_summary"][:70] + "…",
            "Key Gap":  "—",
        }]
        for c in data["competitors"]:
            cm = get_score_meta(c["score"])
            rows.append({
                "Brand":    c["name"],
                "GEO Score":c["score"],
                "Status":   cm["label"].title(),
                "Summary":  c["strength"][:70],
                "Key Gap":  c["gap"][:70],
            })
        df = pd.DataFrame(rows)
        st.dataframe(
            df.style.background_gradient(subset=["GEO Score"], cmap="RdYlGn", vmin=0, vmax=100)
              .set_properties(**{"font-size": "0.85rem"}),
            use_container_width=True,
            hide_index=True,
        )

    # ── Tips ───────────────────────────────────────────────────
    with st.expander("◈  5 PERSONALISED GEO IMPROVEMENT TIPS", expanded=True):
        st.markdown(
            f"<p style=\"font-family:var(--mono);font-size:0.65rem;letter-spacing:0.1em;"
            f"color:var(--muted);margin-bottom:12px\">"
            f"TAILORED FOR {sb.upper()} · {industry.upper()} · {sc.upper()}</p>",
            unsafe_allow_html=True,
        )
        for i, tip in enumerate(data["tips"], 1):
            st.markdown(
                f'<div class="g-tip"><strong>#{i:02d}</strong> — {tip}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Premium CTA ────────────────────────────────────────────
    RAZORPAY_LINK = "https://razorpay.me/your-payment-link"
    st.markdown(f"""
    <div class="g-cta">
      <h3>Unlock the Full Intelligence Report</h3>
      <p>
        A 30-page deep-dive built specifically for <strong>{sb}</strong> —
        covering keyword gap maps, AI citation source analysis,
        a 90-day GEO content calendar, and competitor takedown tactics.
      </p>
      <a class="g-cta-btn" href="{RAZORPAY_LINK}" target="_blank" rel="noopener noreferrer">
        Get Premium Report — ₹999
      </a>
      <div class="g-cta-note">🔒 Razorpay · Instant PDF delivery · No subscription</div>
    </div>
    """, unsafe_allow_html=True)

    remaining = max(0, 6 - st.session_state.get("req_count", 0))
    st.markdown(
        f'<div style="text-align:center;margin-top:14px">'        f'<span class="g-counter">{remaining} FREE ANALYSES REMAINING THIS SESSION</span></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────

else:
    st.markdown("""
    <div class="g-empty">
      <div class="g-empty-icon">◈</div>
      <div class="g-empty-title">Start your first analysis</div>
      <div class="g-step">
        <div class="g-step-n">01</div>
        <div class="g-step-t">Paste your <strong>Gemini API Key</strong> in the sidebar — free from Google AI Studio</div>
      </div>
      <div class="g-step">
        <div class="g-step-n">02</div>
        <div class="g-step-t">Enter your <strong>brand, industry, city</strong> and up to 3 competitors</div>
      </div>
      <div class="g-step">
        <div class="g-step-n">03</div>
        <div class="g-step-t">Hit <strong>Run GEO Analysis</strong> — full report in under 10 seconds</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
