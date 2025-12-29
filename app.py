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

    Additionally tries to pull:
      - profile_name
      - profile_image_url
      - likes
      - posts_count
      - photos_count
      - videos_count

    Also returns simple ESTIMATES:
      - estimated_subscribers
      - estimated_monthly_visits

    Uses public metadata only and NEVER raises on parsing issues.
    On any failure, falls back to default values and records an 'error'
    string plus a 'raw_source' flag so the UI can still work.
    """
    username = handle.strip().lstrip("@").strip("/")
    if not username:
        return {
            "platform": "OnlyFans",
            "handle": handle,
            "profile_name": handle or "Unknown",
            "profile_image_url": None,
            "followers": 5_000,
            "likes": None,
            "posts_count": None,
            "photos_count": None,
            "videos_count": None,
            "avg_views": int(5_000 * 0.3),
            "engagement_rate": 3.5,
            "avg_cpm": 20.0,
            "estimated_subscribers": 5_000,
            "estimated_monthly_visits": 5_000 * 15,
            "raw_source": "onlyfans_invalid_handle_fallback",
            "error": "Handle was empty after cleaning.",
        }

    url = f"https://onlyfans.com/{username}"

    # Default values used whenever we can't parse real data
    def make_fallback(raw_source: str, error: Optional[str] = None) -> Dict[str, Any]:
        followers = 5_000
        avg_views = int(followers * 0.3)
        engagement_rate = 3.5
        avg_cpm = 20.0
        estimated_subscribers = followers
        estimated_monthly_visits = followers * 15

        data = {
            "platform": "OnlyFans",
            "handle": username,
            "profile_name": username,
            "profile_image_url": None,
            "followers": followers,
            "likes": None,
            "posts_count": None,
            "photos_count": None,
            "videos_count": None,
            "avg_views": avg_views,
            "engagement_rate": engagement_rate,
            "avg_cpm": avg_cpm,
            "estimated_subscribers": estimated_subscribers,
            "estimated_monthly_visits": estimated_monthly_visits,
            "raw_source": raw_source,
        }
        if error:
            data["error"] = error
        return data

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        # Network / HTTP error: fallback so the app never crashes
        return make_fallback("onlyfans_http_error_fallback", error=str(e))

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # ---------- Basic identity / image ----------

    profile_name = None
    profile_image_url = None

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        profile_name = og_title["content"].strip()

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        profile_image_url = og_image["content"].strip()

    if not profile_name and soup.title and soup.title.string:
        profile_name = soup.title.string.strip()

    # ---------- Numeric stats ----------

    followers = None
    likes = None
    posts_count = None
    photos_count = None
    videos_count = None

    # 1) Try meta description (common older pattern)
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    if meta_desc_tag and meta_desc_tag.get("content"):
        desc = meta_desc_tag["content"]

        likes_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ll]ikes", desc)
        fans_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+(fans|Fans)", desc)
        posts_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]osts?", desc)
        photos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]hotos?", desc)
        videos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Vv]ideos?", desc)

        if likes_match:
            likes = _parse_human_number(likes_match.group(1))
        if fans_match:
            followers = _parse_human_number(fans_match.group(1))
        if posts_match:
            posts_count = _parse_human_number(posts_match.group(1))
        if photos_match:
            photos_count = _parse_human_number(photos_match.group(1))
        if videos_match:
            videos_count = _parse_human_number(videos_match.group(1))

    # 2) Search in full page text for any remaining stats
    text = soup.get_text(separator=" ", strip=True)

    if followers is None:
        fans_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+(fans|Followers?)", text)
        if fans_match:
            followers = _parse_human_number(fans_match.group(1))

    if likes is None:
        likes_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ll]ikes", text)
        if likes_match:
            likes = _parse_human_number(likes_match.group(1))

    if posts_count is None:
        posts_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]osts?", text)
        if posts_match:
            posts_count = _parse_human_number(posts_match.group(1))

    if photos_count is None:
        photos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]hotos?", text)
        if photos_match:
            photos_count = _parse_human_number(photos_match.group(1))

    if videos_count is None:
        videos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Vv]ideos?", text)
        if videos_match:
            videos_count = _parse_human_number(videos_match.group(1))

    # 3) If absolutely nothing numeric was found, use fallback defaults
    if followers is None and likes is None and posts_count is None:
        fb = make_fallback("onlyfans_fallback_no_numbers_found")
        fb["profile_name"] = profile_name or username
        fb["profile_image_url"] = profile_image_url
        return fb

    # 4) Derive core metrics

    if followers is None and likes is not None:
        # Rough guess: ~10% of followers like something at least once
        followers = max(int(likes / 0.1), likes)

    if followers is None:
        followers = 5_000

    avg_views = int(followers * 0.3)

    if likes is not None and followers > 0:
        engagement_rate = round((likes / followers) * 100, 2)
    else:
        engagement_rate = 3.5

    avg_cpm = 20.0

    # Simple ESTIMATES based on public data
    estimated_subscribers = followers  # "fans" on OF ~= subscribers
    estimated_monthly_visits = followers * 15  # assumption-based

    return {
        "platform": "OnlyFans",
        "handle": username,
        "profile_name": profile_name or username,
        "profile_image_url": profile_image_url,
        "followers": followers,
        "likes": likes,
        "posts_count": posts_count,
        "photos_count": photos_count,
        "videos_count": videos_count,
        "avg_views": avg_views,
        "engagement_rate": engagement_rate,
        "avg_cpm": avg_cpm,
        "estimated_subscribers": estimated_subscribers,
        "estimated_monthly_visits": estimated_monthly_visits,
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

    # Extend here for other platforms if needed.
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
        # Should be rare now; fetch_onlyfans_profile itself falls back safely
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
    help="If web lookup failed or is approximate, set this manually.",
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
        profile = st.session_state.web_profile

        # Top section: image + basic identity
        header_cols = st.columns([1, 3])
        with header_cols[0]:
            if profile.get("profile_image_url"):
                st.image(profile["profile_image_url"], width=140)
        with header_cols[1]:
            display_name = profile.get("profile_name") or profile.get("handle")
            st.markdown(f"### {display_name}")
            st.markdown(f"*Platform:* **{profile.get('platform', 'Unknown')}**")
            st.markdown(f"*Handle:* `@{profile.get('handle')}`")

            # Extra stats if present
            extra_bits = []
            if profile.get("followers") is not None:
                extra_bits.append(f"**{profile['followers']:,}** fans")
            if profile.get("likes") is not None:
                extra_bits.append(f"**{profile['likes']:,}** likes")
            if profile.get("posts_count") is not None:
                extra_bits.append(f"**{profile['posts_count']:,}** posts")
            if profile.get("photos_count") is not None:
                extra_bits.append(f"**{profile['photos_count']:,}** photos")
            if profile.get("videos_count") is not None:
                extra_bits.append(f"**{profile['videos_count']:,}** videos")

            if extra_bits:
                st.markdown(" • ".join(extra_bits))

            # Estimated metrics
            est_subs = profile.get("estimated_subscribers")
            est_visits = profile.get("estimated_monthly_visits")
            if est_subs or est_visits:
                st.markdown("#### Estimated audience metrics")
                if est_subs:
                    st.markdown(f"- Estimated subscribers (fans): **{est_subs:,.0f}**")
                if est_visits:
                    st.markdown(f"- Estimated monthly visits: **{est_visits:,.0f}**")

        st.markdown("#### Raw profile data")
        st.json(profile)

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
    "if the site changes its structure. Always respect the platform's terms of service. "
    "Subscriber and visit metrics shown here are estimates derived from public data."
)
