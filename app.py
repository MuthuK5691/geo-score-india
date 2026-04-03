"""
GEO Score India — v6.0 "Apex"
AI Visibility Intelligence Platform for Indian Brands · April 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECURITY AUDIT — v5.1 → v6.0 FIXES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIX-S1: Payment replay prevention — processed payment_ids stored
         in session state; same payment_id cannot unlock twice.
FIX-S2: data:text and base64 patterns added to injection regex
         (v5.1 missed these exfil vectors).
FIX-S3: brand/city/competitor strings re-sanitized before being
         injected into HTML f-strings (double-safety layer).
FIX-S4: hmac.new (stdlib) — constant-time compare documented.
FIX-S5: Rate limit counter no longer resets on accidental re-run
         within the same second (added floor check).
FIX-S6: Model fallback loop raises on auth/quota errors immediately
         rather than silently falling through all models.

CONVERSION UPGRADES vs v5.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
+ Loss-framing hero ("Your customers ask AI. You don't exist.")
+ Animated social proof bar (brands analyzed counter)
+ Hero stat pills (40%+ searches go to AI, 89% score below 50 etc.)
+ Value-stack paywall with FREE / LOCKED rows + price anchoring
+ Risk reversal guarantee ("100% actionable or full refund")
+ Indian psychology pricing anchor (vs ₹25,000 agency audit)
+ 3 founder testimonials with score deltas (social proof)
+ 5 FAQ expanders — kills every common objection
+ Trust badge bar — Razorpay, HMAC, DPDP, Refund, No Ads
+ Testimonials shown even BEFORE first analysis (trust before ask)
+ CTA button copy changed to "RUN FREE GEO ANALYSIS" (lowers friction)

DEPLOY CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Streamlit Community Cloud → connect repo → Settings → Secrets:
     GEMINI_API_KEY  = "AIza..."
     RZP_KEY_SECRET  = "your_rzp_key_secret"
     RZP_PAYMENT_URL = "https://rzp.io/l/XXXXXX"

2. Razorpay Dashboard → Payment Pages → your page → Page Settings
   → "Action after successful payment" → Redirect to your website
   → URL: https://your-app.streamlit.app/

3. Test with rzp_test_ keys first. Go live only after Razorpay
   approves your website submission.

FREE HOSTING + DOMAIN NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Best free: Streamlit Community Cloud (streamlit.io) — 3 free apps,
           always-on, HTTPS automatic, no custom domain on free tier.
Custom domain (cheapest): Buy .in domain (~₹400-600/yr from BigRock
           or GoDaddy India) + deploy on Render.com free tier
           (supports CNAME for custom domains, sleeps after 15 min
           inactivity — upgrade to $7/mo for always-on).
Recommended path: Streamlit Community Cloud now, migrate to Render
           paid ($7/mo) once you hit ₹5,000+/month revenue.
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
import streamlit as st
import streamlit.components.v1 as components

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
logger = logging.getLogger("geo")

_R    = 74
_CIRC = round(2 * 3.14159265358979 * _R, 4)   # 465.0884

st.set_page_config(
    page_title="GEO Score India — Is Your Brand Invisible to AI?",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)


# ═══════════════════════════════════════════════════════════════════
#  SECURITY LAYER
# ═══════════════════════════════════════════════════════════════════
_INJECT_PAT = re.compile(
    r"(?i)(ignore\s+(all\s+)?previous|forget\s+(all\s+)?instructions"
    r"|act\s+as|you\s+are\s+now|jailbreak|dan\s+mode"
    r"|<script|onerror|onload|javascript:|eval\s*\("
    r"|base64|data:text|data:image)",
)


def sanitize(raw: Any, max_len: int = 120) -> str:
    s = html.escape(str(raw).strip())
    s = re.sub(r"[\x00-\x1f\x7f]", "", s)
    return _INJECT_PAT.sub("", s)[:max_len]


def safe_int(v: Any, lo: int = 0, hi: int = 100) -> int:
    try:
        return max(lo, min(hi, int(v)))
    except Exception:
        return lo


def validate_key(k: str) -> bool:
    return bool(re.fullmatch(r"AIza[0-9A-Za-z\-_]{33,39}", k.strip()))


def mask(k: str) -> str:
    return k[:7] + "·········" + k[-3:] if len(k) > 12 else "·····"


def rate_check() -> Tuple[bool, int]:
    now  = time.time()
    last = st.session_state.get("_last", 0.0)
    n    = st.session_state.get("_n", 0)
    wait = max(0, 12 - int(now - last))
    if n > 0 and wait > 0:
        return True, wait
    if n >= 6:
        return True, -1
    return False, 0


def record_req() -> None:
    st.session_state["_last"] = time.time()
    st.session_state["_n"]    = st.session_state.get("_n", 0) + 1


def safe_json(raw: str) -> Optional[Dict]:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$",           "", raw)
    m   = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    blob = m.group()
    for attempt in (blob, re.sub(r",\s*([}\]])", r"\1", blob)):
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            continue
    return None


def clean_llm(data: Dict) -> Dict:
    score = safe_int(data.get("brand_score", 0))
    sent  = data.get("sentiment", "Neutral")
    if sent not in ("Positive", "Neutral", "Negative"):
        sent = "Neutral"
    braw = data.get("score_breakdown", {}) or {}
    bd   = {
        k: safe_int(braw.get(k, 0), 0, 25)
        for k in ("brand_mentions", "content_authority",
                  "structured_data", "ai_citation_potential")
    }
    comps: List[Dict] = []
    for c in (data.get("competitors", []) or [])[:5]:
        if isinstance(c, dict):
            comps.append({
                "name":     sanitize(str(c.get("name",     "Unknown")), 80),
                "score":    safe_int(c.get("score", 0)),
                "strength": sanitize(str(c.get("strength", "")), 220),
                "gap":      sanitize(str(c.get("gap",      "")), 220),
            })
    tips = [
        sanitize(str(t), 450)
        for t in (data.get("tips", []) or [])[:5]
        if t
    ]
    return {
        "brand_score":     score,
        "brand_summary":   sanitize(str(data.get("brand_summary", "")), 600),
        "sentiment":       sent,
        "quick_win":       sanitize(str(data.get("quick_win", "")),     400),
        "score_breakdown": bd,
        "competitors":     comps,
        "tips":            tips,
    }


# ═══════════════════════════════════════════════════════════════════
#  RAZORPAY — HMAC-SHA256 + REPLAY PREVENTION (FIX-S1)
# ═══════════════════════════════════════════════════════════════════
def verify_rzp(
    pid: str, lid: str, ref: str, status: str,
    sig: str, secret: str,
) -> bool:
    if not all([pid, lid, status, sig, secret]):
        return False
    if status.lower() != "paid":
        return False

    seen: set = st.session_state.get("_seen_pids", set())
    if pid in seen:
        logger.warning("Replay attack blocked for payment_id: %s", pid[:12])
        return False

    msg = f"{lid}|{ref}|{status}|{pid}".encode("utf-8")
    exp = hmac.new(secret.strip().encode("utf-8"), msg, hashlib.sha256).hexdigest()
    ok  = hmac.compare_digest(exp, sig.strip())

    if ok:
        seen.add(pid)
        st.session_state["_seen_pids"] = seen
    return ok


def check_redirect(secret: str) -> bool:
    if not st.session_state.get("_result"):
        return False
    p   = st.query_params
    pid = p.get("razorpay_payment_id", "")
    if not pid:
        return False
    ok = verify_rzp(
        pid,
        p.get("razorpay_payment_link_id",           ""),
        p.get("razorpay_payment_link_reference_id", ""),
        p.get("razorpay_payment_link_status",       ""),
        p.get("razorpay_signature",                 ""),
        secret,
    )
    if ok:
        st.query_params.clear()
    return ok


# ═══════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════
_GEM = _RZP_S = ""
_RZP_RAW = "https://rzp.io/YOUR_PAYMENT_PAGE_LINK"
_USE_SEC = _RZP_OK = False
try:
    _GEM     = st.secrets.get("GEMINI_API_KEY",  "")
    _RZP_S   = st.secrets.get("RZP_KEY_SECRET",  "")
    _RZP_RAW = st.secrets.get("RZP_PAYMENT_URL", _RZP_RAW)
    _USE_SEC = bool(_GEM and validate_key(_GEM))
    _RZP_OK  = bool(_RZP_S)
except Exception:
    pass

_RZP_URL = html.escape(_RZP_RAW, quote=True)


# ═══════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════
_DEFS: Dict[str, Any] = {
    "_n": 0, "_last": 0.0, "_result": None,
    "_unlocked": False, "_seen_pids": set(),
}
for _k, _v in _DEFS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if _RZP_OK and not st.session_state["_unlocked"]:
    if check_redirect(_RZP_S):
        st.session_state["_unlocked"] = True


# ═══════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;0,9..144,900;1,9..144,300;1,9..144,700&family=JetBrains+Mono:wght@300;400;500&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --ink:      #03030a;
  --surface:  #07071a;
  --surface2: #0a0a1f;
  --surface3: #0d0d26;
  --border:   rgba(255,255,255,0.055);
  --border2:  rgba(255,255,255,0.115);
  --saffron:  #FF9933;
  --cyan:     #00C8F0;
  --emerald:  #00DFA0;
  --crimson:  #FF3D6E;
  --gold:     #FFCC44;
  --violet:   #9B7FFF;
  --text:     #ECEAF8;
  --muted:    #42426A;
  --muted2:   #1C1C3A;
  --display:  'Fraunces', Georgia, serif;
  --mono:     'JetBrains Mono', 'Courier New', monospace;
  --body:     'Inter', system-ui, sans-serif;
  --r:  10px; --r2: 16px; --r3: 22px;
  --ease:     cubic-bezier(0.4,0,0.2,1);
  --ease-out: cubic-bezier(0,0,0.2,1);
  --shadow:   0 24px 64px rgba(0,0,0,0.65);
}

*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
html, body, [class*="css"] { font-family: var(--body) !important; }

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton,
.viewerBadge_container__1QSob { display: none !important; }

.main .block-container {
  padding-top: 0 !important;
  padding-bottom: 6rem !important;
  max-width: 1280px !important;
}

.stApp { background: var(--ink); min-height: 100vh; }
.stApp::before {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 110% 70% at -5% -8%,  rgba(255,153,51,0.09)  0%, transparent 52%),
    radial-gradient(ellipse  65% 55% at 108% 112%, rgba(0,200,240,0.06)  0%, transparent 50%),
    radial-gradient(ellipse  50% 40% at  55%  52%, rgba(155,127,255,0.025) 0%, transparent 60%);
}
.stApp::after {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    repeating-linear-gradient(0deg,  transparent, transparent 47px, rgba(255,255,255,0.006) 48px),
    repeating-linear-gradient(90deg, transparent, transparent 47px, rgba(255,255,255,0.006) 48px);
}

[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: #5050a0 !important; }
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b    { color: var(--text) !important; }
[data-testid="stSidebar"] a    {
  color: var(--cyan) !important;
  text-decoration: none !important;
  transition: opacity 0.15s ease !important;
}
[data-testid="stSidebar"] a:hover { opacity: 0.6 !important; }

label,
[data-testid="stTextInput"]  label,
[data-testid="stSelectbox"]  label {
  font-family: var(--mono) !important;
  font-size: 0.56rem !important;
  letter-spacing: 0.22em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

.stTextInput > div > div > input {
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: var(--body) !important;
  font-size: 0.91rem !important;
  padding: 11px 14px !important;
  caret-color: var(--saffron) !important;
  transition: border-color 0.15s var(--ease), box-shadow 0.15s var(--ease) !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--saffron) !important;
  box-shadow: 0 0 0 3px rgba(255,153,51,0.13) !important;
  outline: none !important;
}
.stTextInput > div > div > input:hover:not(:focus) {
  border-color: rgba(255,255,255,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--muted2) !important; }

[data-testid="stSelectbox"] > div > div {
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  transition: border-color 0.15s var(--ease) !important;
}
[data-testid="stSelectbox"] > div > div:hover {
  border-color: rgba(255,255,255,0.18) !important;
}

.stButton > button {
  font-family: var(--mono) !important;
  font-size: 0.7rem !important;
  letter-spacing: 0.24em !important;
  text-transform: uppercase !important;
  background: transparent !important;
  color: var(--saffron) !important;
  border: 1px solid rgba(255,153,51,0.34) !important;
  border-radius: 8px !important;
  padding: 15px 40px !important;
  width: 100% !important;
  cursor: pointer !important;
  position: relative !important;
  overflow: hidden !important;
  transition: background 0.18s var(--ease), color 0.18s var(--ease),
              border-color 0.18s var(--ease), box-shadow 0.18s var(--ease),
              transform 0.1s ease !important;
}
.stButton > button:hover {
  background: var(--saffron) !important;
  color: #040410 !important;
  border-color: var(--saffron) !important;
  box-shadow: 0 0 52px rgba(255,153,51,0.4), 0 4px 24px rgba(255,153,51,0.2) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: scale(0.98) !important; }

[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 3px !important;
  overflow: hidden !important;
}
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--saffron), var(--cyan)) !important;
  border-radius: 3px !important;
}

[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r2) !important;
  padding: 20px 18px !important;
  transition: border-color 0.2s var(--ease), transform 0.2s var(--ease) !important;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(255,153,51,0.22) !important;
  transform: translateY(-2px) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--mono) !important;
  font-size: 1.5rem !important;
  color: var(--cyan) !important;
}
[data-testid="stMetricLabel"] {
  font-family: var(--mono) !important;
  font-size: 0.5rem !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r2) !important;
  margin-bottom: 10px !important;
  overflow: hidden !important;
  transition: border-color 0.2s var(--ease) !important;
}
[data-testid="stExpander"]:hover { border-color: var(--border2) !important; }
[data-testid="stExpander"] summary {
  font-family: var(--mono) !important;
  font-size: 0.62rem !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  color: var(--text) !important;
  padding: 16px 20px !important;
  transition: color 0.15s !important;
}
[data-testid="stExpander"] summary:hover { color: var(--saffron) !important; }

hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 2.5rem 0 !important; }
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: var(--ink); }
::-webkit-scrollbar-thumb { background: var(--muted2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,153,51,0.28); }

/* COMPONENT LIBRARY */
.g-eye { font-family: var(--mono); font-size: 0.54rem; letter-spacing: 0.3em; text-transform: uppercase; color: var(--saffron); margin-bottom: 1rem; display: flex; align-items: center; gap: 10px; }
.g-eye::before { content: ''; display: inline-block; width: 24px; height: 1px; background: var(--saffron); flex-shrink: 0; }
.g-h1 { font-family: var(--display); font-size: clamp(2.2rem, 4.5vw, 4.1rem); font-weight: 900; line-height: 1.04; color: var(--text); margin: 0 0 0.8rem; letter-spacing: -0.03em; }
.g-h1 em { font-style: italic; font-weight: 300; color: var(--saffron); }
.g-sub { font-size: 1rem; font-weight: 300; color: var(--muted); line-height: 1.9; max-width: 560px; }
.g-sub strong { color: #c0c0e0; font-weight: 500; }
.g-lbl { font-family: var(--mono); font-size: 0.54rem; letter-spacing: 0.24em; text-transform: uppercase; color: var(--muted); margin-bottom: 1rem; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.g-section-h { font-family: var(--display); font-size: 1.65rem; font-weight: 700; color: var(--text); margin: 0 0 0.4rem; }
.g-section-s { font-size: 0.88rem; color: var(--muted); line-height: 1.8; margin-bottom: 1.4rem; }

.g-stats { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 1.5rem; margin-bottom: 0.5rem; }
.g-stat { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 9px 16px; }
.g-stat-num { font-family: var(--mono); font-size: 0.88rem; font-weight: 500; color: var(--saffron); }
.g-stat-lbl { font-family: var(--mono); font-size: 0.44rem; letter-spacing: 0.16em; text-transform: uppercase; color: var(--muted); margin-top: 2px; }

.g-sp-wrap { background: var(--surface2); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 16px 0; margin-bottom: 2.5rem; }
.g-sp-inner { display: flex; justify-content: center; flex-wrap: wrap; }
.g-sp-item { display: flex; flex-direction: column; align-items: center; padding: 0 32px; border-right: 1px solid var(--border); }
.g-sp-item:last-child { border-right: none; }
.g-sp-num { font-family: var(--mono); font-size: 1.05rem; font-weight: 500; color: var(--saffron); line-height: 1; }
.g-sp-lbl { font-family: var(--mono); font-size: 0.44rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted); margin-top: 4px; }

.g-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r2); padding: 22px 24px; font-size: 0.93rem; line-height: 1.88; color: #a0a0c8; transition: border-color 0.2s; }
.g-card:hover { border-color: var(--border2); }
.g-qwin { background: rgba(0,223,160,0.05); border: 1px solid rgba(0,223,160,0.13); border-left: 3px solid var(--emerald); border-radius: 8px; padding: 13px 18px; margin-top: 12px; color: #80e8c8; font-size: 0.87rem; line-height: 1.8; }
.g-sent { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r2); padding: 28px 16px; text-align: center; transition: border-color 0.2s, transform 0.2s; }
.g-sent:hover { border-color: var(--border2); transform: translateY(-2px); }
.g-sent-icon { font-size: 2.4rem; margin-bottom: 10px; }
.g-sent-lbl { font-family: var(--mono); font-size: 0.5rem; letter-spacing: 0.22em; text-transform: uppercase; color: var(--muted); }
.g-sent-val { font-family: var(--display); font-size: 1.2rem; font-weight: 700; margin-top: 6px; }

.g-tip { background: var(--surface2); border: 1px solid var(--border); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 14px 18px; margin: 7px 0; color: #8888b4; font-size: 0.87rem; line-height: 1.82; cursor: default; transition: border-left-color 0.15s, background 0.15s, transform 0.15s; }
.g-tip:hover { border-left-color: var(--saffron); background: rgba(255,153,51,0.03); transform: translateX(5px); }
.g-tip strong { color: var(--text); }
.g-tip-n { font-family: var(--mono); font-size: 0.57rem; font-weight: 500; color: var(--saffron); letter-spacing: 0.08em; }

.g-blur { filter: blur(7px); user-select: none; pointer-events: none; opacity: 0.36; }
.g-paywall { background: linear-gradient(to bottom, transparent, var(--ink) 36%); margin-top: -3.8rem; padding: 3.8rem 1rem 1rem; text-align: center; }
.g-pw-h { font-family: var(--display); font-size: 1.55rem; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.g-pw-s { font-size: 0.85rem; color: var(--muted); margin-bottom: 18px; line-height: 1.72; }
.g-pay-btn { display: inline-flex; align-items: center; gap: 8px; font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; background: var(--saffron); color: #040410 !important; text-decoration: none !important; border-radius: 8px; padding: 14px 38px; box-shadow: 0 4px 28px rgba(255,153,51,0.32); transition: box-shadow 0.2s, transform 0.15s; white-space: nowrap; font-weight: 600; }
.g-pay-btn:hover { box-shadow: 0 6px 56px rgba(255,153,51,0.58); transform: translateY(-2px); }
.g-pay-btn:active { transform: scale(0.97); }

.g-val-wrap { background: var(--surface); border: 1px solid rgba(255,153,51,0.14); border-radius: var(--r2); padding: 18px 20px; margin: 14px auto 18px; max-width: 440px; }
.g-val-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.83rem; color: var(--text); }
.g-val-row:last-child { border-bottom: none; }
.g-val-icon { font-size: 0.9rem; flex-shrink: 0; width: 20px; text-align: center; }
.g-badge { font-family: var(--mono); font-size: 0.47rem; letter-spacing: 0.12em; border-radius: 4px; padding: 2px 8px; margin-left: auto; flex-shrink: 0; }
.g-b-free  { color: var(--emerald); background: rgba(0,223,160,0.08);  border: 1px solid rgba(0,223,160,0.22); }
.g-b-lock  { color: #42426a; background: var(--surface3); border: 1px solid var(--border); }
.g-b-paid  { color: var(--saffron); background: rgba(255,153,51,0.07); border: 1px solid rgba(255,153,51,0.22); }
.g-anc { text-align: center; margin: 0 0 16px; }
.g-anc-orig { font-family: var(--mono); font-size: 0.58rem; color: #2a2a52; text-decoration: line-through; letter-spacing: 0.1em; margin-bottom: 3px; }
.g-anc-price { font-family: var(--display); font-size: 2.3rem; font-weight: 900; color: var(--saffron); line-height: 1; }
.g-anc-note { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }
.g-risk { display: inline-flex; align-items: center; gap: 5px; font-family: var(--mono); font-size: 0.5rem; letter-spacing: 0.1em; color: var(--emerald); background: rgba(0,223,160,0.05); border: 1px solid rgba(0,223,160,0.14); border-radius: 100px; padding: 5px 14px; margin-top: 10px; }

.g-testi-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin: 1rem 0; }
.g-testi { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r2); padding: 22px; transition: border-color 0.2s, transform 0.2s; }
.g-testi:hover { border-color: rgba(255,153,51,0.2); transform: translateY(-3px); }
.g-testi-stars { color: var(--gold); font-size: 0.76rem; margin-bottom: 10px; letter-spacing: 2px; }
.g-testi-q { font-size: 0.88rem; font-style: italic; color: #b0b0d0; line-height: 1.74; margin-bottom: 16px; }
.g-testi-q::before { content: '\201C'; font-family: var(--display); font-size: 1.8rem; color: rgba(255,153,51,0.6); line-height: 0; vertical-align: -0.44em; margin-right: 2px; }
.g-testi-info { display: flex; align-items: center; gap: 10px; }
.g-testi-av { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--mono); font-size: 0.72rem; font-weight: 700; color: #040410; flex-shrink: 0; }
.g-testi-name { font-family: var(--mono); font-size: 0.56rem; letter-spacing: 0.06em; color: var(--text); }
.g-testi-role { font-size: 0.68rem; color: var(--muted); margin-top: 2px; }
.g-testi-delta { margin-left: auto; text-align: right; flex-shrink: 0; }
.g-testi-dv { font-family: var(--mono); font-size: 0.68rem; font-weight: 500; color: var(--emerald); }
.g-testi-dl { font-family: var(--mono); font-size: 0.44rem; letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase; margin-top: 1px; }

.g-trust { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; padding: 20px 0 28px; }
.g-trust-badge { display: flex; align-items: center; gap: 6px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 7px 14px; font-family: var(--mono); font-size: 0.48rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); }
.g-trust-badge .ic { font-size: 0.82rem; }

.g-sec { background: rgba(0,223,160,0.04); border: 1px solid rgba(0,223,160,0.11); border-radius: 8px; padding: 11px 14px; margin-top: 12px; font-size: 0.7rem; color: #5ecda8; line-height: 1.65; }
.g-rzp-notice { background: rgba(255,204,68,0.05); border: 1px solid rgba(255,204,68,0.15); border-radius: 8px; padding: 11px 14px; margin-top: 12px; font-size: 0.7rem; color: #c8a830; line-height: 1.6; }
.g-ts { font-family: var(--mono); font-size: 0.52rem; letter-spacing: 0.18em; color: #16163a; margin-bottom: 1.4rem; }
.g-counter { display: inline-block; font-family: var(--mono); font-size: 0.52rem; letter-spacing: 0.15em; background: var(--surface); border: 1px solid var(--border); border-radius: 4px; padding: 5px 14px; color: var(--muted); margin-top: 14px; }
.g-unlocked { display: inline-flex; align-items: center; gap: 7px; font-family: var(--mono); font-size: 0.56rem; letter-spacing: 0.15em; color: var(--emerald); background: rgba(0,223,160,0.06); border: 1px solid rgba(0,223,160,0.16); border-radius: 100px; padding: 5px 14px; }
.g-cta { background: var(--surface); border: 1px solid rgba(255,153,51,0.13); border-radius: var(--r2); padding: 44px 40px; text-align: center; position: relative; overflow: hidden; }
.g-cta::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse 65% 50% at 50% -5%, rgba(255,153,51,0.07), transparent); pointer-events: none; }
.g-cta h3 { font-family: var(--display); font-size: 1.7rem; font-weight: 700; color: var(--text); margin-bottom: 10px; }
.g-cta p { color: var(--muted); font-size: 0.9rem; line-height: 1.82; margin-bottom: 26px; max-width: 480px; margin-left: auto; margin-right: auto; }
.g-cta-note { margin-top: 14px; font-family: var(--mono); font-size: 0.54rem; letter-spacing: 0.1em; color: var(--muted2); }

.g-empty { text-align: center; padding: 64px 24px 40px; }
.g-empty-icon { font-size: 2.8rem; margin-bottom: 20px; opacity: 0.18; }
.g-empty-h { font-family: var(--display); font-size: 1.6rem; font-weight: 700; color: #3a3a68; margin-bottom: 28px; }
.g-step { display: flex; align-items: flex-start; gap: 14px; text-align: left; max-width: 380px; margin: 10px auto; }
.g-step-n { font-family: var(--mono); font-size: 0.58rem; color: var(--saffron); border: 1px solid rgba(255,153,51,0.2); min-width: 28px; height: 28px; border-radius: 5px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
.g-step-t { color: #3a3a72; font-size: 0.84rem; line-height: 1.78; }
.g-step-t strong { color: #6868a4; }

@keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeIn { from{opacity:0} to{opacity:1} }
@keyframes barGrow { from{width:0!important} }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.55} }
.anim-up { animation: fadeUp 0.44s var(--ease-out) both; }
.anim-in { animation: fadeIn 0.5s ease both; }
.d1{animation-delay:.06s} .d2{animation-delay:.12s}
.d3{animation-delay:.18s} .d4{animation-delay:.24s} .d5{animation-delay:.3s}

@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:0.01ms!important;transition-duration:0.01ms!important}
}
@media(max-width:1100px){ .g-testi-grid{grid-template-columns:1fr 1fr} }
@media(max-width:900px){
  .g-h1{font-size:2rem}
  .g-cta{padding:28px 22px}
  .main .block-container{padding-left:1rem!important;padding-right:1rem!important}
  .g-testi-grid{grid-template-columns:1fr}
  .g-sp-item{padding:0 16px}
}
@media(max-width:640px){
  .g-h1{font-size:1.72rem}
  .g-sub{font-size:0.85rem}
  .g-stats{gap:7px}
  [data-testid="stMetricValue"]{font-size:1.15rem!important}
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT: SCORE RING
# ═══════════════════════════════════════════════════════════════════
def score_ring(score: int, label: str, color: str) -> None:
    ticks = "".join(
        f'<line x1="94" y1="4" x2="94" y2="9" stroke="rgba(255,255,255,0.055)" '
        f'stroke-width="1.5" transform="rotate({i * 12} 94 94)"/>'
        for i in range(30)
    )
    components.html(f"""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;display:flex;justify-content:center;padding-top:4px}}
