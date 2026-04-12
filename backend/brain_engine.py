"""
TRIBE v2 brain simulation wrapper.

Three execution modes (auto-detected in priority order):
  1. Modal GPU endpoint  (MODAL_BRAIN_URL env var set)
  2. Local tribev2       (tribev2 pip package installed)
  3. Mock engine         (development fallback)
"""

from __future__ import annotations

import base64
import io
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger(__name__)

MODAL_BRAIN_URL = os.getenv("MODAL_BRAIN_URL")  # set after `modal deploy`
CACHE_DIR = os.getenv("TRIBE_CACHE_DIR", "./cache")

# ---------------------------------------------------------------------------
# Modal remote engine
# ---------------------------------------------------------------------------

def _simulate_via_modal(content_path: str) -> Dict[str, Any]:
    """Call the Modal-deployed TRIBE v2 endpoint.

    Handles Modal's 303 redirect on cold starts and retries.
    Sends file as base64 in JSON body (works up to ~100MB files).
    """
    import httpx

    file_size = os.path.getsize(content_path)
    filename = Path(content_path).name
    log.info(
        "Sending %s (%.1f MB) to Modal TRIBE v2...",
        filename, file_size / 1024 / 1024,
    )

    if file_size > 100 * 1024 * 1024:
        raise ValueError(f"File too large ({file_size / 1024 / 1024:.0f} MB). Max 100 MB.")

    with open(content_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    import time

    payload = {"content_base64": content_b64, "filename": filename}
    max_retries = 5
    resp = None

    with httpx.Client(timeout=600, follow_redirects=True) as client:
        for attempt in range(max_retries):
            resp = client.post(MODAL_BRAIN_URL, json=payload)
            if resp.status_code == 200:
                break
            if resp.status_code in (204, 503, 502):
                wait = min(10 * (attempt + 1), 30)
                log.warning(
                    "Modal returned %s (cold start), retrying in %ds (attempt %d/%d)",
                    resp.status_code, wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                continue
            log.error("Modal returned %s: %s", resp.status_code, resp.text[:200])
            raise RuntimeError(f"Modal brain simulation failed: HTTP {resp.status_code}")

    if resp is None or resp.status_code != 200:
        raise RuntimeError(
            f"Modal brain simulation failed after {max_retries} retries: "
            f"HTTP {resp.status_code if resp else 'no response'}"
        )

    data = resp.json()

    predictions_mean = np.array(data["predictions_mean"], dtype=np.float32)

    return {
        "predictions": predictions_mean[np.newaxis, :],
        "roi_means": data["roi_means"],
        "top_regions": data["top_regions"],
        "n_timesteps": data["n_timesteps"],
        "heatmap_bytes": base64.b64decode(data["heatmap_base64"]),
        "temporal_roi_data": data.get("temporal_roi_data", []),
        "temporal_heatmaps": data.get("temporal_heatmaps", []),
    }


# ---------------------------------------------------------------------------
# Local TRIBE v2 engine
# ---------------------------------------------------------------------------

_model: Any = None
_plotter: Any = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from tribev2 import TribeModel

        log.info("Loading TRIBE v2 model locally (this may take a minute)...")
        _model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=CACHE_DIR,
            device="auto",
        )
        log.info("TRIBE v2 model loaded.")
    except ImportError:
        log.warning(
            "tribev2 not installed -- will use mock engine. "
            "Install with: pip install tribev2"
        )
        _model = None
    return _model


def _get_plotter():
    global _plotter
    if _plotter is not None:
        return _plotter
    try:
        from tribev2.plotting.cortical import PlotBrainNilearn

        _plotter = PlotBrainNilearn(mesh="fsaverage5", inflate="half", bg_map="sulcal")
    except ImportError:
        log.warning("tribev2 plotting not available -- heatmaps will be mocked.")
        _plotter = None
    return _plotter


# ---------------------------------------------------------------------------
# Mock engine (for development without GPU / tribev2 installed)
# ---------------------------------------------------------------------------

N_VERTICES = 20_484
N_ROIS = 180

# Deterministic-ish mock ROI names matching HCP MMP1.0 regions we care about
MOCK_ROI_NAMES = [
    "V1", "V2", "V3", "V4", "V3A", "V3B", "V6", "V6A", "V7", "V8",
    "MT", "MST", "FST", "LO1", "LO2", "LO3", "FFC", "VVC", "PIT",
    "VMV1", "VMV2", "VMV3",
    "A1", "A4", "A5", "MBelt", "LBelt", "PBelt", "RI", "TA2", "STGa",
    "AVI", "AAIC", "FOP1", "FOP2", "FOP3", "FOP4", "FOP5", "MI",
    "PoI1", "PoI2", "Ig", "PI",
    "p24", "a24", "p24pr", "33pr", "a32pr", "d32", "p32", "s32", "SCEF",
    "OFC", "pOFC", "10r", "10v", "a10p", "10pp", "10d", "11l", "13l", "25",
    "STS", "STSdp", "STSda", "STSvp", "STSva",
    "TPOJ1", "TPOJ2", "TPOJ3", "TGd", "TGv", "TE1a",
    "PFm", "PGi", "PGs",
    "8C", "8Av", "8BL", "8Ad", "p9-46v", "a9-46v", "46", "9-46d",
    "9a", "9p", "i6-8", "s6-8",
]


def _mock_simulate(content_path: str, seed: int | None = None) -> Dict[str, Any]:
    """Generate plausible-looking mock brain data for dev/demo."""
    rng = np.random.RandomState(seed or hash(content_path) % 2**31)
    n_timesteps = 60
    preds = rng.randn(n_timesteps, N_VERTICES).astype(np.float32)

    roi_values = rng.randn(len(MOCK_ROI_NAMES)).astype(np.float32)
    # Boost fear-related regions for dramatic demo effect
    for i, name in enumerate(MOCK_ROI_NAMES):
        if name in {"AVI", "AAIC", "FOP1", "p24", "a24"}:
            roi_values[i] += 1.5
    roi_means = dict(zip(MOCK_ROI_NAMES, roi_values.tolist()))

    sorted_rois = sorted(roi_means.items(), key=lambda x: abs(x[1]), reverse=True)
    top_regions = [name for name, _ in sorted_rois[:20]]

    return {
        "predictions": preds,
        "roi_means": roi_means,
        "top_regions": top_regions,
        "n_timesteps": n_timesteps,
    }


def _mock_heatmap() -> bytes:
    """Generate a placeholder heatmap PNG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, title in zip(axes, ["Left Hemisphere", "Right Hemisphere"]):
        data = np.random.randn(50, 50)
        ax.imshow(data, cmap="hot", interpolation="bilinear")
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.suptitle("Cortical Activation Heatmap", fontsize=13, fontweight="bold")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate(content_path: str) -> Dict[str, Any]:
    """Run brain simulation on a piece of content.

    Execution priority:
      1. Modal GPU endpoint (if MODAL_BRAIN_URL is set)
      2. Local tribev2 (if installed)
      3. Mock engine (fallback)

    Returns dict with:
      - predictions: (n_timesteps, 20484) ndarray
      - roi_means: {roi_name: float}
      - top_regions: [str] top-20 most activated ROIs
      - n_timesteps: int
    """
    if MODAL_BRAIN_URL:
        log.info("Using Modal GPU for brain simulation")
        return _simulate_via_modal(content_path)

    model = _get_model()
    if model is None:
        log.info("Using mock brain engine for: %s", content_path)
        return _mock_simulate(content_path)

    from tribev2.utils import get_topk_rois, summarize_by_roi

    events = model.get_events_dataframe(video_path=content_path)
    preds, segments = model.predict(events, verbose=True)

    mean_activation = preds.mean(axis=0)
    roi_means_arr = summarize_by_roi(mean_activation, hemi="both", mesh="fsaverage5")
    top_rois = get_topk_rois(mean_activation, hemi="both", mesh="fsaverage5", k=20)

    from tribev2.utils import get_hcp_labels

    labels = get_hcp_labels(mesh="fsaverage5", combine=False, hemi="both")
    roi_means = dict(zip(labels, roi_means_arr.tolist()))

    return {
        "predictions": preds,
        "roi_means": roi_means,
        "top_regions": top_rois,
        "n_timesteps": preds.shape[0],
    }


def generate_heatmap(
    predictions: np.ndarray | None = None,
    precomputed_bytes: bytes | None = None,
) -> bytes:
    """Render a cortical heatmap as PNG bytes.

    If precomputed_bytes are provided (from Modal), returns those directly.
    If predictions are provided and tribev2 plotting is available,
    renders a real brain surface. Otherwise returns a mock.
    """
    if precomputed_bytes:
        return precomputed_bytes

    plotter = _get_plotter()
    if plotter is None or predictions is None:
        return _mock_heatmap()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mean_act = predictions.mean(axis=0) if predictions.ndim > 1 else predictions
    fig, axes = plotter.get_fig_axes(views=["left", "right"])
    plotter.plot_surf(
        mean_act,
        axes=axes,
        views=["left", "right"],
        cmap="hot",
        norm_percentile=95,
        colorbar=True,
        colorbar_title="Activation",
    )
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
