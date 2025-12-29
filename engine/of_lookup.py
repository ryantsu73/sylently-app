# engine/of_lookup.py

import re
from dataclasses import dataclass
from typing import Optional

import requests
import streamlit as st


@dataclass
class OFProfile:
    handle: str
    url: str
    found_live: bool
    title: Optional[str] = None
    top_percent: Optional[str] = None
    is_free: Optional[bool] = None
    monthly_price: Optional[float] = None
    raw_snippet: Optional[str] = None


def _normalize_handle_or_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""

    # Already a full URL
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw

    # Contains onlyfans.com but no scheme
    if "onlyfans.com" in raw:
        return "https://" + raw.lstrip("/")

    # Treat as handle
    return f"https://onlyfans.com/{raw.lstrip('@').strip('/')}"


def _try_fetch_live_profile(url: str) -> Optional[OFProfile]:
    """
    Try to fetch the public OnlyFans page.

    This only uses normal HTTP GET and does NOT bypass any login, paywalls,
    or protections. If the page is not publicly readable, this will just fail
    and we'll fall back to a mock profile.
    """
    try:
        resp = requests.get(
            url,
            timeout=6,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0 Safari/537.36"
                )
            },
        )
    except Exception:
        return None

    if resp.status_code != 200:
        return None

    html = resp.text

    # Very lightweight parsing – just to show that we touched the real page.
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = None
    if title_match:
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()

    # A lot of profiles mention "Top X%" somewhere in the markup
    top_match = re.search(r"Top\s+(\d+)%", html)
    top_percent = None
    if top_match:
        top_percent = f"Top {top_match.group(1)}%"

    # Price parsing from the raw HTML is messy and site‑specific; keep it simple
    monthly_price = None

    return OFProfile(
        handle=url.rsplit("/", 1)[-1] or "unknown",
        url=url,
        found_live=True,
        title=title,
        top_percent=top_percent,
        monthly_price=monthly_price,
        is_free=None,
        raw_snippet=html[:800],  # small snippet so we don't dump everything
    )


def _mock_profile(handle: str, url: str) -> OFProfile:
    """
    Fallback profile so the demo always works, even if OnlyFans blocks scraping.
    """
    return OFProfile(
        handle=handle or "creator_demo",
        url=url,
        found_live=False,
        title=f"{handle or 'Creator Demo'} | OnlyFans",
        top_percent="Top 2.3%",
        is_free=False,
        monthly_price=14.99,
        raw_snippet="(mocked profile data – used when live page is not accessible)",
    )


def _compute_pricing_hint(profile: OFProfile) -> dict:
    """
    Simple heuristic to show how you might connect OF data to pricing ideas.
    """
    if profile.monthly_price:
        base = profile.monthly_price
    else:
        base = 12.0  # generic anchor if we don't know

    recommended_low = round(base * 0.9, 2)
    recommended_high = round(base * 1.5, 2)

    if profile.top_percent:
        if "1" in profile.top_percent:
            tier_note = "Already in a very high percentile — tests should be conservative."
        else:
            tier_note = "Solid performer — you have room to experiment with higher tiers."
    else:
        tier_note = "Run a small test first; we don't have percentile data."

    return {
        "base_price": base,
        "test_low": recommended_low,
        "test_high": recommended_high,
        "note": tier_note,
    }


def render_ui():
    st.subheader("🔗 OnlyFans Profile Lookup")

    st.markdown(
        """
Connect a public OnlyFans profile to Sylently.

- Paste a **handle** (like `@creatorname`) or a **full profile URL**
- We try to read the public page
- If the site blocks us, we drop into a **mocked profile** so the flow still works
        """
    )

    handle_or_url = st.text_input(
        "OnlyFans handle or profile URL",
        placeholder="e.g. @creatorname or https://onlyfans.com/creatorname",
    )

    if not handle_or_url:
        st.info("Enter a handle or URL above to get started.")
        return

    url = _normalize_handle_or_url(handle_or_url)

    if st.button("Lookup profile"):
        with st.spinner("Connecting to OnlyFans…"):
            live_profile = _try_fetch_live_profile(url)

        if live_profile is None:
            profile = _mock_profile(handle_or_url.strip().lstrip("@"), url)
            st.warning(
                "Could not read live public data from OnlyFans (likely needs login or is protected). "
                "Showing a mocked profile so you can still see how the integration works."
            )
        else:
            profile = live_profile
            st.success("Connected to public OnlyFans page.")

        # --- Profile summary card ---
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### Profile summary")
            st.markdown(f"**Handle:** `{profile.handle}`")
            st.markdown(f"**Profile URL:** {profile.url}")
            if profile.title:
                st.markdown(f"**Page title:** {profile.title}")
            if profile.top_percent:
                st.markdown(f"**Approx. rank:** {profile.top_percent}")
            if profile.monthly_price is not None:
                st.markdown(f"**Advertised monthly price:** ${profile.monthly_price:.2f}")
            elif not profile.found_live:
                st.markdown("**Advertised monthly price:** $14.99 (mocked)")

        with col2:
            hints = _compute_pricing_hint(profile)
            st.markdown("#### Pricing insight")

            st.metric("Baseline price", f"${hints['base_price']:.2f}")
            st.metric(
                "Suggested test range",
                f"${hints['test_low']:.2f} – ${hints['test_high']:.2f}",
            )
            st.caption(hints["note"])

        st.markdown("---")

        # Optional: show a tiny HTML snippet when we actually scraped
        if profile.found_live and profile.raw_snippet:
            with st.expander("Show raw HTML snippet (debug)"):
                st.text(profile.raw_snippet)
        else:
            st.caption(
                "Using mocked data so the prototype works even when OnlyFans blocks scraping."
            )
