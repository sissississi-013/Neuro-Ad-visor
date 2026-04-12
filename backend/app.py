"""
FastAPI application -- FeedYourBrain API.

Endpoints for the 5-phase pipeline:
  1. Upload content
  2. Run brain simulation + emotion mapping
  3. LLM interpretation + suggestions
  4. Apply polishing (user-approved suggestions)
  5. Re-simulate for before/after comparison
"""

from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from . import brain_engine, content_processor, interpreter, polisher
from .emotion_mapping import compute_emotional_profile
from .interpreter import Suggestion

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
log = logging.getLogger("feedyourbrain")


def _extract_video_thumbnail(video_path: Path) -> Optional[str]:
    """Extract a frame from the middle of a video and return as base64 PNG."""
    import subprocess
    import tempfile

    try:
        thumb = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        thumb.close()
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vf", "select=eq(n\\,30)", "-frames:v", "1",
                "-q:v", "2", thumb.name,
            ],
            capture_output=True, timeout=15,
        )
        if os.path.getsize(thumb.name) > 0:
            with open(thumb.name, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        log.warning("Thumbnail extraction failed: %s", e)
    return None

app = FastAPI(
    title="FeedYourBrain",
    description="Neuro-powered content intelligence — simulate brain reactions to social media content",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File-backed session store -- survives hot reloads
import json as _json
import pickle
from pathlib import Path as _Path

_SESSION_DIR = _Path("./sessions")
_SESSION_DIR.mkdir(exist_ok=True)


class _Sessions:
    """Dict-like session store backed by pickle files. Survives uvicorn reloads."""

    def get(self, key: str) -> Optional[dict]:
        p = _SESSION_DIR / f"{key}.pkl"
        if p.exists():
            try:
                return pickle.loads(p.read_bytes())
            except Exception:
                return None
        return None

    def __setitem__(self, key: str, value: dict):
        p = _SESSION_DIR / f"{key}.pkl"
        p.write_bytes(pickle.dumps(value))

    def __contains__(self, key: str) -> bool:
        return (_SESSION_DIR / f"{key}.pkl").exists()


sessions = _Sessions()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    platform: str = "instagram"
    caption: str = ""


class PolishRequest(BaseModel):
    session_id: str
    approved_suggestion_ids: List[str]
    caption: str = ""
    platform: str = "instagram"


class CompareRequest(BaseModel):
    session_id: str


# ---------------------------------------------------------------------------
# Phase 1: Upload / ingest content
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_content(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    platform: str = Form("instagram"),
    caption: str = Form(""),
):
    """Upload an image/video file or provide a URL to analyze."""
    session_id = uuid.uuid4().hex

    if file:
        data = await file.read()
        path = content_processor.save_upload(data, file.filename or "upload.bin")
    elif url:
        path = content_processor.download_from_url(url)
    else:
        raise HTTPException(400, "Provide either a file upload or a URL")

    content_type = content_processor.classify_content(path)

    sessions[session_id] = {
        "path": str(path),
        "content_type": content_type,
        "platform": platform,
        "caption": caption,
    }

    return {
        "session_id": session_id,
        "content_type": content_type,
        "filename": path.name,
    }


# ---------------------------------------------------------------------------
# Phase 2: Brain simulation + emotion mapping
# ---------------------------------------------------------------------------

@app.post("/api/simulate/{session_id}")
async def run_simulation(session_id: str):
    """Run TRIBE v2 brain simulation on uploaded content."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    content_path = Path(session["path"])

    # Image-to-video conversion happens ON Modal (not locally).
    # Videos and audio go straight through. Only convert locally if running local TRIBE v2.
    if brain_engine.MODAL_BRAIN_URL:
        prepared_path = content_path  # Modal handles all conversion
    elif brain_engine._get_model() is not None:
        prepared_path = content_processor.prepare_for_tribe(content_path)
    else:
        prepared_path = content_path  # mock mode

    log.info("Running brain simulation on: %s", prepared_path)
    sim_result = brain_engine.simulate(str(prepared_path))

    profile = compute_emotional_profile(
        roi_means=sim_result["roi_means"],
        top_regions=sim_result["top_regions"],
    )

    heatmap_bytes = brain_engine.generate_heatmap(
        predictions=sim_result.get("predictions"),
        precomputed_bytes=sim_result.get("heatmap_bytes"),
    )
    heatmap_b64 = base64.b64encode(heatmap_bytes).decode()

    # Compute per-timestep emotional profiles for the timeline
    temporal_roi_data = sim_result.get("temporal_roi_data", [])
    timeline = []
    for t, t_roi in enumerate(temporal_roi_data):
        t_profile = compute_emotional_profile(
            roi_means=t_roi,
            top_regions=sim_result["top_regions"],
        )
        timeline.append({
            "t": t,
            "seconds": t * 2.0,  # TRs are ~2 seconds each
            "scores": t_profile.radar_values(),
        })

    session["sim_result"] = {
        "roi_means": sim_result["roi_means"],
        "top_regions": sim_result["top_regions"],
        "n_timesteps": sim_result["n_timesteps"],
    }
    session["profile"] = profile
    session["heatmap_b64"] = heatmap_b64
    sessions[session_id] = session

    return {
        "session_id": session_id,
        "emotional_profile": profile.to_dict(),
        "radar": profile.radar_values(),
        "heatmap_base64": heatmap_b64,
        "n_timesteps": sim_result["n_timesteps"],
        "top_regions": sim_result["top_regions"][:10],
        "timeline": timeline,
        "temporal_heatmaps": sim_result.get("temporal_heatmaps", []),
    }


# ---------------------------------------------------------------------------
# Phase 3: LLM interpretation + suggestions
# ---------------------------------------------------------------------------

@app.post("/api/interpret/{session_id}")
async def run_interpretation(session_id: str):
    """Get LLM interpretation of brain simulation results."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    profile = session.get("profile")
    if not profile:
        raise HTTPException(400, "Run simulation first")

    content_path = Path(session["path"])
    content_type = session.get("content_type", "")

    # Try to get a visual for the LLM to see alongside the brain data
    img_b64 = None
    if content_type == "image":
        with open(content_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
    elif content_type == "video":
        img_b64 = _extract_video_thumbnail(content_path)

    if img_b64:
        result = interpreter.interpret_with_image(
            profile=profile,
            image_base64=img_b64,
            platform=session.get("platform", "instagram"),
        )
    else:
        description = session.get("caption", "")
        result = interpreter.interpret(
            profile=profile,
            content_description=description,
            platform=session.get("platform", "instagram"),
        )

    session["interpretation"] = result
    sessions[session_id] = session  # persist to disk

    return result.to_dict()


@app.get("/api/interpret/{session_id}/stream")
async def stream_interpretation(session_id: str):
    """Stream LLM interpretation in real-time (SSE)."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    profile = session.get("profile")
    if not profile:
        raise HTTPException(400, "Run simulation first")

    stream = interpreter.stream_interpretation(
        profile=profile,
        content_description=session.get("caption", ""),
        platform=session.get("platform", "instagram"),
    )

    async def event_generator():
        for event in stream:
            if event.type == "response.output_text.delta":
                yield f"data: {json.dumps({'type': 'delta', 'text': event.delta})}\n\n"
            elif event.type == "response.completed":
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Phase 4: Multimodal polishing
# ---------------------------------------------------------------------------

@app.post("/api/polish")
async def run_polishing(req: PolishRequest):
    """Apply user-approved suggestions via multimodal polishing models."""
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    interp = session.get("interpretation")
    if not interp:
        raise HTTPException(400, "Run interpretation first")

    approved = [
        s for s in interp.suggestions
        if s.id in req.approved_suggestion_ids
    ]

    if not approved:
        raise HTTPException(400, "No valid suggestions selected")

    content_path = Path(session["path"])

    result = polisher.polish(
        suggestions=approved,
        content_path=content_path,
        original_caption=req.caption or session.get("caption", ""),
        platform=req.platform,
    )

    polished_image_b64 = None
    polished_path = None
    if result.polished_image:
        polished_image_b64 = base64.b64encode(result.polished_image).decode()
        polished_path = content_path.parent / f"polished_{content_path.name}"
        polished_path.write_bytes(result.polished_image)
        session["polished_path"] = str(polished_path)

    session["polish_result"] = result
    sessions[req.session_id] = session

    return {
        "session_id": req.session_id,
        "polished_image_base64": polished_image_b64,
        "polished_caption": result.polished_caption,
        "applied_suggestions": result.applied_suggestions,
        "errors": result.errors,
    }


# ---------------------------------------------------------------------------
# Phase 5: Verification re-simulation
# ---------------------------------------------------------------------------

@app.post("/api/compare/{session_id}")
async def run_comparison(session_id: str):
    """Re-simulate the polished content and compare with original."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    polish_result = session.get("polish_result")
    if not polish_result:
        raise HTTPException(400, "Run polishing first")

    polished_path = session.get("polished_path")
    original_profile = session.get("profile")
    original_radar = original_profile.radar_values() if original_profile else {}

    if polished_path:
        prepared = content_processor.prepare_for_tribe(Path(polished_path))
        new_sim = brain_engine.simulate(str(prepared))
        new_profile = compute_emotional_profile(
            roi_means=new_sim["roi_means"],
            top_regions=new_sim["top_regions"],
        )
        new_heatmap = brain_engine.generate_heatmap(new_sim.get("predictions"))
        new_heatmap_b64 = base64.b64encode(new_heatmap).decode()
        new_radar = new_profile.radar_values()
    else:
        new_radar = original_radar
        new_heatmap_b64 = session.get("heatmap_b64", "")

    deltas = {}
    for dim in new_radar:
        orig = original_radar.get(dim, 0)
        curr = new_radar[dim]
        deltas[dim] = {
            "before": round(orig, 3),
            "after": round(curr, 3),
            "delta": round(curr - orig, 3),
            "percent_change": round((curr - orig) / max(orig, 0.001) * 100, 1),
        }

    return {
        "session_id": session_id,
        "original_radar": original_radar,
        "polished_radar": new_radar,
        "deltas": deltas,
        "original_heatmap_base64": session.get("heatmap_b64", ""),
        "polished_heatmap_base64": new_heatmap_b64,
    }


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    return {
        "session_id": session_id,
        "content_type": session.get("content_type"),
        "platform": session.get("platform"),
        "has_simulation": "profile" in session,
        "has_interpretation": "interpretation" in session,
        "has_polished": "polish_result" in session,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "feedyourbrain"}
