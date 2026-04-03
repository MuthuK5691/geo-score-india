"""
GEO SCORE INDIA — Premium UI v3.0
Full custom dark dashboard. Animated. Polished. Zero generic Streamlit look.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from geo_ai_engine import init_session, run_analysis_safely


def _build_hero_html() -> str:
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:wght@300;400&family=Figtree:wght@300;400;500&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { background:#060911; height:100%; overflow:hidden; }

body {
  background: #060911;
  background-image:
    radial-gradient(ellipse 60% 50% at 70% 30%, rgba(245,158,11,0.06) 0%, transparent 70%),
    radial-gradient(ellipse 40% 60% at 20% 80%, rgba(99,102,241,0.04) 0%, transparent 70%);
  font-family: 'Figtree', sans-serif;
  display: flex;
  align-items: center;
  padding: 2.5rem 3rem;
  position: relative;
}

/* Grain overlay */
body::before {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0; opacity: 0.4;
}

.hero { position: relative; z-index: 1; max-width: 660px; }

.eyebrow {
  font-family: 'DM Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.22em;
  color: #F59E0B;
  text-transform: uppercase;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.1s forwards;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.2rem;
}
.eyebrow::before {
  content: '';
  display: inline-block;
  width: 28px; height: 1px;
  background: #F59E0B;
}

.headline {
  font-family: 'Syne', sans-serif;
  font-size: clamp(2.4rem, 5vw, 3.8rem);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.035em;
  color: #EEF2FF;
  opacity: 0;
  animation: fadeUp 0.7s ease 0.25s forwards;
  margin-bottom: 0.3rem;
}
.headline em {
  color: #F59E0B;
  font-style: italic;
}

.subline {
  font-size: 0.95rem;
  color: #3D5070;
  line-height: 1.7;
  max-width: 520px;
  opacity: 0;
  animation: fadeUp 0.7s ease 0.45s forwards;
  margin-top: 1.2rem;
  margin-bottom: 2.5rem;
}
.subline strong { color: #6B7FA3; font-weight: 500; }

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  overflow: hidden;
  opacity: 0;
  animation: fadeUp 0.7s ease 0.6s forwards;
}
.stat {
  background: rgba(11,16,32,0.8);
  padding: 1rem 0.75rem;
  text-align: center;
  transition: background 0.2s;
}
.stat:hover { background: rgba(245,158,11,0.06); }
.stat-num {
  font-family: 'DM Mono', monospace;
  font-size: 1.4rem;
  font-weight: 400;
  color: #F59E0B;
  line-height: 1;
  margin-bottom: 0.3rem;
}
.stat-label {
  font-size: 0.65rem;
  color: #2D3E58;
  letter-spacing: 0.05em;
  font-family: 'DM Mono', monospace;
}

.hint {
  margin-top: 2rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem;
  color: #1E2B40;
  letter-spacing: 0.12em;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.9s forwards;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.hint::after {
  content: '';
  display: inline-block;
  width: 4px; height: 4px;
  background: #F59E0B;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out 1s infinite;
}

@keyframes fadeUp {
  from { opacity:0; transform:translateY(16px); }
  to { opacity:1; transform:translateY(0); }
}
@keyframes pulse {
  0%,100% { opacity:0.3; transform:scale(1); }
  50% { opacity:1; transform:scale(1.5); }
}
</style>
</head>
<body>
<div class="hero">
  <div class="eyebrow">GEO Score India · 2026</div>
  <div class="headline">Your customers ask AI.<br><em>You don't exist.</em></div>
  <p class="subline">
    Over <strong>40% of product searches</strong> now begin on ChatGPT, Gemini, or Perplexity —
    not Google. If AI doesn't know your brand, you've already lost the sale.
    <strong>Find out where you stand.</strong>
  </p>
  <div class="stats">
    <div class="stat">
      <div class="stat-num">40%+</div>
      <div class="stat-label">Searches via AI</div>
    </div>
    <div class="stat">
      <div class="stat-num">89%</div>
      <div class="stat-label">Brands score &lt;50</div>
    </div>
    <div class="stat">
      <div class="stat-num">3×</div>
      <div class="stat-label">More leads (GEO-optimised)</div>
    </div>
    <div class="stat">
      <div class="stat-num">2,800+</div>
      <div class="stat-label">Brands analyzed</div>
    </div>
  </div>
  <div class="hint">← Enter brand details and run your free analysis</div>
</div>
</body>
</html>"""


