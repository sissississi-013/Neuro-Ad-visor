"""
Image polishing via OpenAI image generation.

Takes approved suggestions and generates modified versions of the original image.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Optional

from openai import OpenAI

log = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def polish_image(
    original_image_path: Path,
    modification_prompt: str,
    style_hint: str = "social media ad, professional, high quality",
) -> bytes:
    """Generate a modified version of an image based on a modification prompt.

    Uses OpenAI's image generation to create a new image that applies
    the suggested modifications while preserving the content's intent.

    Returns PNG bytes of the generated image.
    """
    with open(original_image_path, "rb") as f:
        original_b64 = base64.b64encode(f.read()).decode()

    full_prompt = (
        f"Create a social media image with these specific modifications applied:\n"
        f"{modification_prompt}\n\n"
        f"Style: {style_hint}\n"
        f"Maintain the same core subject and message, but apply the described changes."
    )

    log.info("Generating polished image: %s", modification_prompt[:80])

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=full_prompt,
            n=1,
            size="1024x1024",
        )

        image_b64 = response.data[0].b64_json
        if image_b64:
            return base64.b64decode(image_b64)

        # If b64 not returned, try URL
        import httpx
        image_url = response.data[0].url
        if image_url:
            resp = httpx.get(image_url, timeout=30)
            return resp.content

    except Exception as exc:
        log.error("Image generation failed: %s", exc)
        raise

    raise RuntimeError("No image data returned from OpenAI")


def describe_image(image_path: Path) -> str:
    """Use GPT-4o vision to describe an image for context."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe this social media image in detail. "
                            "Include: colors, subjects, mood, composition, text/copy, "
                            "and any emotional tone it conveys. Be specific."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    return response.choices[0].message.content or ""
