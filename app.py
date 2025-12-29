# app.py

from typing import Dict, Optional

import streamlit as st
import pandas as pd

from synthetic import (
    generate_synthetic_cohort,
    build_profile_percentiles,
    build_pricing_percentiles,
    percentile_band_label,
    short_percentile,
)


# ---------- Page config & global styles ----------

st.set_page_config(
    page_title="Creator Revenue Lab",
    page_icon="💸",
    layout="wide",
)

CUSTOM_CSS = """
<style>
/* Base */
body {
    background: radial-gradient(circle at top left, #0f172a, #020617 55%);
    color: #e5e7eb;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
}
section.main > div {
    padding-top: 1.25rem;
}

/* Headline gradient text */
.gradient-text {
    background: linear-gradient(120deg, #22c55e, #a855f7, #ec4899);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

/* Glass panels */
.glass-panel {
    background: radial-gradient(circle at top left, rgba(15,23,42,0.95), rgba(15,23,42,0.85));
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.25);
    box-shadow: 0 18px 45px rgba(15,23,42,0.75);
    padding: 1.4rem 1.6rem;
}

/* Feature cards */
.feature-card {
    background: radial-gradient(circle at top left, rgba(30,64,175,0.35), rgba(15,23,42,0.98));
    border-radius: 16px;
    border: 1px solid rgba(96,165,250,0.45);
    padding: 1rem 1.2rem;
}

/* Pills & badges */
.pill {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.7rem;
    border-radius: 999px;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid rgba(148,163,184,0.6);
    background: radial-gradient(circle at top left, rgba(30,64,175,0.6), rgba(15,23,42,0.95));
    color: #e5e7eb;
}
.badge-soft {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    font-size: 0.7rem;
    background: rgba(15,118,110,0.22);
    border: 1px solid rgba(45,212,191,0.55);
    color: #a5f3fc;
}

/* Metric cards */
.metric-card {
    background: radial-gradient(circle at top left, rgba(15,23,42,0.98), rgba(15,23,42,0.9));
    border-radius: 14px;
    border: 1px solid rgba(148,163,184,0.4);
    padding: 0.85rem 1rem;
}
.metric-label {
    font-size: 0.75rem;
    color: #9ca3af;
}
.metric-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: #e5e7eb;
}
.metric-sub {
    font-size: 0.7rem;
    color: #6b7280;
}

/* Tabs */
.stTabs [role="tablist"] {
    gap: 0.5rem;
}
.stTabs [role="tab"] {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    border-radius: 999px !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------- Web lookup hook (this is where you plug your old scraper) ----------

def fetch_creator_profile_from_web(handle: str, platform: str) -> Optional[Dict]:
    """
    LOOKUP HOOK: Replace the body of this function with your original scraping / API logic.

    Expected return shape (keys are all optional, but these are what the app uses):
      {
          "handle": str,
          "platform": str,
          "followers": int,
          "avg_views": int,
          "engagement_rate": float,   # 0–1, not percent
          "avg_cpm": float            # optional
      }

    Return None if lookup fails (e.g. profile not found, error, etc).
    """
    # ------- TODO: REPLACE THIS STUB WITH YOUR REAL IMPLEMENTATION -------
    # Example stub just to prove wiring works; REMOVE this and drop your old code in:
    # if platform == "OnlyFans":
    #     return {
    #         "handle": handle.lstrip("@"),
    #         "platform": platform,
    #         "followers": 120_000,
    #         "avg_views": 40_000,
    #         "engagement_rate": 0.08,
    #         "avg_cpm": 30.0,
    #     }
    # return None
    return None
    # ---------------------------------------------------------------------


# ---------- Helpers ----------

def get_profile_id(profile: Dict) -> str:
    if not profile:
        return "none"
    for key in ("handle", "username", "creator_id", "id"):
        if key in profile and profile[key]:
            return str(profile[key]).lower()
    return str(hash(repr(sorted(profile.items()))))


@st.cache_data(show_spinner=False)
def get_synthetic_for_profile(profile: Dict) -> pd.DataFrame:
    return generate_synthetic_cohort(profile)


def format_number(v: Optional[float]) -> str:
    if v is None:
        return "—"
    try:
        v = float(v)
    except Exception:
        return "—"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:.0f}"


def format_pct(v: Optional[float], decimals: int = 1) -> str:
    if v is None:
        return "—"
    return f"{v*100:.{decimals}f}%"


def simple_pricing_fallback(profile: Dict) -> Dict:
    """
    Fallback pricing logic that does NOT depend on any external engines.
    """
    views = float(profile.get("avg_views") or profile.get("avg_video_views") or 0)
    followers = float(profile.get("followers") or profile.get("follower_count") or 0)
    engagement_rate = float(profile.get("engagement_rate") or 0.05)

    if followers < 50_000:
        base_cpm = 18
    elif followers < 250_000:
        base_cpm = 25
    elif followers < 1_000_000:
        base_cpm = 35
    else:
        base_cpm = 45

    base_cpm *= (1 + (engagement_rate - 0.04) * 4.0)

    if views <= 0:
        views = followers * 0.20

    low_cpm = base_cpm * 0.8
    high_cpm = base_cpm * 1.35

    recommended_price = (views / 1000.0) * base_cpm
    low_price = (views / 1000.0) * low_cpm
    high_price = (views / 1000.0) * high_cpm

    return {
        "recommended_price": float(recommended_price),
        "low_price": float(low_price),
        "high_price": float(high_price),
        "base_cpm": float(base_cpm),
        "low_cpm": float(low_cpm),
        "high_cpm": float(high_cpm),
        "currency": "USD",
        "explanation": "Heuristic CPM based on audience size & engagement (fallback only).",
    }


# ---------- Step 1: Creator lookup with web fetch + manual override ----------

def render_creator_lookup() -> Optional[Dict]:
    # Session defaults for pre-filling after a web lookup
    if "prefill_profile" not in st.session_state:
        st.session_state["prefill_profile"] = {}

    prefill = st.session_state["prefill_profile"]

    st.markdown(
        """
        <div class="glass-panel">
          <div class="pill">Step 1 · Load a Creator</div>
          <h2 style="margin-top:0.75rem;margin-bottom:0.35rem;">Creator profile input</h2>
          <p style="font-size:0.86rem;color:#9ca3af;">
            Enter a handle and platform to fetch stats, or just plug in your own estimates. Once loaded, the lab
            spins up a synthetic peer set and unlocks pricing, whales, and DM angles.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_handle, col_platform = st.columns([2, 1])
    with col_handle:
        handle = st.text_input(
            "Creator handle or @username",
            placeholder="@creator",
            value=prefill.get("handle", ""),
        )
    with col_platform:
        platform = st.selectbox(
            "Platform",
            ["Instagram", "TikTok", "YouTube", "OnlyFans", "Other"],
            index=["Instagram", "TikTok", "YouTube", "OnlyFans", "Other"].index(
                prefill.get("platform", "Instagram")
            ),
        )

    col_lookup, col_hint = st.columns([1, 3])
    with col_lookup:
        lookup_clicked = st.button("Lookup from web", use_container_width=True)
    with col_hint:
        st.write(
            "<span style='font-size:0.8rem;color:#6b7280;'>"
            "Web lookup will try to scrape/populate stats (like it used to). You can then tweak them manually."
            "</span>",
            unsafe_allow_html=True,
        )

    # Web lookup: call your scraper, store result into session, rerun to prefill fields
    if lookup_clicked:
        if not handle.strip():
            st.warning("Enter a handle before running web lookup.")
        else:
            with st.spinner("Looking up profile from the web…"):
                fetched = fetch_creator_profile_from_web(handle.strip(), platform)
            if not fetched:
                st.error("Could not fetch profile from the web. Check handle/platform or try manual stats.")
            else:
                # Normalize and store into prefill for the next rerun
                st.session_state["prefill_profile"] = {
                    "handle": fetched.get("handle") or handle.strip(),
                    "platform": fetched.get("platform") or platform,
                    "followers": int(fetched.get("followers") or 0),
                    "avg_views": int(fetched.get("avg_views") or 0),
                    "engagement_rate": float(fetched.get("engagement_rate") or 0.0),
                    "avg_cpm": float(fetched.get("avg_cpm") or 0.0),
                }
                st.success("Profile fetched. Fields below have been updated.")
                st.experimental_rerun()

    st.markdown("##### Key stats (edit or override any value)")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        followers = st.number_input(
            "Followers",
            min_value=0,
            step=1000,
            value=int(prefill.get("followers", 0)),
        )
    with c2:
        avg_views = st.number_input(
            "Avg views / story",
            min_value=0,
            step=1000,
            value=int(prefill.get("avg_views", 0)),
        )
    with c3:
        er_default_percent = (
            prefill.get("engagement_rate", 0.0) * 100.0
            if prefill.get("engagement_rate") is not None
            else 0.0
        )
        engagement_rate = st.number_input(
            "Engagement rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            value=float(er_default_percent),
        )
    with c4:
        avg_cpm = st.number_input(
            "Known CPM (optional)",
            min_value=0.0,
            step=1.0,
            value=float(prefill.get("avg_cpm", 0.0)),
        )

    col_btn, col_hint2 = st.columns([1, 3])
    with col_btn:
        load_clicked = st.button("Load creator →", type="primary", use_container_width=True)
    with col_hint2:
        st.write(
            "<span style='font-size:0.8rem;color:#6b7280;'>"
            "If lookup failed or was off, just edit these numbers and load the creator."
            "</span>",
            unsafe_allow_html=True,
        )

    if not load_clicked:
        return None

    if followers <= 0 and avg_views <= 0:
        st.warning("Please provide at least followers or average views.")
        return None

    profile = {
        "handle": handle.strip() or prefill.get("handle") or None,
        "platform": platform,
        "followers": int(followers) if followers else None,
        "avg_views": int(avg_views) if avg_views else None,
        "engagement_rate": (engagement_rate / 100.0) if engagement_rate else None,
        "avg_cpm": float(avg_cpm) if avg_cpm else None,
    }

    st.session_state["creator_profile"] = profile
    st.session_state["profile_id"] = get_profile_id(profile)

    st.success("Creator loaded. Scroll down to see pricing & labs.")

    return profile