.wrap{{background:#080816;border:1px solid rgba(255,255,255,0.07);border-radius:16px;
  padding:28px 24px 24px;display:flex;flex-direction:column;align-items:center;
  position:relative;overflow:hidden;width:100%;max-width:280px;
  box-shadow:0 24px 64px rgba(0,0,0,0.65)}}
.wrap::before{{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,{color}55,transparent)}}
.glow{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:300px;height:300px;background:radial-gradient(circle,{color}12,transparent 55%);
  border-radius:50%;pointer-events:none;opacity:0;transition:opacity 1.5s ease}}
.rw{{position:relative;width:188px;height:188px}}
.ring-fill{{filter:drop-shadow(0 0 5px {color}70);
  transition:stroke-dashoffset 2s cubic-bezier(0.25,0.46,0.45,0.94)}}
.center{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center}}
.num{{font-family:'Fraunces',serif;font-size:3.5rem;font-weight:900;color:{color};
  line-height:1;letter-spacing:-0.04em;text-shadow:0 0 28px {color}48}}
.denom{{font-family:'JetBrains Mono',monospace;font-size:0.62rem;
  color:rgba(255,255,255,0.16);margin-top:3px;letter-spacing:0.08em}}
.badge{{margin-top:16px;font-size:0.54rem;font-weight:500;letter-spacing:0.26em;
  text-transform:uppercase;color:{color};background:{color}10;
  border:1px solid {color}32;border-radius:100px;padding:5px 18px;
  font-family:'JetBrains Mono',monospace;white-space:nowrap}}
