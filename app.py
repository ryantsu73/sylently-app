import re
import json
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st


# -----------------------------
# OnlyFans scraping utilities
# -----------------------------

def _parse_human_number(text: str) -> Optional[int]:
    """
    Convert strings like '4.5K', '10.2M', '12,345' to an integer.
    Returns None if it cannot be parsed.
    """
    if not text:
        return None
    t = text.strip().lower().replace(",", "")
    match = re.match(r"^([0-9]*\.?[0-9]+)\s*([km])?$", t)
    if not match:
        # Maybe it's a plain integer like "1234"
        if t.isdigit():
            return int(t)
        return None

    num = float(match.group(1))
    suffix = match.group(2)

    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000

    return int(num)


def fetch_onlyfans_profile(handle: str) -> Dict[str, Any]:
    """
    Scrape a public OnlyFans profile and estimate:
      - followers (fans)
      - avg_views (heuristic from followers)
      - engagement_rate (heuristic from likes and followers)
      - avg_cpm (simple assumption)

    This uses public metadata only. If we cannot find any numbers,
    we gracefully fall back to generic defaults instead of raising.
    """
    username = handle.strip().lstrip("@").strip("/")
    if not username:
        raise ValueError("Handle is empty after cleaning. Please provide a valid OnlyFans username.")

    url = f"https://onlyfans.com/{username}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, headers=headers, timeout=20)

    if resp.status_code != 200:
        # Still a hard failure here because the page itself isn't reachable.
        raise RuntimeError(
            f"Failed to load OnlyFans profile page (status {resp.status_code}). "
            f"URL tried: {url}"
        )

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    followers = None
    likes = None

    # 1) Try meta description first (old pattern)
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    if meta_desc_tag and meta_desc_tag.get("content"):
        desc = meta_desc_tag["content"]

        # Example patterns: '10.5K likes', '2.3K fans'
        likes_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ll]ikes", desc)
        fans_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ff]ans", desc)

        if likes_match:
            likes_str = likes_match.group(1)
            likes = _parse_human_number(likes_str)

        if fans_match:
            fans_str = fans_match.group(1)
            followers = _parse_human_number(fans_str)

    # 2) If still missing, search in full page text more flexibly
    if followers is None or likes is None:
        text = soup.get_text(separator=" ", strip=True)

        if followers is None:
            # look for "1234 fans" / "1234 followers"
            fans_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+(fans|Followers?)", text)
            if fans_match:
                followers = _parse_human_number(fans_match.group(1))

        if likes is None:
            # look for "1234 likes"
            likes_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ll]ikes", text)
            if likes_match:
                likes = _parse_human_number(likes_match.group(1))

    # 3) If we truly found nothing, DO NOT raise – return a reasonable default
    if followers is None and likes is None:
        # Fallback generic profile – user can override in the sidebar
        followers = 5_000
        likes = None
        avg_views = int(followers * 0.3)
        engagement_rate = 3.5
        avg_cpm = 20.0

        return {
            "platform": "OnlyFans",
            "handle": username,
            "followers": followers,
            "avg_views": avg_views,
            "engagement_rate": engagement_rate,
            "avg_cpm": avg_cpm,
            "raw_source": "onlyfans_fallback_no_numbers_found",
        }

    # 4) Normal derivations when we have at least one signal

    if followers is None and likes is not None:
        # Rough guess: ~10% of followers like something at least once
        followers = max(int(likes / 0.1), likes)

    if followers is None:
        # Absolute last resort
        followers = 5_000

    avg_views = int(followers * 0.3)

    if likes is not None and followers > 0:
        engagement_rate = round((likes / followers) * 100, 2)
    else:
        engagement_rate = 3.5

    avg_cpm = 20.0

    return {
        "platform": "OnlyFans",
        "handle": username,
        "followers": followers,
        "avg_views": avg_views,
        "engagement_rate": engagement_rate,
        "avg_cpm": avg_cpm,
        "raw_source": "onlyfans_meta_or_text",
    }


