"""
Multimodal polishing orchestrator.

Dispatches user-approved suggestions to the appropriate polishing model
(image, text, audio) and collects results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .interpreter import Suggestion

log = logging.getLogger(__name__)


@dataclass
class PolishResult:
    original_path: Optional[Path] = None
    polished_image: Optional[bytes] = None
    polished_caption: Optional[str] = None
    polished_audio: Optional[bytes] = None
    applied_suggestions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "has_polished_image": self.polished_image is not None,
            "polished_caption": self.polished_caption,
            "has_polished_audio": self.polished_audio is not None,
            "applied_suggestions": self.applied_suggestions,
            "errors": self.errors,
        }


def polish(
    suggestions: List[Suggestion],
    content_path: Optional[Path] = None,
    original_caption: str = "",
    platform: str = "instagram",
) -> PolishResult:
    """Apply approved suggestions using the appropriate polishing models.

    Groups suggestions by modification_type and dispatches to specialised
    models. Returns a unified PolishResult.
    """
    result = PolishResult(original_path=content_path)

    image_suggestions = [s for s in suggestions if s.modification_type == "image"]
    text_suggestions = [s for s in suggestions if s.modification_type == "text"]
    audio_suggestions = [s for s in suggestions if s.modification_type == "audio"]

    if image_suggestions and content_path:
        result = _polish_image(image_suggestions, content_path, result)

    if text_suggestions and original_caption:
        result = _polish_text(text_suggestions, original_caption, platform, result)

    if audio_suggestions:
        log.info("Audio polishing requested but not yet implemented (stretch goal)")
        result.errors.append("Audio polishing is a stretch goal -- not yet available")

    layout_suggestions = [s for s in suggestions if s.modification_type == "layout"]
    if layout_suggestions:
        for s in layout_suggestions:
            result.applied_suggestions.append(f"[layout] {s.title}: {s.description}")

    return result


def _polish_image(
    suggestions: List[Suggestion],
    content_path: Path,
    result: PolishResult,
) -> PolishResult:
    """Dispatch image suggestions to the image polisher."""
    from .models.image_polisher import polish_image

    combined_prompt = "\n".join(
        f"- {s.title}: {s.description}" for s in suggestions
    )

    try:
        polished_bytes = polish_image(
            original_image_path=content_path,
            modification_prompt=combined_prompt,
        )
        result.polished_image = polished_bytes
        for s in suggestions:
            result.applied_suggestions.append(f"[image] {s.title}")
        log.info("Image polished successfully (%d bytes)", len(polished_bytes))
    except Exception as exc:
        log.error("Image polishing failed: %s", exc)
        result.errors.append(f"Image polishing failed: {exc}")

    return result


def _polish_text(
    suggestions: List[Suggestion],
    original_caption: str,
    platform: str,
    result: PolishResult,
) -> PolishResult:
    """Dispatch text suggestions to the text polisher."""
    from .models.text_polisher import polish_caption

    modifications = [f"{s.title}: {s.description}" for s in suggestions]

    try:
        new_caption = polish_caption(
            original_caption=original_caption,
            modifications=modifications,
            platform=platform,
        )
        result.polished_caption = new_caption
        for s in suggestions:
            result.applied_suggestions.append(f"[text] {s.title}")
        log.info("Caption polished: '%s...'", new_caption[:60])
    except Exception as exc:
        log.error("Text polishing failed: %s", exc)
        result.errors.append(f"Text polishing failed: {exc}")

    return result
