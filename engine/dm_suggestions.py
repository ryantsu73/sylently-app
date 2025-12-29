# engine/dm_suggestions.py

import streamlit as st
from textwrap import dedent


def _generate_dm(context: str, goal: str, tone: str) -> str:
    base_intro = "Hey love,"
    if tone == "Sweet & caring":
        base_intro = "Hey babe,"
    elif tone == "Playful & flirty":
        base_intro = "Heeey trouble 😉,"
    elif tone == "Direct & confident":
        base_intro = "Hey you,"

    goal_line = ""
    if goal == "Save from churn":
        goal_line = (
            "I noticed you’ve been a little quieter lately and I just wanted to check in on you. "
            "If there's anything you'd love more (or less) of from me, tell me honestly."
        )
    elif goal == "Upsell to higher tier":
        goal_line = (
            "You've been such a real one that I wanted to give you first dibs on my higher tier. "
            "It’s where I drop the stuff I can’t post anywhere else, plus little behind-the-scenes moments just for us."
        )
    elif goal == "Re-engage inactive fan":
        goal_line = (
            "It's been a minute since I saw your name pop up and I kinda miss you in my notifications. "
            "I’ve been posting some new things I really think you’d enjoy."
        )
    else:
        goal_line = (
            "I wanted to send something a little more personal than just another post on the feed."
        )

    tone_addon = ""
    if tone == "Sweet & caring":
        tone_addon = (
            "You genuinely mean a lot to me here, not just as a sub but as a person showing up for me."
        )
    elif tone == "Playful & flirty":
        tone_addon = (
            "You know I notice when you show up for me… and when you disappear 👀."
        )
    elif tone == "Direct & confident":
        tone_addon = (
            "I'm building something special here and I want my real ones with me while I do it."
        )
    else:
        tone_addon = "You always stand out in my list, just saying."

    context_line = ""
    ctx = context.strip()
    if ctx:
        context_line = f"\n\n(P.S. I was thinking about you because: {ctx})"

    closing = ""
    if tone == "Sweet & caring":
        closing = "Thank you for being here with me, seriously. 🤍"
    elif tone == "Playful & flirty":
        closing = "Now come say hi so I know you’re still mine 😈"
    elif tone == "Direct & confident":
        closing = "If you’re down, I’d love to keep you close while I keep leveling this up."
    else:
        closing = "Either way, I appreciate you more than you think."

    msg = dedent(
        f"""
        {base_intro}

        {goal_line}

        {tone_addon}{context_line}

        {closing}
        """
    ).strip()

    return msg


def render_ui():
    st.subheader("💬 DM Studio")

    st.markdown(
        """
        Draft on‑brand DMs for your top fans.

        This doesn’t call any external AI — it’s a **lightweight template engine** you can tweak.
        """
    )

    col_left, col_right = st.columns([2, 1])

    with col_left:
        context = st.text_area(
            "What do you know about this fan? (optional)",
            placeholder="Example: tipped $80 in the past, was super active in DMs, recently went quiet for 3 weeks…",
            height=130,
        )

    with col_right:
        goal = st.selectbox(
            "Goal of this DM",
            [
                "Save from churn",
                "Upsell to higher tier",
                "Re-engage inactive fan",
                "Just nurture / say thanks",
            ],
        )
        tone = st.selectbox(
            "Tone",
            [
                "Sweet & caring",
                "Playful & flirty",
                "Direct & confident",
                "Soft & appreciative",
            ],
        )

    if st.button("Generate DM"):
        dm = _generate_dm(context=context, goal=goal, tone=tone)
        st.markdown("#### Suggested DM")
        st.code(dm, language="text")