def fetch_creator_profile_from_web(handle: str, platform: str) -> Dict[str, Any]:
    """
    Dispatcher for web lookups by platform.

    Returns a dict with at least:
      - followers
      - avg_views
      - engagement_rate
      - avg_cpm
    """
    platform_norm = platform.strip().lower()

    if not handle:
        raise ValueError("Handle cannot be empty.")

    if platform_norm == "onlyfans":
        return fetch_onlyfans_profile(handle)

    # You can extend this for other platforms:
    # elif platform_norm == "instagram": ...
    # elif platform_norm == "tiktok": ...
    # etc.
    raise NotImplementedError(f"Web lookup not implemented for platform: {platform}")


# -----------------------------
# Analytics / synthetic cohort
# -----------------------------

def generate_synthetic_cohort(
    followers: int,
    avg_views: float,
    engagement_rate: float,
    avg_cpm: float,
    n: int = 1000,
) -> pd.DataFrame:
    """
    Generate a synthetic cohort of similar creators to benchmark against.
    Very simple probabilistic model around the given stats.
    """

    followers = max(followers, 1)
    base_log = np.log(followers)

    # Followers: log-normal spread around the creator's follower count
    followers_dist = np.random.lognormal(mean=base_log, sigma=0.4, size=n).astype(int)

    # Views: normally 20–50% of followers, centered around creator's ratio
    creator_view_ratio = avg_views / followers if followers > 0 else 0.3
    creator_view_ratio = np.clip(creator_view_ratio, 0.05, 0.8)
    view_ratios = np.random.normal(loc=creator_view_ratio, scale=0.05, size=n)
    view_ratios = np.clip(view_ratios, 0.02, 0.9)
    views_dist = (followers_dist * view_ratios).astype(int)

    # Engagement rate: normal around creator's ER ± 1.5pp
    er_mean = np.clip(engagement_rate, 0.1, 50.0)
    er_dist = np.random.normal(loc=er_mean, scale=1.5, size=n)
    er_dist = np.clip(er_dist, 0.1, 80.0)

    # CPM: log-normal around creator's CPM
    cpm_base = max(avg_cpm, 0.5)
    log_cpm_mean = np.log(cpm_base)
    cpm_dist = np.random.lognormal(mean=log_cpm_mean, sigma=0.35, size=n)

    df = pd.DataFrame(
        {
            "followers": followers_dist,
            "avg_views": views_dist,
            "engagement_rate": er_dist,
            "avg_cpm": cpm_dist,
        }
    )

    return df


def percentile_rank(series: pd.Series, value: float) -> float:
    """Return the percentile rank of `value` within `series`."""
    if len(series) == 0:
        return 0.0
    return round(100.0 * (series < value).mean(), 2)


# -----------------------------
# Streamlit app
# -----------------------------

st.set_page_config(
    page_title="Creator Earnings Benchmark",
    page_icon="📊",
    layout="wide",
)

st.title("Creator Earnings Benchmark & OnlyFans Lookup")

# --- Session state ---
if "web_profile" not in st.session_state:
    st.session_state.web_profile = None
if "cohort_df" not in st.session_state:
    st.session_state.cohort_df = None

# --- Sidebar: lookup and inputs ---
st.sidebar.header("1. Lookup Creator Profile")

platform = st.sidebar.selectbox(
    "Platform",
    options=["OnlyFans", "Instagram", "TikTok", "YouTube"],
    index=0,
)

handle = st.sidebar.text_input(
    "Creator handle / username",
    placeholder="@creatorname or creatorname",
)


if st.sidebar.button("Lookup from web"):
    try:
        with st.spinner(f"Looking up {handle} on {platform}..."):
            profile = fetch_creator_profile_from_web(handle, platform)
        st.session_state.web_profile = profile
        st.sidebar.success("Profile data fetched from web.")
    except NotImplementedError as e:
        st.sidebar.error(str(e))
    except Exception as e:
        st.sidebar.error(f"Lookup failed: {e}")

