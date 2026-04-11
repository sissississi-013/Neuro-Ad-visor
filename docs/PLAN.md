# FeedYourBrain -- Project Plan, Learnings & Progress Log

> A neuro-powered content intelligence agent for the Perplexity Hackathon.
> Simulates human brain reactions to social media content, interprets the
> emotional response, and helps creators optimize their content with a
> human-in-the-loop feedback pipeline.

---

## Table of Contents

1. [The Problem](#the-problem)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Progress Log](#progress-log)
5. [TRIBE v2 Deep Dive](#tribe-v2-deep-dive)
6. [Perplexity Agent API Deep Dive](#perplexity-agent-api-deep-dive)
7. [Neuroscience: Brain Region to Emotion Mapping](#neuroscience-brain-region-to-emotion-mapping)
8. [Modal GPU Deployment](#modal-gpu-deployment)
9. [Infrastructure Decisions](#infrastructure-decisions)
10. [Project Structure](#project-structure)
11. [Related Work & Competitors](#related-work--competitors)
12. [Differentiators](#differentiators)
13. [Demo Script](#demo-script)
14. [Open Questions & Next Steps](#open-questions--next-steps)

---

## The Problem

Social media marketers and content creators have no way to predict how their
content will emotionally land before publishing. Traditional A/B testing is
slow and expensive. Neuromarketing labs cost $50K+ per study. Existing
"sentiment analysis" tools only analyze text -- they miss the visceral,
subconscious brain response to visual and auditory stimuli.

## Architecture

### The Human-in-the-Loop Brain Feedback Pipeline

```
Phase 1: BRAIN SIMULATION
  User uploads content
    --> Content Processor (format detection, image-to-video conversion)
    --> TRIBE v2 on Modal A100 GPU
    --> ROI Emotion Analyzer (HCP MMP1.0 parcellation)

Phase 2: LLM INTERPRETATION
  Emotional profile + cortical heatmap + original image
    --> Perplexity Agent API (with web_search for neuroscience grounding)
    --> Plain-English emotional breakdown
    --> Ranked, actionable suggestion cards (structured JSON output)

Phase 3: HUMAN DECISION
  User sees brain heatmap, emotion radar chart, suggestion cards
    --> Toggles on/off which suggestions to apply
    --> AI advises, human decides (creative control preserved)

Phase 4: MULTIMODAL POLISHING
  User-approved suggestions dispatched to specialized models:
    --> Image: OpenAI gpt-image-1 (DALL-E) for visual modifications
    --> Text: OpenAI gpt-4o for caption/copy rewrites
    --> Audio: stretch goal

Phase 5: VERIFICATION
  Polished content re-run through TRIBE v2
    --> Side-by-side brain heatmaps
    --> Radar chart overlay (before vs. after)
    --> Per-dimension delta scores with percent changes
```

KEY DESIGN PRINCIPLE: The agent does NOT auto-regenerate. It interprets,
explains, and suggests. The human decides. Then specialized models polish.
Then brain sim verifies.

### Hackathon Tracks

- **Track A**: Best Agent-Powered Application (Perplexity Agent API) -- primary
- **Track B**: Best Computer-Powered Product (Perplexity Computer)
- **Track C**: Most Creative Computer Workflow (Perplexity Computer)

Architecture is modular -- not confined to one track. Perplexity Computer
does NOT have a public developer API (it's consumer-only for Max subscribers),
so Track A with the Agent API is the strongest programmatic fit.

---

## Tech Stack

| Layer              | Technology                                           | Status    |
|--------------------|------------------------------------------------------|-----------|
| Orchestrator       | Perplexity Agent API (Python SDK `perplexityai`)     | Built     |
| Brain Simulation   | Meta TRIBE v2 (`facebook/tribev2`) on Modal A100     | Deployed  |
| ROI Analysis       | TRIBE v2 HCP MMP1.0 parcellation utilities           | Built     |
| Image Generation   | OpenAI API (`gpt-image-1`)                           | Built     |
| Text Polishing     | OpenAI API (`gpt-4o`)                                | Built     |
| Backend            | FastAPI (Python)                                     | Built     |
| Frontend           | Next.js + React + Tailwind + Framer Motion           | Built     |
| GPU Infrastructure | Modal (serverless A100, scale-to-zero)               | Deployed  |
| Brain Visualization| TRIBE v2 `PlotBrainNilearn` (server-side render)     | Built     |

---

## Progress Log

### Session 1 (current)

**Research phase:**
- Researched Meta TRIBE v2 architecture, API, code, model weights, HuggingFace
- Researched Perplexity Agent API: read full quickstart, tools (web_search,
  fetch_url, function calling), models, presets, output control (streaming +
  structured JSON), image attachments
- Researched neuroscience of emotion: HCP MMP1.0 parcellation, brain regions
  associated with fear, disgust, reward, social cognition, etc.
- Researched competitors: BrainSuite AI, MindPilot, Open Brain, Social Neuron
- Researched hackathon tracks and Perplexity Computer (no developer API)

**Design phase:**
- Designed 5-phase pipeline with human-in-the-loop decision point
- Mapped 9 emotion dimensions to HCP brain ROIs
- Designed Perplexity Agent as interpreter (not executor)
- Chose structured JSON output for clean suggestion parsing

**Build phase:**
- Built full backend: 7 Python modules + FastAPI app
  - `emotion_mapping.py` -- 9-axis emotional profile from HCP ROIs
  - `brain_engine.py` -- TRIBE v2 wrapper with 3 execution modes
  - `content_processor.py` -- media download (yt-dlp), image-to-video
  - `interpreter.py` -- Perplexity Agent with structured output + streaming
  - `polisher.py` -- orchestrator dispatching to image/text models
  - `models/image_polisher.py` -- OpenAI gpt-image-1 integration
  - `models/text_polisher.py` -- OpenAI gpt-4o caption rewriting
  - `app.py` -- FastAPI with 8 endpoints covering all 5 phases

- Built full frontend: Next.js with dark neurolab aesthetic
  - `UploadZone` -- drag-and-drop + URL paste + platform selector
  - `BrainViewer` -- cortical heatmap display
  - `EmotionRadar` -- recharts radar chart (9 dimensions)
  - `SuggestionCards` -- toggleable cards with type badges + rationale
  - `CompareView` -- side-by-side heatmaps + delta scores
  - Main page with 5-phase stepper navigation

- Deployed TRIBE v2 to Modal A100 GPU
  - Fixed: tribev2 not on PyPI (install from GitHub)
  - Fixed: Modal deprecated `container_idle_timeout` -> `scaledown_window`
  - Fixed: Modal deprecated `@modal.web_endpoint` -> `@modal.fastapi_endpoint`
  - Fixed: Modal now requires explicit `fastapi[standard]` in image
  - Endpoint live at: `https://sissiwang--feedyourbrain-tribe-simulate-endpoint.modal.run`

**Key decisions made:**
1. Modal for GPU (not local M2, not Colab) -- serverless, scale-to-zero, A100
2. OpenAI for polishing (not via Perplexity) -- direct control over image gen
3. Perplexity Agent for interpretation only -- uses web_search for grounding
4. Mock engine fallback for local dev without GPU
5. Human-in-the-loop is non-negotiable -- user always decides

---

## TRIBE v2 Deep Dive

### What it is
A deep multimodal brain encoding model that predicts fMRI brain responses to
naturalistic stimuli (video, audio, text). Acts as a "digital twin" of human
neural activity.

### Links
- Paper: https://ai.meta.com/blog/tribe-v2-brain-predictive-foundation-model/
- Code: https://github.com/facebookresearch/tribev2
- Model: https://huggingface.co/facebook/tribev2
- Demo: https://aidemos.atmeta.com/tribev2
- License: CC BY-NC-4.0

### Architecture
Three frozen foundation models as feature extractors:
- **Text**: LLaMA 3.2-3B (contextual embeddings, 1024-word context window)
- **Video**: V-JEPA2-Giant (~1B params, 64-frame segments spanning 4 seconds)
- **Audio**: Wav2Vec-BERT 2.0 (~600M params)

Unified Transformer with:
- Shared dimension D=384
- Subject-specific prediction block
- Temporal transformer for time-evolving data
- Predictions on fsaverage5 cortical mesh (~20,484 vertices)
- 5-second hemodynamic lag offset

### Training data
- 720 subjects
- 1,115 hours of fMRI scans
- 8 datasets (Algonauts2025, Lahner2024, Lebel2023, Wen2017, etc.)

### Key API patterns

```python
# Load model
from tribev2 import TribeModel
model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")

# Process content
events = model.get_events_dataframe(video_path="video.mp4")
# Also: audio_path="audio.wav" or text_path="story.txt"
# Text is auto-converted to speech via gTTS for brain prediction

# Predict
preds, segments = model.predict(events, verbose=True)
# preds shape: (n_timesteps, 20484) -- one row per TR (~2 seconds)

# ROI analysis (built-in HCP MMP1.0 parcellation)
from tribev2.utils import summarize_by_roi, get_topk_rois, get_hcp_roi_indices
roi_means = summarize_by_roi(preds.mean(axis=0), hemi="both", mesh="fsaverage5")
top_rois = get_topk_rois(preds.mean(axis=0), hemi="both", k=20)

# Visualization
from tribev2.plotting.cortical import PlotBrainNilearn
plotter = PlotBrainNilearn(mesh="fsaverage5", inflate="half", bg_map="sulcal")
plotter.plot_surf(brain_data, views=["left", "right"], cmap="hot")
plotter.plot_timesteps_mp4(preds, filepath="brain.mp4", segments=segments)
```

### Dependencies (from pyproject.toml)
```
requires-python = ">=3.11"
torch>=2.5.1,<2.7
torchvision>=0.20,<0.22
numpy==2.2.6
x_transformers==1.27.20
neuralset==0.0.2
neuraltrain==0.0.2
huggingface_hub, transformers, moviepy>=2.2.1
spacy, julius, soundfile, gtts, langdetect, Levenshtein, einops, pyyaml
```

NOT on PyPI. Must install from GitHub:
```
pip install tribev2[plotting] @ git+https://github.com/facebookresearch/tribev2.git
```

### Computational requirements
- **Total model weights**: ~20-25GB in fp32 (V-JEPA2 ~4GB, LLaMA 3.2 ~12GB, Wav2Vec ~2.4GB, encoder)
- **Minimum GPU**: A100 40GB recommended (all three encoders loaded simultaneously)
- **Inference time**: ~30-60 seconds per video clip on A100
- **Our M2 Mac (16GB RAM)**: NOT enough to run all encoders -- hence Modal

---

## Perplexity Agent API Deep Dive

### Basics
- SDK: `pip install perplexityai`
- Client: `from perplexity import Perplexity`
- Auth: `PERPLEXITY_API_KEY` env var (auto-read)
- Endpoint: `POST https://api.perplexity.ai/v1/agent`
- OpenAI SDK compatible: change base_url to `https://api.perplexity.ai/v1`

### Available models (through Perplexity, with transparent pricing)
| Model | Input/1M | Output/1M |
|-------|----------|-----------|
| `perplexity/sonar` | $0.25 | $2.50 |
| `openai/gpt-5.4` | $2.50 | $15.00 |
| `openai/gpt-5-mini` | $0.25 | $2.00 |
| `anthropic/claude-sonnet-4-6` | $3.00 | $15.00 |
| `google/gemini-3-flash-preview` | $0.50 | $3.00 |
| `xai/grok-4-1-fast-non-reasoning` | $0.20 | $0.50 |

### Presets
- `fast-search` -- quick web-grounded answers
- `pro-search` -- multi-step research with auto web_search + fetch_url
- `deep-research` -- thorough multi-source research
- `advanced-deep-research` -- most comprehensive

### Tools

**Built-in:**
- `web_search` ($0.005/call) -- domain filtering, recency filtering, date ranges
- `fetch_url` ($0.0005/call) -- full page content extraction

**Custom function calling (multi-turn):**
1. Define functions in `tools` array with JSON Schema parameters
2. Agent returns `function_call` items (type, name, call_id, arguments as JSON string)
3. Execute function locally, return `function_call_output` with matching call_id
4. Send both back to agent for final response

### Image attachments
The agent can SEE images alongside text:
```python
input=[{
    "role": "user",
    "content": [
        {"type": "input_text", "text": "Analyze this..."},
        {"type": "input_image", "image_url": "data:image/png;base64,..."}
    ]
}]
```
Supported: PNG, JPEG, WEBP, GIF. Up to 50MB. Priced by pixel: (w*h)/750 tokens.

### Structured outputs
Force JSON Schema output with `response_format`:
```python
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "schema_name",
        "schema": { ... }  # valid JSON Schema
    }
}
```
First request with new schema may have 10-30s delay for preparation.
Links in JSON responses may hallucinate -- use `search_results` citations instead.

### Streaming
```python
stream = client.responses.create(..., stream=True)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="")
    elif event.type == "response.completed":
        print(event.response.usage)
```

### How we use it
- Model: `openai/gpt-5.4` (best reasoning + tool use)
- Tools: `web_search` (domain-filtered to .edu, nature.com, ncbi.nlm.nih.gov)
- Output: structured JSON with `brain_analysis` schema (summary, dominant_emotion,
  concern_level, suggestions array)
- Image attachment: when content is an image, we send it to the agent so it can
  see the visual alongside the brain data
- Streaming: available for real-time UI updates (SSE endpoint)

---

## Neuroscience: Brain Region to Emotion Mapping

### Source: HCP MMP1.0 Parcellation
180 cortical areas per hemisphere (360 total). Built into TRIBE v2's ROI analysis
utilities. Based on multi-modal MRI data from 210 healthy adults.

### Our 9-Axis Emotional Profile

| # | Dimension | Brain Regions (HCP ROIs) | Interpretation |
|---|-----------|--------------------------|----------------|
| 1 | Fear | AVI, AAIC, FOP1-5, MI, PoI1-2, Ig | Visceral fear, threat detection |
| 2 | Disgust | AVI, AAIC, FOP1-3, PI, Ig | Visceral discomfort, rejection |
| 3 | Anxiety | p24, a24, p24pr, 33pr, a32pr, d32, p32, s32, SCEF | Tension, unease, inner conflict |
| 4 | Reward | OFC, pOFC, 10r, 10v, a10p, 10pp, 10d, 11l, 13l, 25 | Pleasure, desire, approach |
| 5 | Social Connection | STS, STSdp/da/vp/va, TPOJ1-3, TGd, TGv, TE1a | Social cognition, empathy |
| 6 | Empathy | TPOJ1-3, TGd, TGv, PFm, PGi, PGs | Perspective-taking, resonance |
| 7 | Visual Attention | V1-V4, V3A/B, V6/6A, V7, V8, MT, MST, FST, LO1-3, FFC, VVC, PIT, VMV1-3 | Visual capture, salience |
| 8 | Cognitive Load | 8C, 8Av, 8BL, 8Ad, p9-46v, a9-46v, 46, 9-46d, 9a, 9p, i6-8, s6-8 | Executive processing |
| 9 | Auditory Engagement | A1, A4, A5, MBelt, LBelt, PBelt, RI, TA2, STGa | Sound processing intensity |

### Scoring method
1. For each dimension, look up matching ROI activation values
2. Average the activations across all matched ROIs for that dimension
3. Min-max normalize across all 9 dimensions to get 0-1 scores
4. Format as radar chart + text summary for the LLM interpreter

### Key neuroscience references
- Fear: distributed across prefrontal, cingulate, insular cortex, thalamus, amygdala
  (Nature Communications 2021)
- Primary fear system: "central autonomic-interoceptive" / salience network (dACC + AIC)
- ~25 distinct emotion dimensions represented across cortex (NeuroImage 2020)
- Valence-arousal framework separates emotional responses in brain embedding space
- fMRI cortical predictions can be mapped to emotions via established ROI-function literature
- IMPORTANT: TRIBE v2 predicts cortical surface (not subcortical). Amygdala activation
  is inferred via adjacent temporal pole regions (TGd, TGv), not direct measurement.

---

## Modal GPU Deployment

### Why Modal
- Our machine: Apple M2, 16GB RAM -- not enough for TRIBE v2's ~20-25GB model weights
- TRIBE v2 needs Python >=3.11, <3.14 (our system has 3.14.0 -- too new)
- No CUDA GPU available locally
- Modal: serverless A100, scale-to-zero, per-second billing (~$2.50/hr A100)
- $30 free credits = thousands of simulations

### Deployment details
- File: `backend/modal_brain.py`
- App name: `feedyourbrain-tribe`
- Container: Debian Slim + Python 3.11 + PyTorch + tribev2 from GitHub + ffmpeg + spacy
- GPU: A100 (40GB)
- Scaledown window: 300s (keeps warm 5 min after last request)
- Persistent volume: `tribe-cache` for model weights across cold starts
- Endpoint: `https://sissiwang--feedyourbrain-tribe-simulate-endpoint.modal.run`

### Deployment issues encountered & fixed
1. `tribev2` is NOT on PyPI -- must install from GitHub:
   `pip install tribev2[plotting] @ git+https://github.com/facebookresearch/tribev2.git`
2. Modal renamed `container_idle_timeout` -> `scaledown_window`
3. Modal renamed `@modal.web_endpoint` -> `@modal.fastapi_endpoint`
4. Modal now requires explicit `fastapi[standard]` in the image (used to auto-install)

### How brain_engine.py routes to Modal
Three execution modes (auto-detected in priority order):
1. **Modal** -- if `MODAL_BRAIN_URL` env var is set, sends base64-encoded content
   to the Modal endpoint via HTTP POST
2. **Local tribev2** -- if the `tribev2` pip package is importable, runs locally
3. **Mock engine** -- generates plausible-looking random brain data for dev/demo

### Commands
```bash
modal deploy backend/modal_brain.py   # Deploy to production
modal serve backend/modal_brain.py    # Hot-reload dev server
modal run backend/modal_brain.py      # Run test entrypoint
```

---

## Infrastructure Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| GPU provider | Modal | Serverless, scale-to-zero, A100, $30 free credits |
| Brain sim location | Remote (Modal) | M2 16GB can't fit 20GB+ model weights |
| LLM for interpretation | Perplexity Agent API | Built-in web_search for neuroscience grounding |
| LLM model | `openai/gpt-5.4` via Perplexity | Best reasoning + tool use available |
| Image generation | OpenAI direct | `gpt-image-1` not available through Perplexity |
| Text polishing | OpenAI direct | `gpt-4o` for reliable, fast caption rewrites |
| Backend framework | FastAPI | Python-native (same language as TRIBE v2), async |
| Frontend framework | Next.js + React | Fast iteration, SSR, TypeScript |
| Frontend style | Dark neurolab (custom) | Distinctive, not generic -- cyan/magenta/emerald on black |
| State management | In-memory dict | Hackathon scope; swap for Redis in production |

---

## Project Structure

```
feedyourbrain/
  backend/
    app.py                    # FastAPI server -- 8 endpoints for 5 phases
    brain_engine.py           # TRIBE v2 wrapper (Modal / local / mock)
    emotion_mapping.py        # HCP ROI -> 9-axis emotional profile
    interpreter.py            # Perplexity Agent for LLM interpretation
    polisher.py               # Multimodal polishing orchestrator
    content_processor.py      # Media download (yt-dlp), format conversion
    modal_brain.py            # Modal serverless GPU deployment for TRIBE v2
    models/
      __init__.py
      image_polisher.py       # OpenAI gpt-image-1 integration
      text_polisher.py        # OpenAI gpt-4o caption/copy rewrites
      audio_polisher.py       # (stretch goal)
  frontend/
    app/
      layout.tsx              # Root layout (dark theme, custom fonts)
      globals.css             # Design system (cyan/magenta/emerald, noise, glow)
      page.tsx                # Main 5-phase pipeline UI with stepper
      components/
        UploadZone.tsx        # Drag-and-drop + URL paste + platform selector
        BrainViewer.tsx       # Cortical heatmap image display
        EmotionRadar.tsx      # Recharts radar chart (9 dimensions, overlay mode)
        SuggestionCards.tsx   # Toggleable cards with type badges + rationale
        CompareView.tsx       # Side-by-side heatmaps + delta score grid
    lib/
      api.ts                  # API client (upload, simulate, interpret, polish, compare)
  docs/
    PLAN.md                   # This file -- plan, learnings, progress
  .env                        # API keys (NEVER commit)
  .gitignore                  # Covers .env, __pycache__, node_modules, etc.
  requirements.txt            # Python dependencies
  README.md                   # Project overview for hackathon submission
```

### Backend API endpoints

| Method | Path | Phase | Description |
|--------|------|-------|-------------|
| POST | `/api/upload` | 1 | Upload file or provide URL |
| POST | `/api/simulate/{session_id}` | 2 | Run brain simulation |
| POST | `/api/interpret/{session_id}` | 3 | Get LLM interpretation + suggestions |
| GET | `/api/interpret/{session_id}/stream` | 3 | Stream interpretation (SSE) |
| POST | `/api/polish` | 4 | Apply approved suggestions |
| POST | `/api/compare/{session_id}` | 5 | Re-simulate and compare |
| GET | `/api/session/{session_id}` | * | Get session state |
| GET | `/health` | * | Health check |

---

## Related Work & Competitors

| Product | What it does | How we differ |
|---------|-------------|---------------|
| **BrainSuite AI** | Predicts social media ad performance using neuroscience AI (98.7% MIT accuracy) | We use the actual TRIBE v2 fMRI model, not a proprietary black box |
| **MindPilot** | Closed-loop EEG-guided image generation | We use fMRI predictions (higher spatial resolution), no hardware needed |
| **Open Brain (BrainVivo)** | fMRI-based emotion clustering, emotional transformation | We add content modification + re-verification loop |
| **Social Neuron** | Closed-loop content system with 35+ AI models | We ground everything in neuroscience (TRIBE v2), not just performance metrics |
| **Neuromarketing labs** | Physical fMRI/EEG studies on human subjects | We simulate in seconds for free, not $50K+ per study |

---

## Differentiators

1. **Ethical Content Guardian** -- not just marketing optimization; protects viewers
   from manipulative emotional triggers (fear-mongering, anxiety exploitation)
2. **Temporal Brain Journey** -- TRIBE v2 predicts per-TR (every 2 seconds), so we
   can show exactly WHEN in a video fear spikes or attention drops
3. **A/B Testing Without Humans** -- model trained on 720 subjects; simulate the
   average brain response instantly
4. **Platform-Specific Optimization** -- Perplexity web_search finds real-time best
   practices for Instagram, TikTok, Twitter, etc.
5. **Brain Diff** -- literal cortical difference maps between original and polished
6. **Grounded in Science** -- fMRI-trained model + cited neuroscience research, not vibes
7. **Human-in-the-Loop** -- user always controls what changes are made

---

## Demo Script (3 min)

1. **(0:00-0:20)** Intro: "What if you could see how your audience's brain reacts
   before you post?" Upload a dark, fear-inducing social media ad.
2. **(0:20-0:50)** Brain simulation runs on Modal A100. Cortical heatmap lights up
   in the insula and anterior cingulate. Radar chart shows fear/anxiety spiking.
3. **(0:50-1:20)** LLM interpretation streams in via Perplexity Agent: "This ad
   triggers strong fear and anxiety. The dark palette and isolated figure activate
   threat detection. Reward circuits are under-stimulated." Suggestion cards appear.
4. **(1:20-1:40)** User toggles on 2 of 3 suggestions: "warm color palette" and
   "add social element." Leaves "brighten background" off -- their creative choice.
5. **(1:40-2:10)** Multimodal polishing: OpenAI regenerates the visual, rewrites the
   caption. Shows polished content appearing.
6. **(2:10-2:40)** Re-simulation: side-by-side brain heatmaps. Fear drops, reward
   rises. Radar chart overlay shows the shift. Delta cards: "Fear -40%, Reward +25%"
7. **(2:40-3:00)** Outro: "FeedYourBrain -- a digital brain focus group in 60 seconds.
   Powered by Meta TRIBE v2 and Perplexity Agent API."

---

## Environment Variables

```
PERPLEXITY_API_KEY=pplx-...
OPENAI_API_KEY=sk-...
BROWSERUSE_API_KEY=bu_...
MODAL_BRAIN_URL=https://sissiwang--feedyourbrain-tribe-simulate-endpoint.modal.run
```

Never commit `.env` to version control. It is in `.gitignore`.

---

## Open Questions & Next Steps

- [ ] Test the full end-to-end flow: upload -> Modal brain sim -> Perplexity interpret -> OpenAI polish -> re-sim
- [ ] First cold start on Modal may be slow (model download + load); test and optimize
- [ ] Consider Modal Volume pre-warming to cache model weights
- [ ] Video support: does TRIBE v2 handle arbitrary-length videos? May need chunking
- [ ] Audio polishing: what models/services to use? (stretch goal)
- [ ] Temporal brain journey visualization: timeline chart showing per-TR emotions
- [ ] Explore browseruse integration for Track B/C possibilities
- [ ] Prepare sample content for demo (find a genuinely fear-inducing ad)
- [ ] Record 3-minute demo video for hackathon submission
- [ ] Write detailed README.md with setup instructions for judges