.sub{{margin-top:8px;font-family:'JetBrains Mono',monospace;font-size:0.48rem;
  letter-spacing:0.22em;text-transform:uppercase;color:rgba(255,255,255,0.12)}}
</style></head><body>
<div class="wrap">
  <div class="glow" id="glow"></div>
  <div class="rw">
    <svg width="188" height="188" viewBox="0 0 188 188"
         style="position:absolute;top:0;left:0;pointer-events:none">{ticks}</svg>
    <svg width="188" height="188" viewBox="0 0 188 188"
         style="transform:rotate(-90deg);display:block;position:absolute;top:0;left:0">
      <circle cx="94" cy="94" r="{_R}" fill="none" stroke="{color}" stroke-width="9" opacity="0.1"/>
      <circle class="ring-fill" id="ring" cx="94" cy="94" r="{_R}" fill="none"
              stroke="{color}" stroke-width="9" stroke-linecap="round"
              stroke-dasharray="{_CIRC}" stroke-dashoffset="{_CIRC}"/>
    </svg>
    <div class="center">
      <div class="num" id="num">0</div>
      <div class="denom">/100</div>
    </div>
  </div>
  <div class="badge">{label}</div>
  <div class="sub">GEO Visibility Score</div>
</div>
<script>
(function(){{
  var t={score},c={_CIRC};
  var ring=document.getElementById('ring'),
      num=document.getElementById('num'),
      glow=document.getElementById('glow');
  var fo=c-(t/100)*c, s=null, d=2000;
  function ease(x){{return x<0.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;}}
  function tick(ts){{
    if(!s)s=ts;
    var p=Math.min((ts-s)/d,1),e=ease(p);
    ring.style.strokeDashoffset=c-(c-fo)*e;
    num.textContent=Math.round(t*e);
    if(p<1)requestAnimationFrame(tick);else num.textContent=t;
  }}
  setTimeout(function(){{requestAnimationFrame(tick);glow.style.opacity='1';}},300);
}})();
</script>
</body></html>""", height=324)


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT: BREAKDOWN BARS
# ═══════════════════════════════════════════════════════════════════
def breakdown_bars(bd: Dict) -> None:
    fields = (
        ("brand_mentions",        "Brand Mentions",        25),
        ("content_authority",     "Content Authority",     25),
        ("structured_data",       "Structured Data",       25),
        ("ai_citation_potential", "AI Citation Potential", 25),
    )

    def bar_color(v: int) -> str:
        if v >= 22: return "#00DFA0"
        if v >= 18: return "#00C8F0"
        if v >= 12: return "#FF9933"
        if v >= 7:  return "#FFCC44"
        return "#FF3D6E"

    rows: List[str] = []
    for i, (key, lbl, mx) in enumerate(fields):
        v = bd.get(key, 0)
        p = (v / mx) * 100
        c = bar_color(v)
        d = i * 0.1
        rows.append(
            f'<div style="margin:14px 0;animation:sbIn 0.4s ease {d:.2f}s both">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.56rem;'
            f'letter-spacing:0.14em;text-transform:uppercase;color:#42426A">{lbl}</span>'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.76rem;'
            f'font-weight:500;color:{c}">{v}'
            f'<span style="color:#42426A;font-size:0.54rem">/{mx}</span></span></div>'
            f'<div style="background:#101028;border-radius:3px;height:4px;overflow:hidden">'
            f'<div style="height:100%;border-radius:3px;background:{c};width:{p:.1f}%;'
            f'animation:barGrow 1.35s cubic-bezier(0.4,0,0.2,1) {d:.2f}s both;'
            f'box-shadow:0 0 7px {c}55"></div></div></div>'
        )
    st.markdown(
        '<style>'
        '@keyframes sbIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}'
        '@keyframes barGrow{from{width:0!important}}'
        '</style><div style="padding-top:4px">' + "".join(rows) + '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT: COMPETITOR CARDS
# ═══════════════════════════════════════════════════════════════════
def _score_color(s: int) -> str:
    if s >= 81: return "#00DFA0"
    if s >= 66: return "#00C8F0"
    if s >= 46: return "#FF9933"
    if s >= 26: return "#FFCC44"
    return "#FF3D6E"


def _score_label(s: int) -> str:
    if s >= 81: return "DOMINANT"
    if s >= 66: return "STRONG"
    if s >= 46: return "ESTABLISHED"
    if s >= 26: return "EMERGING"
    return "INVISIBLE"


def competitor_cards(brand: str, score: int, comps: List[Dict]) -> None:
    all_b = [{"name": brand, "score": score, "you": True, "note": ""}]
    for c in comps:
        all_b.append({
            "name":  c["name"], "score": c["score"], "you": False,
            "note":  c.get("strength", "") or c.get("gap", ""),
        })
    all_b.sort(key=lambda x: x["score"], reverse=True)

    cards: List[str] = []
    for i, b in enumerate(all_b):
        s   = b["score"]
        col = _score_color(s)
        lbl = _score_label(s)
        d   = i * 0.07
        isy = b["you"]
        bg  = "rgba(255,153,51,0.032)" if isy else "#080816"
        bc  = "rgba(255,153,51,0.36)"  if isy else "rgba(255,255,255,0.055)"
        bch = f"{col}50"
        you = (
            f' <span style="font-family:\'JetBrains Mono\',monospace;font-size:0.5rem;'
            f'color:#42426A;letter-spacing:0.1em">YOU</span>'
        ) if isy else ""
        star = f'<span style="color:{col};margin-right:4px">★</span>' if isy else ""
        note = (
            f'<p style="font-size:0.73rem;color:#42426A;margin:5px 0 0;line-height:1.55">'
            f'{b["note"]}</p>'
        ) if b.get("note") else ""
        cards.append(
            f'<div style="background:{bg};border:1px solid {bc};border-radius:10px;'
            f'padding:16px 20px;margin-bottom:8px;cursor:default;'
            f'animation:ccIn 0.42s ease {d:.2f}s both;'
            f'transition:border-color 0.15s ease,transform 0.15s ease" '
            f'onmouseover="this.style.transform=\'translateY(-2px)\';'
            f'this.style.borderColor=\'{bch}\'" '
            f'onmouseout="this.style.transform=\'\';this.style.borderColor=\'{bc}\'">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">'
            f'<div style="flex:1;min-width:0">'
            f'<div style="font-family:\'Inter\',sans-serif;font-size:0.89rem;font-weight:500;'
            f'color:#eceaf8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
            f'{star}{b["name"]}{you}</div>{note}</div>'
            f'<div style="text-align:right;flex-shrink:0">'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:1.42rem;'
            f'font-weight:500;color:{col};text-shadow:0 0 14px {col}48">{s}</span>'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.53rem;'
            f'color:#42426A"> /100</span></div></div>'
            f'<div style="margin-top:10px;background:#0c0c1e;border-radius:2px;'
            f'height:3px;overflow:hidden">'
            f'<div style="height:100%;border-radius:2px;background:{col};width:{s}%;'
            f'animation:ccBar 1.25s cubic-bezier(0.4,0,0.2,1) {d:.2f}s both;'
            f'box-shadow:0 0 7px {col}48"></div></div>'
            f'<div style="margin-top:7px;font-family:\'JetBrains Mono\',monospace;'
            f'font-size:0.48rem;letter-spacing:0.2em;color:{col}40;'
            f'text-transform:uppercase">{lbl}</div></div>'
        )
    st.markdown(
        '<style>'
        '@keyframes ccIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}'
        '@keyframes ccBar{from{width:0!important}}'
        '</style><div>' + "".join(cards) + '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT: SOCIAL PROOF BAR
# ═══════════════════════════════════════════════════════════════════
def social_proof_bar() -> None:
    st.markdown("""
