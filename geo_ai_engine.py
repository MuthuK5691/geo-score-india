"""
GEO SCORE INDIA — AI ENGINE v2.0
Multi-provider fallback chain. Zero single point of failure.
Groq (primary) → Gemini 2.5 Flash-Lite (fallback) → OpenRouter (emergency)

Free tier capacity per day:
  Groq Llama 3.3 70B    : 1,000 req/day @ 30 RPM
  Gemini 2.5 Flash-Lite : 1,000 req/day @ 15 RPM
  OpenRouter free        :   200 req/day @ 20 RPM
  ─────────────────────────────────────────────
  Total effective ceiling: ~2,200 req/day free

Root cause fixed: gemini-2.0-flash retired March 3 2026. Endpoint dead.
All providers here are stable and verified as of April 2026.
"""

import os
import time
import json
import hashlib
import requests
import streamlit as st
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
# SECTION 1 — SECRETS & CONFIG
# Create .streamlit/secrets.toml with:
#   GROQ_API_KEY = "gsk_..."
#   GEMINI_API_KEY = "AIza..."
#   OPENROUTER_API_KEY = "sk-or-..."  (optional, free signup)
# All three keys are free. No credit card needed for any.
# ─────────────────────────────────────────────────────────────

PROVIDER_PRIORITY = ["groq", "gemini", "openrouter"]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",   # Best quality, 1000 RPD
    "llama3-70b-8192",           # Older but stable fallback
    "llama3-8b-8192",            # Fast, 14400 RPD — emergency
]

# FIX: gemini-2.5-flash-lite-preview-06-17 does not exist (future date).
# gemini-2.5-flash-lite is the stable released model as of April 2026.
GEMINI_MODEL = "gemini-2.5-flash-lite"

OPENROUTER_MODELS = [
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-4-maverick:free",
    "qwen/qwen3-235b-a22b:free",
]


def _get_secret(key: str, fallback_env: bool = True) -> Optional[str]:
    """Pull from st.secrets first, then os.environ. Never crash silently."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        if fallback_env:
            return os.environ.get(key)
        return None


# ─────────────────────────────────────────────────────────────
# SECTION 2 — CACHING LAYER
# ─────────────────────────────────────────────────────────────

def _cache_key(brand: str, city: str, competitor: str, industry: str) -> str:
    raw = f"{brand.lower().strip()}|{city.lower().strip()}|{competitor.lower().strip()}|{industry.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


@st.cache_data(ttl=3600, show_spinner=False)
def get_geo_analysis(brand: str, city: str, competitor: str, industry: str) -> dict:
    """
    PUBLIC ENTRY POINT. Always call this, never the internal functions.
    Cache hit = zero API calls. Cache miss = goes through provider chain.
    """
    return _run_provider_chain(brand, city, competitor, industry)


# ─────────────────────────────────────────────────────────────
# SECTION 3 — PROMPT
# ─────────────────────────────────────────────────────────────

def _build_prompt(brand: str, city: str, competitor: str, industry: str) -> tuple:
    system = """You are an AI Generative Engine Optimization (GEO) analyst specializing in Indian brands.
GEO measures how visible a brand is when Indian consumers ask AI assistants (ChatGPT, Gemini, Perplexity, Claude) questions.

CRITICAL: Respond ONLY in valid JSON. Zero markdown. Zero explanation. Zero preamble.
If you don't have confident data on a brand, score conservatively (30-45) and flag gaps.

