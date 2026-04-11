"""
HCP MMP1.0 ROI-to-emotion mapping and emotional profile scoring.

Maps TRIBE v2's cortical predictions (via HCP parcellation) to a 9-axis
emotional profile using established neuroscience literature on brain
region function.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Emotion dimensions
# ---------------------------------------------------------------------------

EMOTION_DIMENSIONS = [
    "fear",
    "disgust",
    "reward",
    "social_connection",
    "visual_attention",
    "cognitive_load",
    "anxiety",
    "empathy",
    "auditory_engagement",
]


@dataclass
class EmotionScore:
    dimension: str
    score: float  # normalised 0-1
    raw: float
    dominant_regions: List[str]
    interpretation: str


@dataclass
class EmotionalProfile:
    scores: Dict[str, EmotionScore] = field(default_factory=dict)
    top_activated_regions: List[str] = field(default_factory=list)
    timestamp_scores: np.ndarray | None = None  # (n_timesteps, n_dimensions)

    def to_dict(self) -> dict:
        return {
            "scores": {
                k: dataclasses.asdict(v) for k, v in self.scores.items()
            },
            "top_activated_regions": self.top_activated_regions,
        }

    def radar_values(self) -> Dict[str, float]:
        return {k: v.score for k, v in self.scores.items()}


# ---------------------------------------------------------------------------
# HCP ROI -> Emotion dimension mapping
#
# Each entry: list of HCP ROI name patterns (supports wildcards used by
# tribev2.utils.get_hcp_roi_indices) and the human-readable interpretation.
# ---------------------------------------------------------------------------

ROI_EMOTION_MAP: Dict[str, dict] = {
    "fear": {
        "rois": ["AVI", "AAIC", "FOP1", "FOP2", "FOP3", "FOP4", "FOP5",
                 "MI", "PoI1", "PoI2", "Ig"],
        "label": "Fear / Threat Detection",
        "interpretation": "Content triggers visceral fear or threat detection",
    },
    "disgust": {
        "rois": ["AVI", "AAIC", "FOP1", "FOP2", "FOP3", "PI", "Ig"],
        "label": "Disgust / Interoception",
        "interpretation": "Content triggers visceral discomfort or rejection",
    },
    "anxiety": {
        "rois": ["p24", "a24", "p24pr", "33pr", "a32pr", "d32", "p32",
                 "s32", "SCEF"],
        "label": "Anxiety / Cognitive Conflict",
        "interpretation": "Content creates tension, unease, or inner conflict",
    },
    "reward": {
        "rois": ["OFC", "pOFC", "10r", "10v", "a10p", "10pp", "10d",
                 "11l", "13l", "25"],
        "label": "Reward / Pleasure",
        "interpretation": "Content feels rewarding, appealing, or desirable",
    },
    "social_connection": {
        "rois": ["STS", "STSdp", "STSda", "STSvp", "STSva",
                 "TPOJ1", "TPOJ2", "TPOJ3", "TGd", "TGv", "TE1a"],
        "label": "Social Connection / Empathy",
        "interpretation": "Content triggers social cognition and empathetic processing",
    },
    "empathy": {
        "rois": ["TPOJ1", "TPOJ2", "TPOJ3", "TGd", "TGv",
                 "PFm", "PGi", "PGs"],
        "label": "Empathy / Perspective-Taking",
        "interpretation": "Content activates emotional resonance and perspective-taking",
    },
    "visual_attention": {
        "rois": ["V1", "V2", "V3", "V4", "V3A", "V3B", "V6", "V6A",
                 "V7", "V8", "MT", "MST", "FST", "LO1", "LO2", "LO3",
                 "FFC", "VVC", "PIT", "VMV1", "VMV2", "VMV3"],
        "label": "Visual Attention / Salience",
        "interpretation": "High visual capture, strong attention engagement",
    },
    "cognitive_load": {
        "rois": ["8C", "8Av", "8BL", "8Ad", "p9-46v", "a9-46v",
                 "46", "9-46d", "9a", "9p", "i6-8", "s6-8"],
        "label": "Cognitive Load / Deliberation",
        "interpretation": "Content demands focused thinking and executive processing",
    },
    "auditory_engagement": {
        "rois": ["A1", "A4", "A5", "MBelt", "LBelt", "PBelt",
                 "RI", "TA2", "STGa"],
        "label": "Auditory Engagement",
        "interpretation": "Sound design is highly engaging",
    },
}


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def compute_emotional_profile(
    roi_means: Dict[str, float],
    top_regions: List[str],
    temporal_roi_means: np.ndarray | None = None,
) -> EmotionalProfile:
    """Turn per-ROI activation values into a 9-axis EmotionalProfile.

    Args:
        roi_means: mapping of ROI name -> mean activation (from summarize_by_roi).
        top_regions: top-K activated region names.
        temporal_roi_means: optional (n_timesteps, n_rois) for per-timepoint scoring.

    Returns:
        EmotionalProfile with normalised scores per dimension.
    """
    raw_scores: Dict[str, Tuple[float, List[str]]] = {}

    for dim, spec in ROI_EMOTION_MAP.items():
        matched_vals: List[float] = []
        matched_names: List[str] = []
        for roi_name in spec["rois"]:
            if roi_name in roi_means:
                matched_vals.append(roi_means[roi_name])
                matched_names.append(roi_name)
        raw = float(np.mean(matched_vals)) if matched_vals else 0.0
        raw_scores[dim] = (raw, matched_names)

    all_raw = [v for v, _ in raw_scores.values()]
    rmin, rmax = (min(all_raw), max(all_raw)) if all_raw else (0.0, 1.0)
    spread = rmax - rmin if rmax != rmin else 1.0

    profile = EmotionalProfile(top_activated_regions=top_regions)

    for dim, (raw, regions) in raw_scores.items():
        normalised = float(np.clip((raw - rmin) / spread, 0.0, 1.0))
        profile.scores[dim] = EmotionScore(
            dimension=dim,
            score=normalised,
            raw=raw,
            dominant_regions=regions,
            interpretation=ROI_EMOTION_MAP[dim]["interpretation"],
        )

    return profile


def format_profile_for_llm(profile: EmotionalProfile) -> str:
    """Produce a concise text summary of the emotional profile for the LLM interpreter."""
    lines = ["## Brain Emotional Profile\n"]
    sorted_scores = sorted(
        profile.scores.values(), key=lambda s: s.score, reverse=True
    )
    for s in sorted_scores:
        bar = "█" * int(s.score * 10) + "░" * (10 - int(s.score * 10))
        lines.append(
            f"- **{ROI_EMOTION_MAP[s.dimension]['label']}**: "
            f"{s.score:.0%} [{bar}]  (regions: {', '.join(s.dominant_regions[:3])})"
        )
    lines.append(f"\n**Top activated brain regions**: {', '.join(profile.top_activated_regions[:10])}")
    return "\n".join(lines)