def render_profile_header(profile: Dict, profile_percentiles: Dict):
    followers = profile.get("followers")
    views = profile.get("avg_views")
    er = profile.get("engagement_rate")

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.markdown(
            f"""
            <div class="glass-panel" style="padding:0.9rem 1rem;">
              <div class="pill">Profile loaded</div>
              <h3 style="margin-top:0.55rem;margin-bottom:0.15rem;">
                {profile.get("handle") or "Unnamed creator"}
              </h3>
              <p style="font-size:0.8rem;color:#9ca3af;margin:0;">
                {profile.get("platform","Platform not set")} • Synthetic peer set generated
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Followers</div>
              <div class="metric-value">{format_number(followers)}</div>
              <div class="metric-sub">
                vs peers: {short_percentile(profile_percentiles.get("followers_pct"))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Avg views</div>
              <div class="metric-value">{format_number(views)}</div>
              <div class="metric-sub">
                vs peers: {short_percentile(profile_percentiles.get("views_pct"))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Engagement</div>
              <div class="metric-value">
                {format_pct(er) if er is not None else "—"}
              </div>
              <div class="metric-sub">
                vs peers: {short_percentile(profile_percentiles.get("engagement_pct"))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------- Smart Price Lab ----------

def render_smart_price_tab(profile: Optional[Dict], cohort_df: Optional[pd.DataFrame]):
    st.markdown(
        """
        <div class="pill" style="margin-bottom:0.4rem;">Lab 1 · Smart Price</div>
        <h3 style="margin-top:0;margin-bottom:0.25rem;">Anchor this deal the sane way</h3>
        <p style="font-size:0.85rem;color:#9ca3af;margin-bottom:0.4rem;">
          We take your inputs + a synthetic peer set to triangulate a price band, then benchmark your ask vs similar creators.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not profile or cohort_df is None or cohort_df.empty:
        st.info("Load a creator above to generate a synthetic peer set and pricing band.")
        return

    c1, c2, c3 = st.columns([1.6, 1, 1])
    with c1:
        offer_type = st.selectbox(
            "Deliverable",
            [
                "1 × Story (single frame)",
                "3-frame Story sequence",
                "1 × Reel / TikTok",
                "Reel + Story amplification",
                "Custom package",
            ],
        )
    with c2:
        usage = st.selectbox(
            "Usage",
            ["Organic only", "Spark/whitelist 30d", "Spark/whitelist 90d", "Full paid + cutdowns"],
        )
    with c3:
        urgency = st.selectbox("Urgency", ["Flexible", "Standard", "Rush"])

    st.divider()

    pricing_result = simple_pricing_fallback(profile)

    rec_price = pricing_result.get("recommended_price")
    low_price = pricing_result.get("low_price")
    high_price = pricing_result.get("high_price")
    currency = pricing_result.get("currency", "USD")

    rec_display = f"{currency} {rec_price:,.0f}" if rec_price is not None else "—"
    if low_price is not None and high_price is not None:
        band_display = f"{currency} {low_price:,.0f} – {currency} {high_price:,.0f}"
    else:
        band_display = "—"

    price_pcts = build_pricing_percentiles(profile, cohort_df, rec_price)

    ctop1, ctop2 = st.columns([1.4, 1])
    with ctop1:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Recommended ask</div>
              <div class="metric-value">
                {rec_display}
              </div>
              <div class="metric-sub">
                Band: {band_display}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ctop2:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">Synthetic sanity check</div>
              <div class="metric-sub" style="margin-top:0.2rem;margin-bottom:0.25rem;">
                Price vs {len(cohort_df):,} lookalike creators
              </div>
              <div style="font-size:0.8rem;color:#e5e7eb;margin-bottom:0.2rem;">
                {percentile_band_label(price_pcts.get("price_pct"))}
              </div>
              <div style="font-size:0.75rem;color:#9ca3af;">
                Effective CPM vs peers: {percentile_band_label(price_pcts.get("cpm_pct"))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("See synthetic peer distribution & explanation", expanded=False):
        st.markdown(
            """
            **How this works**

            - We generate a cohort of synthetic creators clustered around this profile's followers, views, and engagement.  
            - For each synthetic creator we simulate a CPM and resulting package price.  
            - Your recommended ask is positioned inside that distribution to show whether it's underpriced,
              in-line, or aggressive.
            """,
            unsafe_allow_html=False,
        )

        show_table = st.checkbox("Show raw synthetic sample (head)", value=False)
        if show_table:
            st.dataframe(cohort_df.head(25), use_container_width=True)

        st.caption(
            "Synthetic cohort is regenerated if you materially change followers, views, or engagement."
        )

    if explanation := pricing_result.get("explanation"):
        st.markdown(
            f"<p style='font-size:0.8rem;color:#9ca3af;margin-top:0.6rem;'>{explanation}</p>",
            unsafe_allow_html=True,
        )


# ---------- Whale Radar & DM Studio ----------

def render_whale_radar_tab(profile: Optional[Dict], cohort_df: Optional[pd.DataFrame]):
    st.markdown(
        """
        <div class="pill" style="margin-bottom:0.4rem;">Lab 2 · Whale Radar</div>
        <h3 style="margin-top:0;margin-bottom:0.25rem;">Find brands that actually match this profile</h3>
        <p style="font-size:0.85rem;color:#9ca3af;margin-bottom:0.4rem;">
          Uses profile context + synthetic peers to bias toward brands that overpay for similar audiences.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not profile or cohort_df is None or cohort_df.empty:
        st.info("Load a creator above to generate whale brand ideas for this audience shape.")
        return

    st.write("• Example whale brand 1  \n• Example whale brand 2  \n• Example whale brand 3")
    st.caption("Hook your real whale targeting logic into this tab; `profile` and `cohort_df` are available.")


def render_dm_studio_tab(profile: Optional[Dict], cohort_df: Optional[pd.DataFrame]):
    st.markdown(
        """
        <div class="pill" style="margin-bottom:0.4rem;">Lab 3 · DM Studio</div>
        <h3 style="margin-top:0;margin-bottom:0.25rem;">Pitch lines tuned to their leverage</h3>
        <p style="font-size:0.85rem;color:#9ca3af;margin-bottom:0.4rem;">
          DM hooks and email subject lines that match their percentile position in the market.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not profile or cohort_df is None or cohort_df.empty:
        st.info("Load a creator above to get leverage-aware DM lines.")
        return

    st.write(
        "“Hey [Brand], creators at this size usually see CPMs in the [X] band – "
        "we've consistently driven above-benchmark performance on similar deals.”"
    )
    st.caption("Replace this with your DM engine; `profile` and synthetic context are available.")


# ---------- Layout: hero + tools ----------

def main():
    # Hero
    st.markdown(
        """
        <div style="margin-bottom:1.4rem;">
          <div class="pill">Creator Revenue Lab</div>
          <h1 class="gradient-text" style="font-size:2.4rem;margin-top:0.5rem;margin-bottom:0.4rem;">
            Price, pitch & prospect like you’ve done this 1,000 times.
          </h1>
          <p style="font-size:0.95rem;color:#9ca3af;max-width:640px;">
            Start with a single creator profile, then let the lab spin up a synthetic peer set, pressure-test your pricing,
            and generate whale brand ideas & DM copy that match their leverage in the market.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature strip
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.markdown(
            """
            <div class="feature-card">
              <div class="badge-soft">Smart CPM bands</div>
              <p style="font-size:0.8rem;color:#d1d5db;margin-top:0.4rem;margin-bottom:0;">
                Synthetic pricing sanity check so you know if an ask is laughable, fair, or leaving money on the table.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with fc2:
        st.markdown(
            """
            <div class="feature-card">
              <div class="badge-soft">Whale targeting</div>
              <p style="font-size:0.8rem;color:#d1d5db;margin-top:0.4rem;margin-bottom:0;">
                Radar for brands that historically overpay for this exact audience shape.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with fc3:
        st.markdown(
            """
            <div class="feature-card">
              <div class="badge-soft">Leverage-aware copy</div>
              <p style="font-size:0.8rem;color:#d1d5db;margin-top:0.4rem;margin-bottom:0;">
                DM lines tuned to whether this creator is mid-pack or a quiet top 10% killer.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Step 1: lookup
    saved_profile = st.session_state.get("creator_profile")
    new_profile = render_creator_lookup()
    profile = new_profile or saved_profile

    cohort_df: Optional[pd.DataFrame] = None
    profile_pcts: Dict = {}
    if profile:
        cohort_df = get_synthetic_for_profile(profile)
        profile_pcts = build_profile_percentiles(profile, cohort_df)
        render_profile_header(profile, profile_pcts)
        st.markdown("")

    # Tabs are always visible
    tabs = st.tabs(["💸 Smart Price Lab", "🐋 Whale Radar", "✉️ DM Studio"])

    with tabs[0]:
        render_smart_price_tab(profile, cohort_df)
    with tabs[1]:
        render_whale_radar_tab(profile, cohort_df)
    with tabs[2]:
        render_dm_studio_tab(profile, cohort_df)


if __name__ == "__main__":
    main()