Required JSON structure (every field mandatory):
{
  "geo_score": <integer 0-100>,
  "grade": "<A|B|C|D|F>",
  "score_breakdown": {
    "ai_mentions": <0-25, how often AI mentions this brand>,
    "factual_authority": <0-25, Wikipedia/press coverage quality>,
    "query_coverage": <0-25, what % of category queries return brand>,
    "trust_signals": <0-25, reviews, certifications, structured data>
  },
  "vs_competitor": {
    "brand_score": <integer>,
    "competitor_score": <integer>,
    "gap": <integer, positive means brand leads>,
    "verdict": "<one clear sentence>"
  },
  "critical_gaps": [
    "<specific gap 1>",
    "<specific gap 2>",
    "<specific gap 3>"
  ],
  "quick_wins": [
    "<specific action with timeline>",
    "<specific action with timeline>",
    "<specific action with timeline>"
  ],
  "top_queries_to_target": [
    "<exact query Indian users ask AI>",
    "<exact query Indian users ask AI>",
    "<exact query Indian users ask AI>"
  ],
  "city_specific_insight": "<one sentence about this city's AI query patterns for this category>",
  "risk_level": "<low|medium|high>",
  "ai_readiness": "<not_ready|developing|competitive|leading>",
  "summary": "<2-3 sentence executive summary a founder can act on today>"
}"""

    user = f"""Analyze GEO visibility for this Indian brand:

Brand: {brand}
City/Region: {city}
Top Competitor: {competitor}
Industry: {industry}

