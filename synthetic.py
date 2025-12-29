# synthetic.py

import math
import random
from typing import Dict, Optional

import numpy as np
import pandas as pd


def _safe_get(profile: Dict, *keys, default=None):
    for k in keys:
        if k in profile and profile[k] is not None:
            return profile[k]
    return default


def generate_synthetic_cohort(
    profile: Dict,
    n: int = 300,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic cohort of similar creators around the given profile.

    Columns:
      - followers
      - avg_views
      - engagement_rate
      - cpm
      - suggested_price
    """
    rng = np.random.default_rng(random_state)

    # Base metrics from profile with robust fallbacks
    followers = float(_safe_get(profile, "followers", "follower_count", default=100_000))
    avg_views = float(
        _safe_get(profile, "avg_views", "avg_video_views", "story_views", default=followers * 0.15)
    )
    engagement_rate = float(_safe_get(profile, "engagement_rate", default=0.05))
    base_cpm = float(_safe_get(profile, "avg_cpm", "cpm", default=25.0))

    # Clamp to avoid degenerate values
    followers = max(followers, 1_000)
    avg_views = max(avg_views, 1_000)
    engagement_rate = max(min(engagement_rate, 0.25), 0.005)
    base_cpm = max(base_cpm, 5.0)

    # Use log-normal-ish spreads around the profile
    followers_scale = 0.5  # 50% spread
    views_scale = 0.5
    cpm_scale = 0.35
    er_scale = 0.35

    followers_samples = np.clip(
        rng.lognormal(mean=math.log(followers), sigma=followers_scale, size=n),
        1_000,
        followers * 20
    )
    views_samples = np.clip(
        rng.lognormal(mean=math.log(avg_views), sigma=views_scale, size=n),
        1_000,
        followers_samples * 0.8
    )
    er_samples = np.clip(
        rng.normal(loc=engagement_rate, scale=engagement_rate * er_scale, size=n),
        0.003,
        0.35
    )
    cpm_samples = np.clip(
        rng.normal(loc=base_cpm, scale=base_cpm * cpm_scale, size=n),
        5.0,
        250.0
    )

    suggested_price = (views_samples / 1000.0) * cpm_samples

    df = pd.DataFrame(
        {
            "followers": followers_samples.astype(int),
            "avg_views": views_samples.astype(int),
            "engagement_rate": er_samples,
            "cpm": cpm_samples,
            "suggested_price": suggested_price,
        }
    )

    return df


def percentile_rank(values: pd.Series, value: Optional[float]) -> Optional[float]:
    """
    Simple percentile rank implementation: percentage of values <= value.
    Returns 0–100 or None if invalid.
    """
    if value is None:
        return None
    try:
        arr = np.asarray(values, dtype=float)
    except Exception:
        return None
    if arr.size == 0:
        return None
    return float(np.mean(arr <= float(value)) * 100.0)


def build_profile_percentiles(
    profile: Dict,
    cohort_df: pd.DataFrame
) -> Dict[str, Optional[float]]:
    """
    Percentiles for the *profile* vs synthetic peers:
      - followers_pct
      - views_pct
      - engagement_pct
    """
    if cohort_df is None or cohort_df.empty:
        return {
            "followers_pct": None,
            "views_pct": None,
            "engagement_pct": None,
        }

    followers = _safe_get(profile, "followers", "follower_count")
    avg_views = _safe_get(profile, "avg_views", "avg_video_views", "story_views")
    engagement_rate = _safe_get(profile, "engagement_rate")

    return {
        "followers_pct": percentile_rank(cohort_df["followers"], followers) if followers else None,
        "views_pct": percentile_rank(cohort_df["avg_views"], avg_views) if avg_views else None,
        "engagement_pct": percentile_rank(
            cohort_df["engagement_rate"], engagement_rate
        )
        if engagement_rate
        else None,
    }


def build_pricing_percentiles(
    profile: Dict,
    cohort_df: pd.DataFrame,
    recommended_price: Optional[float],
) -> Dict[str, Optional[float]]:
    """
    Percentiles for the *recommended price* vs synthetic peers:
      - price_pct (absolute price vs synthetic suggested_price)
      - cpm_pct   (effective CPM vs synthetic cpm)
    """
    if cohort_df is None or cohort_df.empty:
        return {"price_pct": None, "cpm_pct": None}

    if recommended_price is None:
        return {"price_pct": None, "cpm_pct": None}

    # Effective CPM for the recommended price based on profile views
    views = float(
        _safe_get(profile, "avg_views", "avg_video_views", "story_views", default=0) or 0
    )
    if views <= 0:
        effective_cpm = None
    else:
        effective_cpm = float(recommended_price) / (views / 1000.0)

    price_pct = percentile_rank(cohort_df["suggested_price"], recommended_price)
    cpm_pct = percentile_rank(cohort_df["cpm"], effective_cpm) if effective_cpm else None

    return {"price_pct": price_pct, "cpm_pct": cpm_pct}


def percentile_band_label(p: Optional[float]) -> str:
    """
    Turns a percentile into a human-readable band label.
    """
    if p is None:
        return "n/a"
    if p < 20:
        return f"{p:.0f}th • Underpriced vs peers"
    if p < 40:
        return f"{p:.0f}th • Slightly low vs peers"
    if p <= 60:
        return f"{p:.0f}th • In line with peers"
    if p <= 80:
        return f"{p:.0f}th • Strong (top 20%)"
    return f"{p:.0f}th • Very strong (top 10%)"


def short_percentile(p: Optional[float]) -> str:
    if p is None:
        return "—"
    return f"{p:.0f}th"