st.sidebar.markdown("---")
st.sidebar.header("2. Override / Confirm Stats")

# Defaults from web profile if available
wp = st.session_state.web_profile or {}

followers_default = wp.get("followers", 10_000)
avg_views_default = wp.get("avg_views", 3_000)
engagement_default = wp.get("engagement_rate", 3.5)
cpm_default = wp.get("avg_cpm", 20.0)

followers_input = st.sidebar.number_input(
    "Followers / fans",
    min_value=1,
    value=int(followers_default),
    step=100,
    help="If web lookup failed, set this manually.",
)

avg_views_input = st.sidebar.number_input(
    "Average views per post",
    min_value=1,
    value=int(avg_views_default),
    step=100,
)

engagement_input = st.sidebar.number_input(
    "Engagement rate (%)",
    min_value=0.1,
    max_value=100.0,
    value=float(engagement_default),
    step=0.1,
)

cpm_input = st.sidebar.number_input(
    "Average CPM (USD)",
    min_value=0.5,
    max_value=1000.0,
    value=float(cpm_default),
    step=0.5,
)

generate_btn = st.sidebar.button("Generate synthetic cohort & benchmarks")

# -----------------------------
# Main layout
# -----------------------------

col_main, col_side = st.columns([3, 2])

with col_main:
    st.subheader("Creator profile")

    if st.session_state.web_profile:
        st.markdown("**Loaded from web lookup:**")
        st.json(st.session_state.web_profile)
    else:
        st.info("No web profile loaded yet. Use the sidebar to look up a creator or enter stats manually.")

    st.markdown("---")
    st.subheader("Benchmark vs similar creators")

    if generate_btn:
        with st.spinner("Generating synthetic cohort and benchmarks..."):
            df = generate_synthetic_cohort(
                followers=int(followers_input),
                avg_views=float(avg_views_input),
                engagement_rate=float(engagement_input),
                avg_cpm=float(cpm_input),
                n=1000,
            )
            st.session_state.cohort_df = df

    df = st.session_state.cohort_df

    if df is not None and len(df) > 0:
        # Compute percentile ranks
        p_followers = percentile_rank(df["followers"], followers_input)
        p_views = percentile_rank(df["avg_views"], avg_views_input)
        p_eng = percentile_rank(df["engagement_rate"], engagement_input)
        p_cpm = percentile_rank(df["avg_cpm"], cpm_input)

        st.markdown("### Percentile positioning")
        st.write(
            f"- Followers: **{p_followers}th** percentile\n"
            f"- Average views: **{p_views}th** percentile\n"
            f"- Engagement rate: **{p_eng}th** percentile\n"
            f"- CPM: **{p_cpm}th** percentile"
        )

        st.markdown("### Sample of synthetic cohort")
        st.dataframe(df.head(20))
    else:
        st.info("Generate the synthetic cohort from the sidebar to see benchmarks here.")

with col_side:
    st.subheader("Earnings back-of-the-envelope")

    st.markdown(
        "This is a simple earnings estimate given your CPM and an assumed "
        "number of monthly impressions."
    )

    monthly_posts = st.number_input(
        "Estimated posts per month",
        min_value=1,
        max_value=1000,
        value=30,
    )

    impressions_per_post = avg_views_input  # from sidebar
    total_monthly_impressions = monthly_posts * impressions_per_post
    estimated_monthly_earnings = (total_monthly_impressions / 1000.0) * cpm_input

    st.metric(
        label="Estimated monthly impressions",
        value=f"{total_monthly_impressions:,.0f}",
    )
    st.metric(
        label="Estimated monthly earnings (USD)",
        value=f"${estimated_monthly_earnings:,.2f}",
    )

    st.caption(
        "These are rough estimates only. For serious forecasting, plug in your real "
        "impression data and a more sophisticated revenue model."
    )

st.markdown("---")
st.caption(
    "Note: OnlyFans scraping is based on public meta information and may break "
    "if the site changes its structure. Always respect the platform's terms of service."
)