def _build_results_html(result: dict, brand: str, competitor_name: str) -> str:
    score        = result.get("geo_score", 0)
    grade        = result.get("grade", _grade(score))
    breakdown    = result.get("score_breakdown", {})
    vs           = result.get("vs_competitor", {})
    brand_score  = vs.get("brand_score", score)
    comp_score   = vs.get("competitor_score", 50)
    verdict      = vs.get("verdict", "")
    gap          = vs.get("gap", brand_score - comp_score)
    gaps         = result.get("critical_gaps", [])
    wins         = result.get("quick_wins", [])
    queries      = result.get("top_queries_to_target", [])
    city_insight = result.get("city_specific_insight", "")
    summary      = result.get("summary", "")
    risk         = result.get("risk_level", "medium")
    readiness    = result.get("ai_readiness", "developing")
    provider     = result.get("_provider", "groq")
    timestamp    = (result.get("_timestamp") or "")[:16].replace("T", " · ")

    # Colors
    if score >= 70:   sc, sg = "#10B981", "rgba(16,185,129,0.18)"
    elif score >= 45: sc, sg = "#F59E0B", "rgba(245,158,11,0.18)"
    else:             sc, sg = "#EF4444", "rgba(239,68,68,0.18)"

    grade_colors = {"A":"#10B981","B":"#84CC16","C":"#F59E0B","D":"#F97316","F":"#EF4444"}
    gc = grade_colors.get(grade, "#F59E0B")

    risk_cfg = {"low":("#10B981","LOW RISK"),"medium":("#F59E0B","MEDIUM RISK"),"high":("#EF4444","HIGH RISK")}
    rc, rl = risk_cfg.get(risk, ("#F59E0B","MEDIUM RISK"))

    read_cfg = {"not_ready":("#EF4444","NOT READY"),"developing":("#F59E0B","DEVELOPING"),"competitive":("#10B981","COMPETITIVE"),"leading":("#10B981","LEADING")}
    rdrc, rdrl = read_cfg.get(readiness, ("#F59E0B","DEVELOPING"))

    pmap = {"groq":"Groq · Llama 3.3 70B","gemini":"Gemini 2.5 Flash-Lite","openrouter":"OpenRouter · DeepSeek"}
    pl = pmap.get(provider, provider)

    # SVG ring math (r=72, cx=cy=90, viewBox 180x180)
    R = 72; C = 2 * 3.14159265 * R  # 452.39
    ring_target = C * (1 - score / 100)

    # Breakdown
    bd_items = [
        ("AI Mentions",       breakdown.get("ai_mentions", 0)),
        ("Factual Authority", breakdown.get("factual_authority", 0)),
        ("Query Coverage",    breakdown.get("query_coverage", 0)),
        ("Trust Signals",     breakdown.get("trust_signals", 0)),
    ]

    def bd_row(label, val):
        pct = (val / 25) * 100
        bar_color = "#10B981" if pct >= 70 else "#F59E0B" if pct >= 44 else "#EF4444"
        return f"""<div class="bd-row">
          <div class="bd-label">{label}</div>
          <div class="bd-track"><div class="bd-fill" data-w="{pct:.1f}" style="background:{bar_color};width:0%"></div></div>
          <div class="bd-val" style="color:{bar_color}">{val}<span>/25</span></div>
        </div>"""

    bd_html = "".join(bd_row(l, v) for l, v in bd_items)

    def gap_item(txt):
        return f'<div class="g-item"><div class="g-dot red"></div><div class="g-txt">{txt}</div></div>'
    def win_item(txt):
        return f'<div class="g-item"><div class="g-dot green"></div><div class="g-txt">{txt}</div></div>'
    def query_tag(q):
        return f'<div class="q-tag"><span class="q-arrow">›</span>{q}</div>'

    gaps_html    = "".join(gap_item(g) for g in gaps)
    wins_html    = "".join(win_item(w) for w in wins)
    queries_html = "".join(query_tag(q) for q in queries)

    bs_pct = min(brand_score, 100)
    cs_pct = min(comp_score, 100)
    gap_sign = "+" if gap >= 0 else ""
    gap_color = "#10B981" if gap >= 0 else "#EF4444"

    # Escape for JS
    summary_js = summary.replace('"', '\\"').replace('\n', ' ')

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Figtree:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html{{background:#060911;}}
body{{
  background:#060911;
  background-image:
    radial-gradient(ellipse 80% 40% at 50% 0%, rgba(245,158,11,0.05) 0%,transparent 60%),
    radial-gradient(ellipse 50% 60% at 90% 50%, rgba(99,102,241,0.03) 0%,transparent 60%);
  font-family:'Figtree',sans-serif;
  color:#C8D3E6;
  padding:1.75rem 2rem;
  overflow-x:hidden;
}}
body::before{{
  content:'';position:fixed;inset:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E");
  pointer-events:none;z-index:0;
}}
.dash{{position:relative;z-index:1;max-width:900px;margin:0 auto;}}

/* ── TOP BAR ── */
.topbar{{
  display:flex;justify-content:space-between;align-items:flex-end;
  margin-bottom:1.75rem;
  padding-bottom:1rem;
  border-bottom:1px solid rgba(255,255,255,0.05);
  opacity:0;animation:fadeUp 0.5s ease 0.05s forwards;
}}
.brand-display{{
  font-family:'Syne',sans-serif;
  font-size:1.6rem;font-weight:800;
  letter-spacing:-0.03em;color:#EEF2FF;
}}
.brand-display span{{color:{sc};}}
.meta{{
  font-family:'DM Mono',monospace;
  font-size:0.57rem;letter-spacing:0.1em;
  color:#1E2B40;text-align:right;line-height:1.8;
}}

/* ── HERO ROW ── */
.hero-row{{
  display:grid;
  grid-template-columns:auto 1fr 1fr 1fr;
  gap:1px;
  background:rgba(255,255,255,0.04);
  border-radius:14px;overflow:hidden;
  margin-bottom:1px;
  opacity:0;animation:fadeUp 0.55s ease 0.15s forwards;
}}
.hero-cell{{
  background:#0A0F1E;
  padding:1.5rem 1.25rem;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  transition:background 0.2s;
}}
.hero-cell:hover{{background:#0C1224;}}

/* Score Ring */
.ring-wrap{{position:relative;width:160px;height:160px;}}
.ring-wrap svg{{position:absolute;inset:0;}}
.ring-track{{fill:none;stroke:rgba(255,255,255,0.06);stroke-width:8;}}
.ring-prog{{
  fill:none;stroke:{sc};stroke-width:8;
  stroke-linecap:round;
  stroke-dasharray:{C:.2f};
  stroke-dashoffset:{C:.2f};
  transform-origin:center;
  transform:rotate(-90deg);
  transition:stroke-dashoffset 1.6s cubic-bezier(0.4,0,0.2,1);
  filter:drop-shadow(0 0 8px {sc});
}}
.ring-glow{{
  fill:none;stroke:{sc};stroke-width:16;opacity:0.06;
  stroke-dasharray:{C:.2f};stroke-dashoffset:{C:.2f};
  transform-origin:center;transform:rotate(-90deg);
  transition:stroke-dashoffset 1.6s cubic-bezier(0.4,0,0.2,1);
}}
.ring-center{{
  position:absolute;inset:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
}}
.ring-num{{
  font-family:'DM Mono',monospace;font-size:2rem;font-weight:400;
  color:{sc};line-height:1;
}}
.ring-denom{{font-family:'DM Mono',monospace;font-size:0.6rem;color:#2D3E58;margin-top:1px;}}

/* Grade cell */
.grade-val{{
  font-family:'Syne',sans-serif;
  font-size:3.2rem;font-weight:800;
  color:{gc};
  line-height:1;
  text-shadow:0 0 30px {gc}60;
  margin-bottom:0.35rem;
}}
.cell-label{{
  font-family:'DM Mono',monospace;
  font-size:0.55rem;letter-spacing:0.18em;
  text-transform:uppercase;color:#2D3E58;
}}

/* Risk / readiness badge cells */
.badge-val{{
  font-family:'DM Mono',monospace;
  font-size:0.75rem;font-weight:500;
  letter-spacing:0.12em;
  padding:0.4rem 0.8rem;
  border-radius:6px;
  margin-bottom:0.4rem;
}}

/* ── SUMMARY ── */
.summary-card{{
  background:#0A0F1E;border-radius:14px;
  padding:1.4rem 1.6rem;margin-top:1px;margin-bottom:1px;
  border-left:3px solid {sc};
  opacity:0;animation:fadeUp 0.55s ease 0.3s forwards;
}}
.summary-label{{
  font-family:'DM Mono',monospace;font-size:0.55rem;
  letter-spacing:0.18em;color:#2D3E58;
  text-transform:uppercase;margin-bottom:0.6rem;
}}
.summary-text{{
  font-size:0.9rem;line-height:1.7;color:#8899B8;font-weight:300;
}}

/* ── VS COMPETITOR ── */
.vs-card{{
  background:#0A0F1E;border-radius:14px;
  padding:1.4rem 1.6rem;margin-bottom:1px;
  opacity:0;animation:fadeUp 0.55s ease 0.4s forwards;
}}
.vs-header{{
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:1.2rem;
}}
.section-label{{
  font-family:'DM Mono',monospace;font-size:0.55rem;
  letter-spacing:0.18em;color:#2D3E58;text-transform:uppercase;
}}
.gap-badge{{
  font-family:'DM Mono',monospace;font-size:0.7rem;
  color:{gap_color};letter-spacing:0.05em;
}}
.vs-row{{margin-bottom:0.75rem;}}
.vs-brand-label{{
  display:flex;justify-content:space-between;
  font-size:0.78rem;margin-bottom:0.35rem;
}}
.vs-name{{color:#6B7FA3;}}
.vs-num{{font-family:'DM Mono',monospace;color:#EEF2FF;}}
.vs-track{{background:rgba(255,255,255,0.05);border-radius:4px;height:6px;overflow:hidden;}}
.vs-fill{{height:6px;border-radius:4px;width:0%;transition:width 1.2s cubic-bezier(0.4,0,0.2,1);}}
.verdict{{
  font-size:0.78rem;color:#4A5D7A;line-height:1.5;
  margin-top:0.75rem;padding-top:0.75rem;
  border-top:1px solid rgba(255,255,255,0.04);
  font-style:italic;
}}

/* ── BREAKDOWN ── */
.breakdown-card{{
  background:#0A0F1E;border-radius:14px;
  padding:1.4rem 1.6rem;margin-bottom:1px;
  opacity:0;animation:fadeUp 0.55s ease 0.5s forwards;
}}
.bd-row{{
  display:flex;align-items:center;gap:1rem;
  padding:0.5rem 0;
  border-bottom:1px solid rgba(255,255,255,0.03);
}}
.bd-row:last-child{{border-bottom:none;}}
.bd-label{{
  font-family:'DM Mono',monospace;font-size:0.62rem;
  color:#3D5070;letter-spacing:0.05em;
  width:140px;flex-shrink:0;
}}
.bd-track{{flex:1;background:rgba(255,255,255,0.05);border-radius:3px;height:5px;overflow:hidden;}}
.bd-fill{{height:5px;border-radius:3px;width:0%;transition:width 1.4s cubic-bezier(0.4,0,0.2,1);}}
.bd-val{{
  font-family:'DM Mono',monospace;font-size:0.72rem;
  width:42px;text-align:right;flex-shrink:0;
}}
.bd-val span{{color:#1E2B40;font-size:0.6rem;}}

/* ── GAPS + WINS ── */
.gw-grid{{
  display:grid;grid-template-columns:1fr 1fr;
  gap:1px;margin-bottom:1px;
}}
.gw-card{{
  background:#0A0F1E;
  padding:1.4rem 1.6rem;
  opacity:0;
}}
.gw-card:first-child{{border-radius:14px 0 0 14px;animation:fadeUp 0.55s ease 0.6s forwards;}}
.gw-card:last-child{{border-radius:0 14px 14px 0;animation:fadeUp 0.55s ease 0.65s forwards;}}
.g-item{{
  display:flex;align-items:flex-start;gap:0.75rem;
  padding:0.5rem 0;
  border-bottom:1px solid rgba(255,255,255,0.03);
  font-size:0.8rem;line-height:1.5;color:#5A6F8C;
}}
.g-item:last-child{{border-bottom:none;}}
.g-dot{{
  width:6px;height:6px;border-radius:50%;flex-shrink:0;margin-top:6px;
}}
.g-dot.red{{background:#EF4444;box-shadow:0 0 6px rgba(239,68,68,0.4);}}
.g-dot.green{{background:#10B981;box-shadow:0 0 6px rgba(16,185,129,0.4);}}
.g-txt{{color:#5A6F8C;}}

/* ── QUERIES ── */
.queries-card{{
  background:#0A0F1E;border-radius:14px;
  padding:1.4rem 1.6rem;margin-bottom:1px;
  opacity:0;animation:fadeUp 0.55s ease 0.7s forwards;
}}
.queries-wrap{{display:flex;flex-direction:column;gap:0.4rem;margin-top:0.75rem;}}
.q-tag{{
  display:flex;align-items:center;gap:0.6rem;
  background:rgba(245,158,11,0.04);
  border:1px solid rgba(245,158,11,0.1);
  border-radius:6px;
  padding:0.5rem 0.9rem;
  font-family:'DM Mono',monospace;
  font-size:0.72rem;color:#6B7FA3;
  transition:all 0.15s;
  cursor:default;
}}
.q-tag:hover{{background:rgba(245,158,11,0.08);border-color:rgba(245,158,11,0.2);color:#8899B8;}}
.q-arrow{{color:#F59E0B;font-size:1rem;line-height:1;}}

/* ── CITY INSIGHT ── */
.city-card{{
  background:linear-gradient(135deg, rgba(245,158,11,0.05) 0%, rgba(10,15,30,0.95) 60%);
  border:1px solid rgba(245,158,11,0.1);
  border-radius:14px;
  padding:1.2rem 1.6rem;
  display:flex;align-items:flex-start;gap:0.75rem;
  opacity:0;animation:fadeUp 0.55s ease 0.8s forwards;
}}
.city-pin{{font-size:1.1rem;margin-top:1px;flex-shrink:0;}}
.city-label{{
  font-family:'DM Mono',monospace;font-size:0.55rem;
  letter-spacing:0.18em;color:#F59E0B;
  text-transform:uppercase;margin-bottom:0.3rem;opacity:0.7;
}}
.city-text{{font-size:0.82rem;color:#5A6F8C;line-height:1.6;}}

/* ── ANIMATIONS ── */
@keyframes fadeUp{{
  from{{opacity:0;transform:translateY(12px);}}
  to{{opacity:1;transform:translateY(0);}}
}}

::-webkit-scrollbar{{width:3px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:rgba(245,158,11,0.15);border-radius:2px;}}
</style>
</head>
<body>
<div class="dash">

  <!-- TOP BAR -->
  <div class="topbar">
    <div class="brand-display">{brand}<span> ·</span></div>
    <div class="meta">{timestamp}<br>{pl}</div>
  </div>

  <!-- HERO ROW: ring + grade + risk + readiness -->
  <div class="hero-row">
    <div class="hero-cell">
      <div class="ring-wrap">
        <svg viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg">
          <circle class="ring-track" cx="90" cy="90" r="{R}"/>
          <circle class="ring-glow" id="ring-glow" cx="90" cy="90" r="{R}"/>
          <circle class="ring-prog" id="ring-prog" cx="90" cy="90" r="{R}"/>
        </svg>
        <div class="ring-center">
          <div class="ring-num" id="score-counter">0</div>
          <div class="ring-denom">/100</div>
        </div>
      </div>
    </div>
    <div class="hero-cell">
      <div class="grade-val">{grade}</div>
      <div class="cell-label">GEO Grade</div>
    </div>
    <div class="hero-cell">
      <div class="badge-val" style="background:{rc}18;color:{rc};">{rl}</div>
      <div class="cell-label">Risk Level</div>
    </div>
    <div class="hero-cell">
      <div class="badge-val" style="background:{rdrc}18;color:{rdrc};">{rdrl}</div>
      <div class="cell-label">AI Readiness</div>
    </div>
  </div>

  <!-- SUMMARY -->
  <div class="summary-card">
    <div class="summary-label">Executive Summary</div>
    <div class="summary-text" id="summary-text"></div>
  </div>

  <!-- VS COMPETITOR -->
  <div class="vs-card">
    <div class="vs-header">
      <div class="section-label">vs Competitor</div>
      <div class="gap-badge">{gap_sign}{gap} pts &nbsp;{'↑ You lead' if gap >= 0 else '↓ They lead'}</div>
    </div>
    <div class="vs-row">
      <div class="vs-brand-label">
        <span class="vs-name">{brand}</span>
        <span class="vs-num">{brand_score}</span>
      </div>
      <div class="vs-track">
        <div class="vs-fill" id="brand-bar" data-w="{bs_pct}" style="background:{sc};"></div>
      </div>
    </div>
    <div class="vs-row" style="margin-top:0.75rem;">
      <div class="vs-brand-label">
        <span class="vs-name">{competitor_name}</span>
        <span class="vs-num">{comp_score}</span>
      </div>
      <div class="vs-track">
        <div class="vs-fill" id="comp-bar" data-w="{cs_pct}" style="background:#334155;"></div>
      </div>
    </div>
    <div class="verdict">{verdict}</div>
  </div>

  <!-- BREAKDOWN -->
  <div class="breakdown-card">
    <div class="section-label" style="margin-bottom:0.5rem;">Score Breakdown</div>
    {bd_html}
  </div>

  <!-- GAPS + WINS -->
  <div class="gw-grid">
    <div class="gw-card">
      <div class="section-label" style="margin-bottom:0.75rem;">Critical Gaps</div>
      {gaps_html}
    </div>
    <div class="gw-card">
      <div class="section-label" style="margin-bottom:0.75rem;">Quick Wins</div>
      {wins_html}
    </div>
  </div>

  <!-- QUERIES -->
  <div class="queries-card">
    <div class="section-label">Top Queries to Target</div>
    <div class="queries-wrap">{queries_html}</div>
  </div>

  <!-- CITY INSIGHT -->
  {'<div class="city-card"><div class="city-pin">📍</div><div><div class="city-label">Local Intelligence</div><div class="city-text">' + city_insight + '</div></div></div>' if city_insight else ''}

</div>

<script>
const SCORE = {score};
const CIRC  = {C:.4f};
const TARGET_OFFSET = CIRC * (1 - SCORE / 100);
const SUMMARY = "{summary_js}";

// Counter
function animateCounter(el, target, dur) {{
  const start = performance.now();
  function step(now) {{
    const p = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(ease * target);
    if (p < 1) requestAnimationFrame(step);
  }}
  requestAnimationFrame(step);
}}

// Ring
function animateRing() {{
  const prog = document.getElementById('ring-prog');
  const glow = document.getElementById('ring-glow');
  if (prog) {{ prog.style.strokeDashoffset = TARGET_OFFSET; }}
  if (glow) {{ glow.style.strokeDashoffset = TARGET_OFFSET; }}
}}

// Bars (comparison + breakdown)
function animateBars() {{
  document.querySelectorAll('[data-w]').forEach(el => {{
    const w = el.getAttribute('data-w');
    setTimeout(() => {{ el.style.width = w + '%'; }}, 100);
  }});
}}

// Typewriter summary
function typeWriter(el, text, speed) {{
  let i = 0;
  el.textContent = '';
  function type() {{
    if (i < text.length) {{
      el.textContent += text[i++];
      setTimeout(type, speed);
    }}
  }}
  type();
}}

window.addEventListener('load', () => {{
  const counter = document.getElementById('score-counter');
  const summEl  = document.getElementById('summary-text');

  setTimeout(() => {{
    if (counter) animateCounter(counter, SCORE, 1400);
    animateRing();
    animateBars();
    if (summEl && SUMMARY) typeWriter(summEl, SUMMARY, 14);
  }}, 250);
}});
</script>
</body>
</html>"""


def _grade(score: int) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"


# ── STREAMLIT APP ──────────────────────────────────────────────

st.set_page_config(
    page_title="GEO Score India · AI Visibility Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL CSS OVERRIDE ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Figtree:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* Kill Streamlit chrome */
#MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none !important; }
.stApp { background: #060911 !important; }
[data-testid="stAppViewContainer"] { background: #060911 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMain"] { padding: 0 !important; }
[data-testid="column"] { padding: 0 !important; }
.element-container { margin: 0 !important; }
iframe { border: none !important; display: block !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: #07091A !important;
  border-right: 1px solid rgba(245,158,11,0.1) !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding: 1.5rem 1.25rem 1rem !important;
}
[data-testid="stSidebar"] * { color: #C8D3E6 !important; }

/* Input labels */
.stTextInput > label, .stSelectbox > label {
  font-family: 'DM Mono', monospace !important;
  font-size: 0.58rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  color: #3D5070 !important;
  margin-bottom: 4px !important;
}
.stTextInput > label *, .stSelectbox > label * { color: #3D5070 !important; }

/* Inputs */
.stTextInput > div > div > input {
  background: #0B1020 !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 7px !important;
  color: #E1E8F5 !important;
  font-family: 'Figtree', sans-serif !important;
  font-size: 0.875rem !important;
  padding: 0.55rem 0.8rem !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input::placeholder { color: #1E2B40 !important; }
.stTextInput > div > div > input:focus {
  border-color: rgba(245,158,11,0.35) !important;
  box-shadow: 0 0 0 3px rgba(245,158,11,0.06) !important;
  outline: none !important;
}

/* Selectbox */
.stSelectbox > div > div {
  background: #0B1020 !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 7px !important;
  color: #E1E8F5 !important;
}

/* Button */
.stButton > button {
  background: linear-gradient(135deg, #F59E0B, #D97706) !important;
  color: #060911 !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'DM Mono', monospace !important;
  font-weight: 500 !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  padding: 0.75rem 1rem !important;
  width: 100% !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 4px 24px rgba(245,158,11,0.28) !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, #FBBF24, #F59E0B) !important;
  box-shadow: 0 6px 32px rgba(245,158,11,0.45) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Divider */
hr { border: none !important; border-top: 1px solid rgba(255,255,255,0.05) !important; margin: 1rem 0 !important; }

/* Expanders */
[data-testid="stExpander"] {
  background: transparent !important;
  border: 1px solid rgba(255,255,255,0.04) !important;
  border-radius: 6px !important;
  margin-bottom: 0.4rem !important;
}
.streamlit-expanderHeader {
  color: #3D5070 !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 0.6rem !important;
  letter-spacing: 0.12em !important;
  padding: 0.5rem 0.75rem !important;
}
.streamlit-expanderContent { background: transparent !important; border: none !important; padding: 0.5rem 0.75rem !important; }
.streamlit-expanderContent p { color: #4A5D7A !important; font-size: 0.78rem !important; line-height: 1.6 !important; }

/* Spinner */
.stSpinner > div { border-top-color: #F59E0B !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(245,158,11,0.15); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── SESSION INIT ─────────────────────────────────────────────
init_session()

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.25rem 0 1.5rem; border-bottom:1px solid rgba(245,158,11,0.08); margin-bottom:1.25rem;">
      <div style="font-family:'DM Mono',monospace;font-size:0.55rem;color:#F59E0B;letter-spacing:0.22em;text-transform:uppercase;margin-bottom:0.6rem;opacity:0.8;">
        AI Visibility Intelligence
      </div>
      <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#F1F5FD;letter-spacing:-0.03em;line-height:1.15;">
        GEO Score<br><span style="color:#F59E0B;">India</span>
      </div>
      <div style="font-family:'DM Mono',monospace;font-size:0.55rem;color:#2D3E58;letter-spacing:0.1em;margin-top:0.4rem;">
        v3.0 · Free Tier Active
      </div>
    </div>
    """, unsafe_allow_html=True)

    brand     = st.text_input("Brand Name",    placeholder="e.g. Mamaearth",   value="")
    city      = st.text_input("City / Region", placeholder="e.g. Chennai",     value="")
    competitor= st.text_input("Top Competitor",placeholder="e.g. Plum Goodness",value="")
    industry  = st.selectbox("Industry", options=[
        "D2C / Beauty & Personal Care", "FMCG / Consumer Goods", "EdTech",
        "FinTech / BFSI", "HealthTech / Wellness", "Food & Beverage",
        "Fashion & Apparel", "Real Estate", "Automobile", "SaaS / B2B Tech",
        "E-commerce / Marketplace", "Media & Entertainment", "Other",
    ])

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    run_clicked = st.button("◆  RUN FREE GEO ANALYSIS")
    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    with st.expander("▶ WHAT IS GEO?"):
        st.markdown("Generative Engine Optimization — how visible your brand is when consumers ask ChatGPT, Gemini, or Perplexity instead of Google.")
    with st.expander("▶ IS MY DATA STORED?"):
        st.markdown("Brand names are sent to AI providers for analysis only. No personal data collected.")
    with st.expander("▶ WHICH AI RUNS THIS?"):
        prov = st.session_state.get("provider_used")
        pmap = {"groq":"Groq · Llama 3.3 70B","gemini":"Gemini 2.5 Flash-Lite","openrouter":"OpenRouter · DeepSeek","none":"All unavailable"}
        st.markdown(f"Last used: **{pmap.get(prov, prov)}**" if prov else "Groq → Gemini → OpenRouter. Auto-fallback.")


# ── RUN LOGIC ────────────────────────────────────────────────
if run_clicked:
    result = run_analysis_safely(brand, city, competitor, industry)
    if result and result.get("error"):
        st.error(f"Analysis failed: {result.get('error_message')}")


# ── RENDER ───────────────────────────────────────────────────
current = st.session_state.get("geo_result")

if current and not current.get("error"):
    html = _build_results_html(current, brand or "Brand", competitor or "Competitor")
    components.html(html, height=1520, scrolling=False)
else:
    components.html(_build_hero_html(), height=600, scrolling=False)


# ══════════════════════════════════════════════════════════════
# HTML BUILDERS
# ══════════════════════════════════════════════════════════════