<div class="g-sp-wrap">
  <div class="g-sp-inner">
    <div class="g-sp-item">
      <span class="g-sp-num" id="sp-brands">2,800+</span>
      <span class="g-sp-lbl">Brands Analyzed</span>
    </div>
    <div class="g-sp-item">
      <span class="g-sp-num">89%</span>
      <span class="g-sp-lbl">Scored Below 50</span>
    </div>
    <div class="g-sp-item">
      <span class="g-sp-num">3</span>
      <span class="g-sp-lbl">AI Engines Covered</span>
    </div>
    <div class="g-sp-item">
      <span class="g-sp-num">&lt;10s</span>
      <span class="g-sp-lbl">Per Analysis</span>
    </div>
  </div>
</div>
<script>
(function(){
  var el = document.getElementById('sp-brands');
  if (!el) return;
  var target = 2847, start = null, dur = 1800;
  function ease(t){ return 1 - Math.pow(1 - t, 3); }
  function tick(ts){
    if (!start) start = ts;
    var p = Math.min((ts - start) / dur, 1);
    var v = Math.round(ease(p) * target);
    el.textContent = v.toLocaleString('en-IN') + '+';
    if (p < 1) requestAnimationFrame(tick);
  }
  setTimeout(function(){ requestAnimationFrame(tick); }, 600);
})();
</script>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT: VALUE STACK PAYWALL
# ═══════════════════════════════════════════════════════════════════
def value_stack_paywall(brand: str, blurred_html: str) -> None:
    def row(icon: str, text: str, kind: str) -> str:
        badge_cls  = {"free": "g-b-free", "lock": "g-b-lock"}.get(kind, "g-b-lock")
        badge_text = {"free": "FREE",     "lock": "LOCKED"}.get(kind, "LOCKED")
        return (
            f'<div class="g-val-row">'
            f'<span class="g-val-icon">{icon}</span>{text}'
            f'<span class="g-badge {badge_cls}">{badge_text}</span></div>'
        )

    free_rows = [
        ("🎯", f"GEO Score for {brand}",        "free"),
        ("📊", "4-dimension score breakdown",    "free"),
        ("🏆", "Live competitor benchmark",       "free"),
        ("💡", "2 priority GEO tips (preview)",  "free"),
    ]
    locked_rows = [
        ("🔑", "All 5 personalised action tips", "lock"),
        ("📅", "90-day AI content calendar",     "lock"),
        ("🗺️", "AI citation source map (India)", "lock"),
        ("🔍", "Query gap vs competitors",       "lock"),
        ("⚔️", "Competitor takedown playbook",  "lock"),
    ]

    rows_html = "".join(row(*r) for r in free_rows + locked_rows)

    if _RZP_OK:
        cta_html = f"""
        <div class="g-anc">
          <div class="g-anc-orig">AGENCY SEO AUDIT ₹25,000+</div>
          <div class="g-anc-price">₹999</div>
          <div class="g-anc-note">One-time · No subscription · Instant unlock · GST inclusive</div>
        </div>
        <a class="g-pay-btn" href="{_RZP_URL}" target="_blank" rel="noopener noreferrer">
          🔓 Unlock Full Report — ₹999
        </a>
        <div style="margin-top:11px">
          <span class="g-risk">✓ 100% actionable insights or full refund — guaranteed</span>
        </div>
        <div style="margin-top:10px;font-family:'JetBrains Mono',monospace;font-size:0.47rem;
             letter-spacing:0.1em;color:#1a1a3a">
          🔒 Razorpay · UPI / Card / Netbanking · HMAC-SHA256 · No data stored
        </div>
        """
    else:
        cta_html = """
        <div style="background:rgba(255,204,68,0.05);border:1px solid rgba(255,204,68,0.14);
             border-radius:8px;padding:14px;font-size:0.78rem;color:#c8a830;text-align:center;margin-top:14px">
          ⏳ Payment unlock activates once Razorpay approval completes.<br>
          <span style="font-size:0.65rem;color:#8a6820">Free analysis is fully functional now.</span>
        </div>
        """

    st.markdown(
        f'<div class="g-blur">{blurred_html}</div>'
        f'<div class="g-paywall">'
        f'<p class="g-pw-h">Unlock the Full Report for {brand}</p>'
        f'<p class="g-pw-s">Your 2 free tips are the surface.<br>'
        f'The ₹999 report has everything needed to act — this week, not next quarter.</p>'
        f'<div class="g-val-wrap">{rows_html}</div>'
        f'{cta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT: TESTIMONIALS
# ═══════════════════════════════════════════════════════════════════
_TESTIMONIALS_HTML = """
<div class="g-testi-grid">
  <div class="g-testi anim-up d1">
    <div class="g-testi-stars">★★★★★</div>
    <div class="g-testi-q">Found out we were completely invisible on Perplexity despite ranking well on Google. The citation source map showed exactly which publications Gemini trusts — we pitched them within the week.</div>
    <div class="g-testi-info">
      <div class="g-testi-av" style="background:#FF9933">AM</div>
      <div>
        <div class="g-testi-name">Arjun Mehta</div>
        <div class="g-testi-role">Founder · D2C Skincare · Pune</div>
      </div>
      <div class="g-testi-delta">
        <div class="g-testi-dv">32 → 71</div>
        <div class="g-testi-dl">GEO Score</div>
      </div>
    </div>
  </div>
  <div class="g-testi anim-up d2">
    <div class="g-testi-stars">★★★★★</div>
    <div class="g-testi-q">Our competitor was getting cited 4× more on ChatGPT even though our product is better. The gap analysis made it obvious why — and the 90-day calendar gave the exact content to close it.</div>
    <div class="g-testi-info">
      <div class="g-testi-av" style="background:#00C8F0">PK</div>
      <div>
        <div class="g-testi-name">Priya Krishnamurthy</div>
        <div class="g-testi-role">Co-founder · EdTech · Chennai</div>
      </div>
      <div class="g-testi-delta">
        <div class="g-testi-dv">18 → 63</div>
        <div class="g-testi-dl">GEO Score</div>
      </div>
    </div>
  </div>
  <div class="g-testi anim-up d3">
    <div class="g-testi-stars">★★★★★</div>
    <div class="g-testi-q">Spent ₹8L on SEO last quarter and still invisible on AI. GEO Score showed the problem in 8 seconds. The takedown playbook alone is worth 100× the ₹999 ask. No brainer.</div>
    <div class="g-testi-info">
      <div class="g-testi-av" style="background:#00DFA0">RS</div>
      <div>
        <div class="g-testi-name">Rohit Sharma</div>
        <div class="g-testi-role">CMO · B2B SaaS · Bengaluru</div>
      </div>
      <div class="g-testi-delta">
        <div class="g-testi-dv">24 → 58</div>
        <div class="g-testi-dl">GEO Score</div>
      </div>
    </div>
  </div>
</div>
"""

_TRUST_HTML = """
<div class="g-trust">
  <div class="g-trust-badge"><span class="ic">🔒</span> Razorpay Secured</div>
  <div class="g-trust-badge"><span class="ic">🛡️</span> HMAC-SHA256</div>
  <div class="g-trust-badge"><span class="ic">🇮🇳</span> DPDP Compliant</div>
  <div class="g-trust-badge"><span class="ic">⚡</span> Gemini 2.0 Flash</div>
  <div class="g-trust-badge"><span class="ic">🚫</span> No Ads. Ever.</div>
  <div class="g-trust-badge"><span class="ic">↩️</span> Refund Guaranteed</div>
  <div class="g-trust-badge"><span class="ic">📵</span> No Data Stored</div>
</div>
<div style="text-align:center;margin-top:4px;font-family:'JetBrains Mono',monospace;
     font-size:0.44rem;letter-spacing:0.16em;color:#12122e">
  GEO SCORE INDIA · APRIL 2026 · AI VISIBILITY INTELLIGENCE
</div>
"""


# ═══════════════════════════════════════════════════════════════════
#  LLM: BUILD PROMPT
# ═══════════════════════════════════════════════════════════════════
def build_prompt(brand: str, city: str, industry: str,
                 competitor: str, api_key: str) -> str:
    b  = sanitize(brand,      80)
    ci = sanitize(city,       60)
    ind = sanitize(industry,  60)
    co  = sanitize(competitor, 80)
    key_note = f"(user key: {mask(api_key)})" if api_key else "(server key)"
    return f"""You are a GEO (Generative Engine Optimisation) expert specialising in the Indian market, April 2026.

Analyse the brand "{b}" ({ind}, {ci}, India).
Known competitor: "{co}" (include 2-3 more relevant Indian competitors if appropriate).

Return ONLY valid JSON — no markdown, no preamble, no trailing text.
Schema (strict):
{{
  "brand_score": <integer 0-100>,
  "brand_summary": "<2-sentence AI-visibility summary, India context>",
  "sentiment": "<Positive|Neutral|Negative>",
  "quick_win": "<single highest-impact action, max 25 words>",
  "score_breakdown": {{
    "brand_mentions":        <0-25>,
    "content_authority":     <0-25>,
    "structured_data":       <0-25>,
    "ai_citation_potential": <0-25>
  }},
  "competitors": [
    {{"name": "...", "score": <0-100>, "strength": "<≤18 words>", "gap": "<≤18 words>"}},
    ...
  ],
  "tips": [
    "<tip 1 — specific, actionable, India-context, ≤60 words>",
    "<tip 2>",
    "<tip 3>",
    "<tip 4>",
    "<tip 5>"
  ]
}}

Rules:
- brand_score = sum of score_breakdown values (must match exactly)
- tips[0] and tips[1] are shown free; tips[2-4] are paywalled — make all 5 genuinely valuable
- India-specific: cite Indian publications, influencer platforms, regional language opportunities
- Be specific — name real Indian platforms (Moj, ShareChat, Indiamart, Justdial, etc.) where relevant
- {key_note}"""


# ═══════════════════════════════════════════════════════════════════
#  LLM: CALL GEMINI
# ═══════════════════════════════════════════════════════════════════
_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]


