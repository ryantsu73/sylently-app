# app.py

import streamlit as st

# ---------------------------------------------------
# IMPORT YOUR ENGINE MODULE UIs
# ---------------------------------------------------
from engine.pricing_engine import render_ui as render_smart_price_test_ui
from engine.whales import render_ui as render_whale_radar_ui
from engine.dm_suggestions import render_ui as render_dm_studio_ui
from engine.of_lookup import render_ui as render_of_lookup_ui  # NEW


# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Sylently – AI Pricing Lab for Creators",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------
# GLOBAL CSS INJECTION
# ---------------------------------------------------
def inject_global_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background-color: #050712;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.main {
    background: radial-gradient(circle at top left, #1d2033 0, #050712 45%, #02010a 100%);
    color: #F9FAFB;
}

/* Hero section */
.hero-container {
    padding: 3.5rem 3rem 2rem 3rem;
    border-radius: 32px;
    position: relative;
    overflow: hidden;
    background: radial-gradient(circle at top left, rgba(139, 92, 246, 0.26), transparent 55%),
                radial-gradient(circle at bottom right, rgba(236, 72, 153, 0.18), transparent 55%),
                linear-gradient(135deg, #050818 0%, #050712 60%, #04030f 100%);
    border: 1px solid rgba(148, 163, 184, 0.22);
    box-shadow:
        0 40px 120px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(15, 23, 42, 0.8);
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    border-radius: 999px;
    padding: 6px 14px;
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.5);
    color: #E5E7EB;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero-title {
    font-size: 3.0rem;
    line-height: 1.05;
    letter-spacing: -0.06em;
    font-weight: 700;
}

.hero-gradient {
    background: linear-gradient(120deg, #e5e7eb 0%, #c4b5fd 40%, #f97316 80%, #f9a8d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 1.25rem;
    font-size: 1.05rem;
    color: #9CA3AF;
    max-width: 32rem;
}

.hero-metrics {
    display: flex;
    gap: 2.5rem;
    margin-top: 2.0rem;
    font-size: 0.9rem;
}

.hero-metric-label {
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.75rem;
}
.hero-metric-value {
    font-size: 1.4rem;
    font-weight: 600;
    color: #E5E7EB;
}

.hero-cta-row {
    display: flex;
    gap: 1.0rem;
    align-items: center;
    margin-top: 2rem;
    flex-wrap: wrap;
}

.primary-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1.8rem;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    color: #0B1120;
    font-weight: 600;
    font-size: 0.95rem;
    background: linear-gradient(135deg, #f97316, #ec4899);
    box-shadow:
        0 15px 40px rgba(236, 72, 153, 0.55),
        0 0 0 1px rgba(148, 163, 184, 0.55);
    transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
}

.primary-btn:hover {
    transform: translateY(-1px) scale(1.01);
    filter: brightness(1.03);
    box-shadow:
        0 20px 60px rgba(236, 72, 153, 0.75),
        0 0 0 1px rgba(249, 115, 22, 0.75);
}

.ghost-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
    padding: 0.7rem 1.4rem;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.5);
    background: rgba(15, 23, 42, 0.7);
    color: #E5E7EB;
    font-weight: 500;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
}

.ghost-btn:hover {
    background: rgba(15, 23, 42, 0.9);
    border-color: rgba(248, 250, 252, 0.85);
    transform: translateY(-1px);
}

.tool-card {
    padding: 1.6rem 1.4rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(15,23,42,0.72));
    border: 1px solid rgba(148, 163, 184, 0.3);
    box-shadow:
        0 18px 55px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(15, 23, 42, 0.9);
    color: #E5E7EB;
}

.tool-card h3 {
    font-size: 1.1rem;
    margin-bottom: 0.45rem;
}

.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border-radius: 999px;
    padding: 0.18rem 0.7rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #A5B4FC;
    background: rgba(49, 46, 129, 0.7);
}

.section-title {
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.section-subtitle {
    color: #9CA3AF;
    font-size: 0.95rem;
    margin-bottom: 1.8rem;
}

/* Streamlit tweaks */
button[kind="primary"] {
    border-radius: 999px !important;
}

.stTextInput > div > div > input,
.stNumberInput input,
.stSelectbox > div > div > select {
    background-color: rgba(15, 23, 42, 0.9);
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.6);
    color: #E5E7EB;
}

