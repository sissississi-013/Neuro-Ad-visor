"""
Text/caption polishing via OpenAI.

Rewrites social media captions, CTAs, and copy based on
brain-informed suggestions.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from openai import OpenAI

log = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def polish_caption(
    original_caption: str,
    modifications: List[str],
    platform: str = "instagram",
    tone: str = "engaging and authentic",
) -> str:
    """Rewrite a caption applying brain-informed modifications.

    Args:
        original_caption: The current caption/copy.
        modifications: List of specific changes to apply.
        platform: Target social media platform.
        tone: Desired tone of voice.

    Returns:
        The rewritten caption.
    """
    mod_text = "\n".join(f"- {m}" for m in modifications)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are an expert social media copywriter for {platform}. "
                    f"Rewrite captions to be {tone}. Apply the specific "
                    f"modifications listed. Keep the core message intact. "
                    f"Output ONLY the new caption, nothing else."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original caption:\n{original_caption}\n\n"
                    f"Apply these modifications:\n{mod_text}\n\n"
                    f"Rewrite the caption for {platform}."
                ),
            },
        ],
        max_tokens=500,
        temperature=0.7,
    )

    result = response.choices[0].message.content or original_caption
    log.info("Caption polished: %d -> %d chars", len(original_caption), len(result))
    return result


def generate_caption(
    image_description: str,
    emotional_targets: List[str],
    platform: str = "instagram",
) -> str:
    """Generate a new caption from scratch based on image description and emotional goals."""
    targets_text = ", ".join(emotional_targets)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are an expert social media copywriter for {platform}. "
                    f"Write captions that are engaging, authentic, and optimized for "
                    f"the platform's algorithm. Output ONLY the caption."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write a caption for this image:\n{image_description}\n\n"
                    f"Emotional goals: maximize {targets_text}\n"
                    f"Platform: {platform}"
                ),
            },
        ],
        max_tokens=300,
        temperature=0.8,
    )

    return response.choices[0].message.content or ""