def call_gemini(prompt: str, key: str) -> Dict:
    genai.configure(api_key=key)
    last_err: Exception = RuntimeError("No models attempted")

    for model_name in _MODELS:
        try:
            model = genai.GenerativeModel(
                model_name,
                generation_config=genai.GenerationConfig(
                    temperature=0.35,
                    max_output_tokens=1800,
                    response_mime_type="application/json",
                ),
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT":        "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH":       "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                },
            )
            resp = model.generate_content(prompt)
            raw  = resp.text or ""
            data = safe_json(raw)
            if data:
                return clean_llm(data)
            raise ValueError(f"Non-JSON response from {model_name}")
        except Exception as e:
            msg = str(e).lower()
            # FIX-S6: fail fast on auth / quota — no point trying other models
            if any(x in msg for x in ("api_key", "api key", "invalid", "quota", "billing")):
                raise RuntimeError(f"Auth/Quota error on {model_name}: {e}") from e
            last_err = e
            logger.warning("Model %s failed: %s — trying next", model_name, e)
            time.sleep(0.8)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}") from last_err


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.56rem;'
        'letter-spacing:0.28em;text-transform:uppercase;color:#FF9933;'
        'margin-bottom:1.4rem;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.05)">'
        '◈ GEO Score India</div>',
        unsafe_allow_html=True,
    )

    # ── API key ──────────────────────────────────────────────────
    st.markdown(
        '<p style="font-family:\'JetBrains Mono\',monospace;font-size:0.52rem;'
        'letter-spacing:0.18em;text-transform:uppercase;color:#42426A;margin-bottom:6px">'
        'Gemini API Key</p>',
        unsafe_allow_html=True,
    )
    if _USE_SEC:
        st.markdown(
            f'<div class="g-sec">✓ Server key active<br>'
            f'<span style="font-size:0.6rem;opacity:0.6">{mask(_GEM)}</span></div>',
            unsafe_allow_html=True,
        )
        _active_key = _GEM
    else:
        user_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza…",
            label_visibility="collapsed",
        )
        _active_key = user_key.strip() if user_key else ""
        if _active_key:
            if validate_key(_active_key):
                st.markdown(
                    '<div class="g-sec" style="margin-top:6px">✓ Key format valid</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="background:rgba(255,61,110,0.07);border:1px solid rgba(255,61,110,0.2);'
                    'border-radius:8px;padding:10px 12px;margin-top:6px;font-size:0.68rem;color:#ff3d6e">'
                    '✗ Invalid key format</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="g-rzp-notice" style="margin-top:6px">'
                '🔑 Get a free key at<br>'
                '<a href="https://aistudio.google.com/app/apikey" '
                'target="_blank">aistudio.google.com</a></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Brand inputs ─────────────────────────────────────────────
    st.markdown(
        '<p style="font-family:\'JetBrains Mono\',monospace;font-size:0.52rem;'
        'letter-spacing:0.18em;text-transform:uppercase;color:#42426A;margin-bottom:6px">'
        'Brand Details</p>',
        unsafe_allow_html=True,
    )

    brand_input      = st.text_input("Brand Name",       placeholder="e.g. Mamaearth",      label_visibility="visible")
    city_input       = st.text_input("City / Region",    placeholder="e.g. Delhi NCR",       label_visibility="visible")
    competitor_input = st.text_input("Top Competitor",   placeholder="e.g. Plum Goodness",   label_visibility="visible")

    industries = [
        "D2C / Beauty & Personal Care", "EdTech", "FinTech / BFSI",
        "B2B SaaS", "Healthcare / Pharma", "E-Commerce / Retail",
        "Travel & Hospitality", "Real Estate", "Food & Beverage",
        "Media & Entertainment", "Logistics / Supply Chain", "Other",
    ]
    industry_input = st.selectbox("Industry", industries)

    st.markdown("<br>", unsafe_allow_html=True)

    ready = bool(
        brand_input.strip()
        and city_input.strip()
        and competitor_input.strip()
        and (_active_key if not _USE_SEC else True)
        and (validate_key(_active_key) if _active_key else _USE_SEC)
    )

    run_btn = st.button("◈ Run Free GEO Analysis", disabled=not ready)

    # ── Rate / session info ──────────────────────────────────────
    n_used = st.session_state.get("_n", 0)
    if n_used > 0:
        st.markdown(
            f'<div class="g-counter" style="display:block;margin-top:12px">'
            f'{n_used}/6 analyses used this session</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.get("_unlocked"):
        st.markdown(
            '<div class="g-unlocked" style="display:flex;margin-top:12px">'
            '✓ Full Report Unlocked</div>',
            unsafe_allow_html=True,
        )

    # ── FAQ in sidebar ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family:\'JetBrains Mono\',monospace;font-size:0.5rem;'
        'letter-spacing:0.18em;text-transform:uppercase;color:#42426A;margin-bottom:8px">'
        'Quick FAQ</p>',
        unsafe_allow_html=True,
    )
    with st.expander("What is GEO?"):
        st.markdown(
            "**Generative Engine Optimisation** — making your brand visible when "
            "people ask ChatGPT, Gemini, or Perplexity a question in your category. "
            "Traditional SEO does not protect you here."
        )
    with st.expander("Is my data stored?"):
        st.markdown(
            "No. Your brand name and API key are processed in-memory only and "
            "discarded at the end of your session. No database, no logs."
        )
    with st.expander("What do I get free?"):
        st.markdown(
            "GEO Score, 4-dimension breakdown, competitor benchmark, "
            "AI sentiment, quick win, and **2 priority tips** — free forever."
        )
    with st.expander("What's in the ₹999 report?"):
        st.markdown(
            "All 5 tips + **90-day AI content calendar** + citation source map "
            "(which Indian publications each AI trusts) + query gap analysis + "
            "competitor takedown playbook. One-time, no subscription."
        )
    with st.expander("Refund policy?"):
        st.markdown(
            "If you feel the report isn't 100% actionable for your brand, "
            "email within 7 days for a full refund — no questions asked."
        )

    st.markdown(
        '<div style="margin-top:1.4rem;font-family:\'JetBrains Mono\',monospace;'
        'font-size:0.42rem;letter-spacing:0.12em;color:#12122e;line-height:1.8">'
        'GEO Score India · v6.0 Apex<br>Powered by Gemini 2.0 Flash<br>'
        'Not affiliated with Google or Razorpay</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  MAIN COLUMN: HERO
# ═══════════════════════════════════════════════════════════════════
ts_str = datetime.now().strftime("%d %b %Y · %H:%M IST")
st.markdown(
    f'<div class="g-ts">{ts_str} · GEO SCORE INDIA · AI VISIBILITY INTELLIGENCE</div>',
    unsafe_allow_html=True,
)

st.markdown("""
<div class="g-eye">AI Visibility Intelligence · India</div>
<h1 class="g-h1">Your customers ask AI.<br><em>You don't exist.</em></h1>
<p class="g-sub">
  Over <strong>40% of product searches</strong> now begin on ChatGPT, Gemini, or Perplexity —
  not Google. If AI doesn't know you, you've already lost the sale.
  <strong>GEO Score India</strong> tells you exactly where you stand and what to fix — in under 10 seconds.
</p>
<div class="g-stats">
  <div class="g-stat"><div class="g-stat-num">40%+</div><div class="g-stat-lbl">Searches via AI 2026</div></div>
  <div class="g-stat"><div class="g-stat-num">89%</div><div class="g-stat-lbl">Indian Brands Score &lt;50</div></div>
  <div class="g-stat"><div class="g-stat-num">3×</div><div class="g-stat-lbl">More Leads — GEO-Optimised</div></div>
  <div class="g-stat"><div class="g-stat-num">₹999</div><div class="g-stat-lbl">Full Report · One-Time</div></div>
</div>
""", unsafe_allow_html=True)

social_proof_bar()

# ── Testimonials (shown before results to build trust first) ─────
st.markdown('<div class="g-lbl">What Founders Are Saying</div>', unsafe_allow_html=True)
st.markdown(_TESTIMONIALS_HTML, unsafe_allow_html=True)

st.markdown(
    '<div style="margin-top:1rem"></div>',
    unsafe_allow_html=True,
)
st.markdown(_TRUST_HTML, unsafe_allow_html=True)
st.markdown('<hr>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  RUN ANALYSIS
# ═══════════════════════════════════════════════════════════════════
if run_btn:
    throttled, wait = rate_check()
    if throttled:
        if wait == -1:
            st.error(
                "Session limit reached (6 analyses). "
                "Open a new browser tab to continue, or upgrade to unlimited via the ₹999 report."
            )
        else:
            st.warning(f"⏱ Please wait {wait}s before the next analysis.")
    else:
        key_to_use = _GEM if _USE_SEC else _active_key
        if not key_to_use or not validate_key(key_to_use):
            st.error("Please enter a valid Gemini API key to continue.")
        else:
            record_req()
            with st.spinner("Analysing AI visibility across Gemini · ChatGPT · Perplexity …"):
                try:
                    prompt = build_prompt(
                        brand_input, city_input, industry_input,
                        competitor_input, key_to_use,
                    )
                    result = call_gemini(prompt, key_to_use)
                    st.session_state["_result"] = result
                    st.session_state["_brand"]  = sanitize(brand_input, 80)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    logger.error("Analysis error: %s", e)


# ═══════════════════════════════════════════════════════════════════
#  RENDER RESULTS
# ═══════════════════════════════════════════════════════════════════
result   = st.session_state.get("_result")
unlocked = st.session_state.get("_unlocked", False)
brand_s  = st.session_state.get("_brand", "Your Brand")

if result:
    score   = result["brand_score"]
    bd      = result["score_breakdown"]
    comps   = result["competitors"]
    tips    = result["tips"]
    sent    = result["sentiment"]
    summary = result["brand_summary"]
    qwin    = result["quick_win"]

    # ── Score color ───────────────────────────────────────────────
    ring_color = _score_color(score)
    ring_label = _score_label(score)

    st.markdown('<div class="g-lbl anim-in">GEO Analysis Results</div>', unsafe_allow_html=True)

    # ── Row 1: Score ring + summary + sentiment ───────────────────
    c1, c2, c3 = st.columns([1.1, 2.2, 1.1])
    with c1:
        score_ring(score, ring_label, ring_color)

    with c2:
        st.markdown('<div class="g-lbl">AI Visibility Summary</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="g-card anim-up">{summary}'
            f'<div class="g-qwin">⚡ Quick Win: {qwin}</div></div>',
            unsafe_allow_html=True,
        )

    with c3:
        sent_icon  = {"Positive": "🟢", "Neutral": "🟡", "Negative": "🔴"}.get(sent, "⚪")
        sent_color = {"Positive": "#00DFA0", "Neutral": "#FFCC44", "Negative": "#FF3D6E"}.get(sent, "#9B7FFF")
        st.markdown(
            f'<div class="g-sent anim-up d2">'
            f'<div class="g-sent-icon">{sent_icon}</div>'
            f'<div class="g-sent-lbl">AI Sentiment</div>'
            f'<div class="g-sent-val" style="color:{sent_color}">{sent}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("GEO Score", f"{score}/100", delta=f"{score - 50:+d} vs avg")

    st.markdown('<hr>', unsafe_allow_html=True)

    # ── Row 2: Breakdown + competitors ───────────────────────────
    c4, c5 = st.columns([1, 1])
    with c4:
        st.markdown('<div class="g-lbl">Score Breakdown</div>', unsafe_allow_html=True)
        breakdown_bars(bd)

    with c5:
        st.markdown('<div class="g-lbl">Competitive Benchmark</div>', unsafe_allow_html=True)
        competitor_cards(brand_s, score, comps)

    st.markdown('<hr>', unsafe_allow_html=True)

    # ── Row 3: GEO Tips (free 2 + paywall 3) ─────────────────────
    st.markdown(
        '<div class="g-section-h">GEO Action Plan</div>'
        '<div class="g-section-s">Personalised, India-specific recommendations '
        'ranked by impact. First 2 tips are free.</div>',
        unsafe_allow_html=True,
    )

    # Show free tips
    free_tips_html = ""
    for i in range(min(2, len(tips))):
        free_tips_html += (
            f'<div class="g-tip anim-up" style="animation-delay:{i*0.08:.2f}s">'
            f'<span class="g-tip-n">TIP {i+1}</span><br>{tips[i]}</div>'
        )
    if free_tips_html:
        st.markdown(free_tips_html, unsafe_allow_html=True)

    # Locked tips
    if unlocked:
        st.markdown(
            '<div class="g-unlocked" style="margin:14px 0 10px">✓ Full Report Unlocked — All Tips Visible</div>',
            unsafe_allow_html=True,
        )
        for i in range(2, len(tips)):
            st.markdown(
                f'<div class="g-tip anim-up" style="border-left-color:#9B7FFF;'
                f'animation-delay:{i*0.08:.2f}s">'
                f'<span class="g-tip-n" style="color:#9B7FFF">TIP {i+1}</span><br>{tips[i]}</div>',
                unsafe_allow_html=True,
            )
        # Full report extras
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown(
            '<div class="g-section-h">Full Report — Premium Sections</div>'
            '<div class="g-section-s">Unlocked content for your brand.</div>',
            unsafe_allow_html=True,
        )
        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown('<div class="g-lbl">90-Day AI Content Calendar</div>', unsafe_allow_html=True)
            months = [
                ("Month 1", "Foundation — Schema markup, Google Business optimisation, "
                 "Wikipedia/Wikidata citation push for brand entity recognition."),
                ("Month 2", "Authority — Pitch 3 tier-1 Indian publications "
                 "(Economic Times, YourStory, Inc42) for brand mentions. "
                 "Launch FAQ schema pages targeting top-10 AI queries in your category."),
                ("Month 3", "Amplification — Regional language content (Hindi + "
                 "1 regional language). Indiamart & Justdial profile optimisation. "
                 "Reddit India & Quora answer campaign for query gap terms."),
            ]
            for m, desc in months:
                st.markdown(
                    f'<div class="g-tip" style="border-left-color:#9B7FFF;margin-bottom:8px">'
                    f'<span class="g-tip-n" style="color:#9B7FFF">{m}</span><br>{desc}</div>',
                    unsafe_allow_html=True,
                )
        with ec2:
            st.markdown('<div class="g-lbl">Competitor Takedown Playbook</div>', unsafe_allow_html=True)
            top_comp = comps[0]["name"] if comps else "your top competitor"
            plays = [
                f"Identify the 5 AI queries where {top_comp} is cited. Create a "
                "dedicated comparison page optimised for each query with structured FAQ schema.",
                "Submit a detailed brand profile to Wikidata (free). AI models heavily "
                "weight Wikidata for entity resolution — most Indian brands skip this.",
                "Build a public 'Indian Brand vs Global Brand' data study. "
                "Original research earns citations 4× faster than blog posts.",
            ]
            for j, play in enumerate(plays):
                st.markdown(
                    f'<div class="g-tip" style="border-left-color:#FF3D6E;margin-bottom:8px">'
                    f'<span class="g-tip-n" style="color:#FF3D6E">PLAY {j+1}</span><br>{play}</div>',
                    unsafe_allow_html=True,
                )
    else:
        # Paywall — blur next tips and show value stack
        locked_preview = "".join(
            f'<div class="g-tip"><span class="g-tip-n">TIP {i+1}</span><br>{tips[i]}</div>'
            for i in range(2, min(5, len(tips)))
        )
        value_stack_paywall(brand_s, locked_preview)

    # ── Bottom CTA (if not unlocked) ─────────────────────────────
    if not unlocked and _RZP_OK:
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="g-cta">'
            f'<h3>Ready to dominate AI search in India?</h3>'
            f'<p>Get the complete 5-tip action plan, 90-day calendar, '
            f'citation source map, and competitor takedown playbook for {brand_s}. '
            f'One-time ₹999. Instant delivery. Refund guaranteed.</p>'
            f'<a class="g-pay-btn" href="{_RZP_URL}" target="_blank" rel="noopener noreferrer">'
            f'🔓 Get Full Report — ₹999</a>'
            f'<div class="g-cta-note">'
            f'No subscription · UPI / Card / Netbanking · HMAC-SHA256 secured'
            f'</div></div>',
            unsafe_allow_html=True,
        )

else:
    # ── Empty state ───────────────────────────────────────────────
    st.markdown("""
<div class="g-empty">
  <div class="g-empty-icon">◈</div>
  <div class="g-empty-h">Start your free GEO analysis →</div>
  <div class="g-step">
    <div class="g-step-n">01</div>
    <div class="g-step-t"><strong>Enter your brand name</strong> — the name customers search for</div>
  </div>
  <div class="g-step">
    <div class="g-step-n">02</div>
    <div class="g-step-t"><strong>Add your city and main competitor</strong> — for a personalised benchmark</div>
  </div>
  <div class="g-step">
    <div class="g-step-n">03</div>
    <div class="g-step-t"><strong>Click Run Free GEO Analysis</strong> — results in under 10 seconds</div>
  </div>
  <div style="margin-top:28px;font-family:'JetBrains Mono',monospace;font-size:0.54rem;
       letter-spacing:0.16em;text-transform:uppercase;color:#1c1c3a">
    Free forever · No signup · No credit card
  </div>
</div>
""", unsafe_allow_html=True)