Score based on: Wikipedia presence, press coverage depth, structured data availability,
review platform authority, social proof density, content that AI systems typically cite.
For less-known brands: score 25-45 with honest gap analysis.
For established brands: score based on actual digital authority signals."""

    return system, user


# ─────────────────────────────────────────────────────────────
# SECTION 4 — PROVIDER CHAIN
# ─────────────────────────────────────────────────────────────

def _run_provider_chain(brand: str, city: str, competitor: str, industry: str) -> dict:
    system_prompt, user_prompt = _build_prompt(brand, city, competitor, industry)
    errors = []

    for provider in PROVIDER_PRIORITY:
        try:
            if provider == "groq":
                result = _call_groq(system_prompt, user_prompt)
            elif provider == "gemini":
                result = _call_gemini(system_prompt, user_prompt)
            elif provider == "openrouter":
                result = _call_openrouter(system_prompt, user_prompt)
            else:
                continue

            if result and "geo_score" in result:
                result["_provider"] = provider
                result["_timestamp"] = datetime.now().isoformat()
                return result

        except ProviderSkipError as e:
            errors.append(f"{provider}: {str(e)}")
            continue
        except Exception as e:
            errors.append(f"{provider}: {str(e)}")
            continue

    return {
        "error": True,
        "error_message": "All providers unavailable. Check your API keys.",
        "error_detail": " | ".join(errors),
        "geo_score": 0,
        "_provider": "none",
    }


class ProviderSkipError(Exception):
    """Raised when a provider should be skipped (no key, quota, etc.)"""
    pass


# ─────────────────────────────────────────────────────────────
# PROVIDER 1 — GROQ
# ─────────────────────────────────────────────────────────────

def _call_groq(system_prompt: str, user_prompt: str) -> dict:
    api_key = _get_secret("GROQ_API_KEY")
    if not api_key:
        raise ProviderSkipError("GROQ_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1200,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(3):
            try:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if resp.status_code == 429:
                    break  # Try next model

                if resp.status_code == 401:
                    raise ProviderSkipError("Invalid GROQ_API_KEY")

                if resp.status_code == 200:
                    data = resp.json()
                    raw = data["choices"][0]["message"]["content"]
                    return _parse_json_response(raw)

                time.sleep(2 ** attempt)

            except requests.Timeout:
                if attempt == 2:
                    break
                time.sleep(2)
            except (KeyError, IndexError):
                break

    raise ProviderSkipError("Groq quota exhausted across all models")


# ─────────────────────────────────────────────────────────────
# PROVIDER 2 — GEMINI 2.5 FLASH-LITE (stable)
# Model string: gemini-2.5-flash-lite
# 1,000 req/day, 15 RPM on free tier via AI Studio.
# ─────────────────────────────────────────────────────────────

def _call_gemini(system_prompt: str, user_prompt: str) -> dict:
    api_key = _get_secret("GEMINI_API_KEY")
    if not api_key:
        raise ProviderSkipError("GEMINI_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1200,
            "responseMimeType": "application/json",
        },
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                url,
                params={"key": api_key},
                json=payload,
                timeout=30,
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                if attempt < 2:
                    time.sleep(min(retry_after, 30))
                    continue
                raise ProviderSkipError("Gemini quota exhausted")

            if resp.status_code == 400:
                error_msg = resp.json().get("error", {}).get("message", "")
                if "deprecated" in error_msg.lower() or "not found" in error_msg.lower():
                    raise ProviderSkipError(f"Gemini model unavailable: {error_msg}")
                raise ProviderSkipError(f"Gemini bad request: {error_msg}")

            if resp.status_code == 403:
                raise ProviderSkipError("Gemini API key invalid or region blocked")

            if resp.status_code == 200:
                data = resp.json()
                raw = data["candidates"][0]["content"]["parts"][0]["text"]
                return _parse_json_response(raw)

            time.sleep(2 ** attempt)

        except requests.Timeout:
            if attempt == 2:
                raise ProviderSkipError("Gemini timeout")
            time.sleep(3)

    raise ProviderSkipError("Gemini failed after retries")


# ─────────────────────────────────────────────────────────────
# PROVIDER 3 — OPENROUTER (Emergency fallback)
# ─────────────────────────────────────────────────────────────

def _call_openrouter(system_prompt: str, user_prompt: str) -> dict:
    api_key = _get_secret("OPENROUTER_API_KEY")
    if not api_key:
        raise ProviderSkipError("OPENROUTER_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://geo-score-india.streamlit.app",
        "X-Title": "GEO Score India",
    }

    for model in OPENROUTER_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + "\n\nRespond ONLY with JSON."},
            ],
            "temperature": 0.3,
            "max_tokens": 1200,
        }

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45,
            )

            if resp.status_code == 429:
                continue

            if resp.status_code == 401:
                raise ProviderSkipError("Invalid OPENROUTER_API_KEY")

            if resp.status_code == 200:
                data = resp.json()
                raw = data["choices"][0]["message"]["content"]
                return _parse_json_response(raw)

        except requests.Timeout:
            continue

    raise ProviderSkipError("OpenRouter: all free models exhausted")


# ─────────────────────────────────────────────────────────────
# SECTION 5 — JSON PARSER
# ─────────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    """Strip any markdown formatting and parse JSON safely."""
    if not raw or not raw.strip():
        raise ValueError("Empty response from AI provider")

    text = raw.strip()

    if text.startswith("\ufeff"):
        text = text[1:]

    if "```json" in text:
        text = text.split("```json", 1)[1]
        text = text.rsplit("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1]
        text = text.rsplit("```", 1)[0]

    text = text.strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse failed: {e}. Raw (first 200 chars): {raw[:200]}")

    required = ["geo_score", "score_breakdown", "critical_gaps", "quick_wins", "summary"]
    missing = [f for f in required if f not in result]
    if missing:
        raise ValueError(f"Response missing required fields: {missing}")

    result["geo_score"] = max(0, min(100, int(result.get("geo_score", 0))))

    return result


# ─────────────────────────────────────────────────────────────
# SECTION 6 — SESSION STATE GUARD
# ─────────────────────────────────────────────────────────────

def init_session():
    """Call once at the top of your Streamlit app."""
    defaults = {
        "geo_result": None,
        "last_input_hash": None,
        "is_analyzing": False,
        "analysis_count": 0,
        "provider_used": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def run_analysis_safely(brand: str, city: str, competitor: str, industry: str) -> dict:
    """Safe entry point for the RUN ANALYSIS button handler."""
    errors = []
    if not brand.strip():
        errors.append("Brand name is required")
    if not competitor.strip():
        errors.append("Competitor name is required")
    if not city.strip():
        errors.append("City/region is required")
    if errors:
        st.error(" | ".join(errors))
        return {}

    input_hash = _cache_key(brand, city, competitor, industry)
    if (
        st.session_state.get("last_input_hash") == input_hash
        and st.session_state.get("geo_result")
    ):
        st.info("Showing cached result for these inputs. Change any field to run fresh analysis.")
        return st.session_state["geo_result"]

    st.session_state["is_analyzing"] = True
    with st.spinner("Analyzing AI visibility across search engines..."):
        result = get_geo_analysis(brand, city, competitor, industry)

    st.session_state["is_analyzing"] = False
    st.session_state["geo_result"] = result
    st.session_state["last_input_hash"] = input_hash
    st.session_state["analysis_count"] += 1

    if result.get("_provider"):
        st.session_state["provider_used"] = result["_provider"]

    return result


# ─────────────────────────────────────────────────────────────
# SECTION 7 — UI RENDERER
# ─────────────────────────────────────────────────────────────

def render_results(result: dict):
    """Render the complete GEO analysis output in Streamlit."""
    if not result:
        return

    if result.get("error"):
        st.error(f"Analysis failed: {result.get('error_message', 'Unknown error')}")
        with st.expander("Technical details"):
            st.code(result.get("error_detail", "No details available"))
        return

    score = result.get("geo_score", 0)
    grade = result.get("grade", _score_to_grade(score))
    breakdown = result.get("score_breakdown", {})
    vs = result.get("vs_competitor", {})

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("GEO Score", f"{score}/100")
        _render_score_bar(score)
    with col2:
        grade_colors = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}
        st.markdown(f"### {grade_colors.get(grade, '⚪')} Grade: {grade}")
    with col3:
        risk = result.get("risk_level", "medium")
        risk_map = {"low": "🟢 Low Risk", "medium": "🟡 Medium Risk", "high": "🔴 High Risk"}
        st.markdown(f"### {risk_map.get(risk, risk)}")

    st.markdown("---")
    st.markdown(f"**Summary:** {result.get('summary', '')}")

    if vs:
        st.markdown("---")
        st.subheader("🥊 vs Competitor")
        c1, c2, c3 = st.columns(3)
        c1.metric("Your Score", vs.get("brand_score", score))
        c2.metric("Competitor Score", vs.get("competitor_score", "N/A"))
        gap = vs.get("gap", 0)
        c3.metric("Gap", f"{abs(gap)} pts", delta=f"{'You lead' if gap >= 0 else 'They lead'}")
        st.info(vs.get("verdict", ""))

    st.markdown("---")
    st.subheader("📊 Score Breakdown")
    breakdown_labels = {
        "ai_mentions": "AI Mentions",
        "factual_authority": "Factual Authority",
        "query_coverage": "Query Coverage",
        "trust_signals": "Trust Signals",
    }
    cols = st.columns(4)
    for i, (key, label) in enumerate(breakdown_labels.items()):
        val = breakdown.get(key, 0)
        cols[i].metric(label, f"{val}/25")
        cols[i].progress(val / 25)

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.subheader("🚨 Critical Gaps")
        for gap in result.get("critical_gaps", []):
            st.error(f"• {gap}")

    with right:
        st.subheader("⚡ Quick Wins")
        for win in result.get("quick_wins", []):
            st.success(f"• {win}")

    st.markdown("---")
    st.subheader("🎯 Top Queries to Target")
    for q in result.get("top_queries_to_target", []):
        st.code(q, language=None)

    city_insight = result.get("city_specific_insight")
    if city_insight:
        st.info(f"📍 **Local Insight:** {city_insight}")

    provider = result.get("_provider", "unknown")
    timestamp = result.get("_timestamp", "")
    st.caption(f"Analysis via: {provider} | {timestamp[:16] if timestamp else 'cached'}")


def _score_to_grade(score: int) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"


def _render_score_bar(score: int):
    if score >= 80:
        color = "#22c55e"
    elif score >= 50:
        color = "#f59e0b"
    else:
        color = "#ef4444"
    st.markdown(
        f"""<div style="background:#1e293b;border-radius:8px;height:12px;margin-top:4px;">
        <div style="background:{color};width:{score}%;height:12px;border-radius:8px;
        transition:width 0.8s ease;"></div></div>""",
        unsafe_allow_html=True,
    )