.stSlider > div > div > div > div {
    color: #E5E7EB;
}
</style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------
# HERO SECTION
# ---------------------------------------------------
def render_hero():
    st.markdown(
        """
<div class="hero-container">
<div style="display:flex; gap:3rem; align-items:flex-start; justify-content:space-between; flex-wrap:wrap;">
<div style="max-width:520px;">
<div class="hero-pill">
<span style="width:7px; height:7px; border-radius:999px; background:radial-gradient(circle,#22C55E 0,#16A34A 35%,transparent 100%); box-shadow:0 0 10px rgba(34,197,94,0.9);"></span>
Real‑time AI pricing lab for subscription creators
</div>
<h1 class="hero-title">
Turn fans into<br><span class="hero-gradient">predictable recurring revenue.</span>
</h1>
<p class="hero-subtitle">
Sylently runs price experiments, spots whales before they churn, and
writes the DMs that keep them in love with you — all in one control center.
</p>

<div class="hero-metrics">
<div>
<div class="hero-metric-label">Avg. MRR lift</div>
<div class="hero-metric-value">+18.7%</div>
</div>
<div>
<div class="hero-metric-label">Payback on tests</div>
<div class="hero-metric-value">&lt; 7 days</div>
</div>
<div>
<div class="hero-metric-label">Fans analyzed</div>
<div class="hero-metric-value">127,392+</div>
</div>
</div>

<div class="hero-cta-row">
<button class="primary-btn" onclick="window.scrollTo({ top: document.body.scrollHeight * 0.35, behavior: 'smooth' });">
Start a price test
</button>
<button class="ghost-btn" onclick="window.scrollTo({ top: document.body.scrollHeight * 0.6, behavior: 'smooth' });">
Explore whale radar
</button>
</div>
</div>

<div style="flex:1; min-width:260px; max-width:480px; position:relative;">
<div style="position:relative; padding:1.7rem 1.6rem; border-radius:24px; background:radial-gradient(circle at top,#1E293B,transparent 65%), linear-gradient(135deg,#020617,#020617 55%,#020617); border:1px solid rgba(148,163,184,0.42); box-shadow:0 18px 60px rgba(15,23,42,0.9); overflow:hidden;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.4rem;">
<div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.18em; color:#9CA3AF;">
Sylently · Live lab
</div>
<div style="display:flex; gap:4px;">
<span style="width:8px; height:8px; border-radius:999px; background:#22C55E;"></span>
<span style="width:8px; height:8px; border-radius:999px; background:#F97316;"></span>
<span style="width:8px; height:8px; border-radius:999px; background:#EF4444;"></span>
</div>
</div>

<div style="display:grid; grid-template-columns:2fr 1.5fr; gap:1rem; align-items:flex-start;">
<div>
<div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.16em; color:#9CA3AF; margin-bottom:0.4rem;">
Smart price test
</div>
<div style="font-size:2.1rem; font-weight:600; color:#E5E7EB;">$47 &rarr; $61</div>
<div style="font-size:0.85rem; color:#9CA3AF; margin-top:0.4rem;">
Bayesian optimizer projects <span style="color:#facc15;">+21.3% MRR</span> at new anchor price.
</div>
</div>
<div>
<div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.16em; color:#9CA3AF; margin-bottom:0.4rem;">
Whale radar
</div>
<div style="font-size:1.1rem; color:#E5E7EB; margin-bottom:0.35rem;">
7 whales<br><span style="color:#f97316;">2 at churn‑risk</span>
</div>
<div style="font-size:0.8rem; color:#9CA3AF;">
AI flags your top fans and suggests save‑my‑whale DMs.
</div>
</div>
</div>

</div>
</div>

</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------
# FEATURE CARDS OVERVIEW
# ---------------------------------------------------
def render_tools_overview():
    st.markdown(
        """
<div>
<h2 class="section-title">Your AI revenue lab</h2>
<p class="section-subtitle">
Three focused tools that work together: run price tests, spot whales, and drop irresistible DMs — 
without spreadsheets or guesswork.
</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
<div class="tool-card">
<div class="tool-badge">Core · Experiment</div>
<h3>Smart Price Test</h3>
<p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0.9rem;">
Set your current price, variants, and goal. Sylently runs the math and recommends
the price that grows MRR while keeping fans happy.
</p>
</div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
<div class="tool-card">
<div class="tool-badge" style="background:rgba(22,78,99,0.8); color:#67E8F9;">
Signal · Whales
</div>
<h3>Whale Radar</h3>
<p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0.9rem;">
Upload your fan list and tipping history. We highlight whales, upsell potential,
and early churn‑risk before they ghost.
</p>
</div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
<div class="tool-card">
<div class="tool-badge" style="background:rgba(76,29,149,0.85); color:#F5D0FE;">
Studio · DMs
</div>
<h3>DM Studio</h3>
<p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0.9rem;">
Paste a chat thread or fan notes, pick your vibe, and Sylently drafts playful,
on‑brand DMs that nudge upgrades instead of begging.
</p>
</div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------
# TABS THAT RUN YOUR TOOLS
# ---------------------------------------------------
def render_lab_tabs():
    st.markdown("### Open your lab")
    st.markdown(
        "<p style='color:#9CA3AF; font-size:0.9rem; margin-bottom:1.2rem;'>Choose a tool below to get to work.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🧪 Smart Price Test", "🐋 Whale Radar", "💬 DM Studio", "🔗 OnlyFans Profile"]
    )

    with tab1:
        render_smart_price_test_ui()

    with tab2:
        render_whale_radar_ui()

    with tab3:
        render_dm_studio_ui()

    with tab4:
        render_of_lookup_ui()


# ---------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------
def main():
    inject_global_css()
    render_hero()
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    render_tools_overview()
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    render_lab_tabs()


if __name__ == "__main__":
    main()
