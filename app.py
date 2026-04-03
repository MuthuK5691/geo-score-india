"""
GEO SCORE INDIA — Main App v2.0
Streamlit entrypoint. Integrates geo_ai_engine.py
Run: streamlit run app.py
"""

import streamlit as st
from geo_ai_engine import init_session, run_analysis_safely, render_results

# ── Page config (must be first Streamlit call) ──────────────
st.set_page_config(
    page_title="GEO Score India",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — matches your existing dark aesthetic ───────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #0f172a; }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  .stTextInput > div > input {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
  }
  .stSelectbox > div > div {
    background: #1e293b;
    color: #e2e8f0;
  }
  .stButton > button {
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 0.6rem 1.2rem;
    width: 100%;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #fb923c, #f97316);
    transform: translateY(-1px);
  }
  .stMetric { background: #1e293b; border-radius: 8px; padding: 12px; }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ───────────────────────────────────────
init_session()


# ── Sidebar — inputs ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 GEO Score India")
    st.caption("AI Visibility Intelligence")
    st.markdown("---")

    brand = st.text_input(
        "BRAND NAME",
        placeholder="e.g. Mamaearth",
        value="",
    )

    city = st.text_input(
        "CITY / REGION",
        placeholder="e.g. Chennai",
        value="",
    )

    competitor = st.text_input(
        "TOP COMPETITOR",
        placeholder="e.g. Plum Goodness",
        value="",
    )

    industry = st.selectbox(
        "INDUSTRY",
        options=[
            "D2C / Beauty & Personal Care",
            "FMCG / Consumer Goods",
            "EdTech",
            "FinTech / BFSI",
            "HealthTech / Wellness",
            "Food & Beverage",
            "Fashion & Apparel",
            "Real Estate",
            "Automobile",
            "SaaS / B2B Tech",
            "E-commerce / Marketplace",
            "Media & Entertainment",
            "Other",
        ],
    )

    st.markdown("---")
    run_clicked = st.button("◆ RUN FREE GEO ANALYSIS")

    st.markdown("---")

    # FAQ section
    with st.expander("▶ WHAT IS GEO?"):
        st.markdown(
            "Generative Engine Optimization — how visible your brand is "
            "when consumers ask AI tools like ChatGPT, Gemini, or Perplexity "
            "instead of searching Google."
        )

    with st.expander("▶ IS MY DATA STORED?"):
        st.markdown(
            "Brand names are sent to AI providers for analysis only. "
            "No personal data is collected or stored by this app."
        )

    with st.expander("▶ WHICH AI RUNS THIS?"):
        provider = st.session_state.get("provider_used")
        if provider:
            provider_display = {
                "groq": "Groq — Llama 3.3 70B (fastest)",
                "gemini": "Google — Gemini 2.5 Flash-Lite",
                "openrouter": "OpenRouter — DeepSeek/Llama 4",
                "none": "All providers unavailable",
            }
            st.markdown(f"Last analysis used: **{provider_display.get(provider, provider)}**")
        else:
            st.markdown(
                "Groq (primary) → Gemini 2.5 Flash-Lite → OpenRouter. "
                "Automatically falls back if any provider is unavailable."
            )


# ── Main content area ────────────────────────────────────────
col_main, _ = st.columns([3, 1])

with col_main:
    # Hero (shown before first analysis)
    if not st.session_state.get("geo_result"):
        st.markdown("""
<div style="padding: 2rem 0;">
  <p style="color:#94a3b8;font-size:0.75rem;letter-spacing:0.15em;margin-bottom:0.5rem;">
    AI VISIBILITY INTELLIGENCE · INDIA
  </p>
  <h1 style="font-size:2.8rem;font-weight:700;line-height:1.1;margin-bottom:0;">
    Your customers ask AI.
  </h1>
  <h2 style="font-size:2.8rem;font-weight:700;color:#f97316;font-style:italic;margin-top:0;">
    You don't exist.
  </h2>
  <p style="color:#94a3b8;max-width:560px;line-height:1.7;margin-top:1rem;">
    Over <strong style="color:#f1f5f9">40% of product searches</strong> now begin on ChatGPT, 
    Gemini, or Perplexity — not Google. If AI doesn't know you, you've already lost the sale.
    <strong style="color:#f97316">GEO Score India</strong> tells you exactly where you stand 
    and what to fix — free.
  </p>
</div>
""", unsafe_allow_html=True)

        # Stats row
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("40%+", "Searches via AI 2026")
        s2.metric("89%", "Indian Brands Score <50")
        s3.metric("3×", "More Leads — GEO-Optimised")
        s4.metric("2,800+", "Brands Analyzed")

    # Run analysis when button clicked
    if run_clicked:
        result = run_analysis_safely(brand, city, competitor, industry)
        if result and not result.get("error"):
            st.markdown("---")
            render_results(result)
        elif result.get("error"):
            st.error(f"Analysis failed: {result.get('error_message')}")

    # Show previous result if available and button not clicked this run
    elif st.session_state.get("geo_result") and not run_clicked:
        result = st.session_state["geo_result"]
        if not result.get("error"):
            st.markdown("---")
            render_results(result)
