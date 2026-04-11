"""
Perplexity Agent API integration for brain interpretation.

Takes a raw emotional profile from brain simulation and produces
human-readable insights + actionable suggestion cards, grounded in
real-time neuroscience research via web search.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from perplexity import Perplexity

from .emotion_mapping import EmotionalProfile, format_profile_for_llm

log = logging.getLogger(__name__)

client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))

MODEL = "openai/gpt-5.4"

SYSTEM_INSTRUCTIONS = """\
You are a neuroscience-trained content analyst for social media. You receive
brain simulation data from Meta's TRIBE v2 model (fMRI-trained on 720 subjects).

Your job:
1. Interpret the emotional profile in plain English -- explain WHAT emotions the
   content triggers and WHY (reference specific brain regions and their functions).
2. Ground your analysis by searching for relevant neuroscience research and
   platform-specific content best practices.
3. Generate exactly 3-5 ranked SUGGESTIONS for improving the content. Each
   suggestion must include:
   - A clear, specific modification (not vague "make it better")
   - Which emotion dimension it targets
   - Estimated impact (e.g. "reduce fear ~30%")
   - Brief neuroscience rationale

Be direct, concrete, and actionable. Speak like a brilliant creative director
who also has a neuroscience PhD.
"""

SUGGESTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "brain_analysis",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "2-3 sentence plain-English summary of the brain response",
                },
                "dominant_emotion": {
                    "type": "string",
                    "description": "The strongest emotion triggered",
                },
                "concern_level": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                    "description": "How concerning the emotional response is",
                },
                "suggestions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "target_emotion": {"type": "string"},
                            "estimated_impact": {"type": "string"},
                            "rationale": {"type": "string"},
                            "modification_type": {
                                "type": "string",
                                "enum": ["image", "text", "audio", "layout"],
                            },
                        },
                        "required": [
                            "id", "title", "description", "target_emotion",
                            "estimated_impact", "rationale", "modification_type",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["summary", "dominant_emotion", "concern_level", "suggestions"],
            "additionalProperties": False,
        },
    },
}


@dataclass
class Suggestion:
    id: str
    title: str
    description: str
    target_emotion: str
    estimated_impact: str
    rationale: str
    modification_type: str  # image | text | audio | layout


@dataclass
class InterpretationResult:
    summary: str
    dominant_emotion: str
    concern_level: str
    suggestions: List[Suggestion]
    raw_response: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "dominant_emotion": self.dominant_emotion,
            "concern_level": self.concern_level,
            "suggestions": [s.__dict__ for s in self.suggestions],
        }


def interpret(
    profile: EmotionalProfile,
    content_description: str = "",
    platform: str = "instagram",
) -> InterpretationResult:
    """Synchronous interpretation via Perplexity Agent API.

    Sends the emotional profile + optional content description to the LLM,
    which uses web_search to ground its analysis, then returns structured
    suggestions.
    """
    profile_text = format_profile_for_llm(profile)

    user_input = (
        f"Analyze this social media content's brain response and suggest improvements.\n\n"
        f"**Platform**: {platform}\n"
        f"**Content description**: {content_description or 'Not provided'}\n\n"
        f"{profile_text}"
    )

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=user_input,
        tools=[
            {
                "type": "web_search",
                "filters": {
                    "search_domain_filter": [
                        "nature.com", "science.org", "ncbi.nlm.nih.gov",
                        "pubmed.ncbi.nlm.nih.gov", ".edu",
                    ],
                    "search_recency_filter": "year",
                },
            },
        ],
        response_format=SUGGESTION_SCHEMA,
        max_output_tokens=2048,
    )

    raw_text = response.output_text
    log.info("Perplexity response length: %d chars", len(raw_text or ""))

    return _parse_response(raw_text)


def interpret_with_image(
    profile: EmotionalProfile,
    image_base64: str,
    platform: str = "instagram",
) -> InterpretationResult:
    """Interpretation with the actual image attached so the LLM can see the content."""
    profile_text = format_profile_for_llm(profile)

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Analyze this social media content's brain response.\n\n"
                            f"**Platform**: {platform}\n\n"
                            f"{profile_text}\n\n"
                            f"The image is attached. Use BOTH the brain data and "
                            f"what you see in the image to make specific suggestions."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{image_base64}",
                    },
                ],
            }
        ],
        tools=[{"type": "web_search"}],
        response_format=SUGGESTION_SCHEMA,
        max_output_tokens=2048,
    )

    return _parse_response(response.output_text)


def stream_interpretation(
    profile: EmotionalProfile,
    content_description: str = "",
    platform: str = "instagram",
) -> Any:
    """Return a streaming response for real-time UI updates.

    Yields raw SSE events. NOTE: structured output + streaming may not be
    combinable on all models; falls back to free-text streaming.
    """
    profile_text = format_profile_for_llm(profile)

    user_input = (
        f"Analyze this social media content's brain response and suggest improvements.\n\n"
        f"**Platform**: {platform}\n"
        f"**Content description**: {content_description or 'Not provided'}\n\n"
        f"{profile_text}"
    )

    stream = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=user_input,
        tools=[{"type": "web_search"}],
        stream=True,
        max_output_tokens=2048,
    )

    return stream


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _parse_response(raw_text: str | None) -> InterpretationResult:
    """Parse structured JSON from the LLM response."""
    if not raw_text:
        return InterpretationResult(
            summary="No interpretation available.",
            dominant_emotion="unknown",
            concern_level="low",
            suggestions=[],
        )

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        log.warning("Failed to parse JSON, returning raw text as summary")
        return InterpretationResult(
            summary=raw_text[:500],
            dominant_emotion="unknown",
            concern_level="moderate",
            suggestions=[],
            raw_response=raw_text,
        )

    suggestions = [
        Suggestion(**s) for s in data.get("suggestions", [])
    ]

    return InterpretationResult(
        summary=data.get("summary", ""),
        dominant_emotion=data.get("dominant_emotion", "unknown"),
        concern_level=data.get("concern_level", "moderate"),
        suggestions=suggestions,
        raw_response=raw_text,
    )
