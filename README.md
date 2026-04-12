# Neuro-Advisor

**Predict how audiences emotionally react to your content before you post it.**

Neuro-Advisor is an AI neuromarketing intelligence tool for content creators and marketers. Upload a video or image and get a full cortical activation map showing how real human brains would respond — powered by Meta's TRIBE v2 fMRI model trained on 720 subjects. An AI interpreter explains what emotions are triggered and gives actionable optimization suggestions. Watch the brain's reaction change in real time with synced video playback.

Built for the Perplexity Hackathon 2026.

---

## How It Works

Neuro-Advisor runs a five-phase pipeline with the human in the loop at every decision point.

### Phase 1: Upload Your Creative

Upload a video (MP4, MOV, WebM) or image (PNG, JPG, WebP), or paste a social media URL. Add your caption and select the target platform. The content is sent to an A100 GPU running Meta's TRIBE v2 brain encoding model.

### Phase 2: Neuro Scan

TRIBE v2 predicts how the human brain responds across 20,484 cortical vertices on the fsaverage5 brain surface. For video content, predictions are generated at each 2-second timestep — capturing exactly how the brain's response evolves over time. The output includes:

- **Overall cortical activation map** — a 4-view heatmap showing the mean brain response
- **Temporal brain reaction** — a synced side-by-side view: your video on the left, the brain's response animating on the right, with play/pause/scrub controls
- **Emotional profile** — 9-axis radar chart mapping brain regions to emotions
- **Temporal brain journey** — per-timestep emotion chart with a synced playhead

### Phase 3: AI Insights

The Perplexity Agent API receives the brain activation data alongside a visual of the content. It uses real-time web search grounded in neuroscience research to explain what emotions are triggered, which brain regions drive them, and delivers ranked, actionable suggestions for improvement.

### Phase 4: Optimize

Suggestions are presented as toggleable cards with target emotion, estimated impact, and neuroscience rationale. The user decides which to apply. Selected suggestions are dispatched to specialized models: OpenAI for image regeneration and caption rewriting.

### Phase 5: Results

The polished content is re-run through TRIBE v2 for a second brain simulation. A side-by-side comparison shows the before-and-after brain activation maps, emotional profile overlay, and per-dimension performance uplift scores.

---

## Architecture

```
User uploads video/image
    |
    v
Content Processor (format detection, image-to-video conversion)
    |
    v
TRIBE v2 on Modal A100 GPU (20,484 cortical vertex predictions per timestep)
    |
    +---> Mean heatmap (4-view cortical surface render)
    +---> Per-timestep heatmaps (2x2 grid frames for temporal animation)
    +---> Per-timestep ROI profiles (180 regions x N timesteps)
    |
    v
ROI Emotion Analyzer (HCP MMP1.0 parcellation, 9-axis emotional profile)
    |
    v
Perplexity Agent API (web_search for neuroscience grounding, structured JSON)
    |
    v
User reviews and selects suggestions (human-in-the-loop)
    |
    v
OpenAI image generation + text rewriting (multimodal polishing)
    |
    v
TRIBE v2 re-simulation (before/after performance uplift)
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Brain Simulation | Meta TRIBE v2 (facebook/tribev2) on Modal A100 GPU |
| AI Interpretation | Perplexity Agent API with web_search and structured output |
| Image Polishing | OpenAI gpt-image-1 |
| Text Polishing | OpenAI gpt-4o |
| Backend | FastAPI (Python) |
| Frontend | Next.js, React, Tailwind CSS, Framer Motion, Recharts |
| GPU Infrastructure | Modal (serverless A100, scale-to-zero billing) |
| Brain Visualization | TRIBE v2 PlotBrainNilearn + PIL (nilearn cortical surface rendering, 2x2 grid composition) |

---

## Emotional Profile: 9-Axis Brain Mapping

TRIBE v2 predictions are mapped to emotional dimensions using the HCP MMP1.0 brain parcellation (180 cortical regions per hemisphere):

| Dimension | Brain Regions | What It Means |
|-----------|---------------|---------------|
| Fear | Anterior Insula, Frontal Opercular areas | Threat detection, fight-or-flight |
| Disgust | Anterior Insula, Posterior Insula | Visceral rejection |
| Anxiety | Anterior Cingulate (p24, a24, d32) | Cognitive conflict, unease |
| Reward | Orbitofrontal Cortex, vmPFC | Pleasure, desire, approach motivation |
| Social Connection | Superior Temporal Sulcus, Temporo-Parietal Junction | Empathy, social cognition |
| Empathy | TPJ, Temporal Pole, Parietal areas | Perspective-taking |
| Visual Attention | V1-V4, MT, Fusiform, Ventral Visual areas | Visual salience, attention capture |
| Cognitive Load | Dorsolateral Prefrontal Cortex (8C, 8Av, 46) | Deliberation, executive processing |
| Auditory Engagement | A1, A4, A5, Belt areas | Sound processing intensity |

---

## Project Structure

```
feedyourbrain/
  backend/
    app.py                 # FastAPI server (5 pipeline phases)
    brain_engine.py        # TRIBE v2 wrapper (Modal GPU / local / mock, retry logic)
    emotion_mapping.py     # HCP ROI to 9-axis emotional profile mapping
    interpreter.py         # Perplexity Agent API integration
    polisher.py            # Multimodal polishing orchestrator
    content_processor.py   # Media download, format conversion
    modal_brain.py         # Modal serverless GPU deployment for TRIBE v2
    models/
      image_polisher.py    # OpenAI image generation
      text_polisher.py     # OpenAI caption rewriting
  frontend/
    app/
      page.tsx             # Main 5-phase pipeline UI
      components/
        UploadZone.tsx     # Drag-and-drop upload with platform selector
        BrainViewer.tsx    # Full-width cortical heatmap display
        SyncedBrainView.tsx # Side-by-side video + brain reaction player
        BrainTimeline.tsx  # Temporal emotion chart with synced playhead
        EmotionRadar.tsx   # 9-axis radar chart
        SuggestionCards.tsx # Toggleable suggestion cards
        CompareView.tsx    # Before/after brain diff with uplift scores
    lib/
      api.ts               # API client
  docs/
    PLAN.md                # Detailed plan, research, and progress log
  .env                     # API keys (not committed)
  requirements.txt
  README.md
```

---

## Setup

### Prerequisites

- Python 3.11 or 3.12
- Node.js 18+
- A Modal account (free tier includes $30 GPU credits)
- API keys for Perplexity and OpenAI

### 1. Clone and configure

```bash
git clone https://github.com/sissississi-013/Neuro-Ad-visor.git
cd Neuro-Ad-visor
```

Create a `.env` file in the project root:

```
PERPLEXITY_API_KEY=your_perplexity_key
OPENAI_API_KEY=your_openai_key
MODAL_BRAIN_URL=https://your-modal-endpoint.modal.run
```

### 2. Deploy TRIBE v2 to Modal

```bash
pip install modal
modal setup
modal deploy backend/modal_brain.py
```

Copy the endpoint URL from the deploy output into your `.env` as `MODAL_BRAIN_URL`.

### 3. Start the backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

---

## How Perplexity Agent API Is Used

The Perplexity Agent API serves as the interpretation layer between raw brain simulation data and human-understandable insights:

1. **Model access**: Uses `openai/gpt-5.4` through Perplexity's multi-provider Agent API for high-quality reasoning about neuroscience data.

2. **Web search grounding**: The agent uses `web_search` filtered to neuroscience domains (nature.com, ncbi.nlm.nih.gov, .edu sites) to back its interpretations with real research.

3. **Image attachments**: Content is attached directly so the agent can see what the viewer sees alongside the brain activation data. For video, a representative frame is extracted.

4. **Structured output**: Returns JSON conforming to a strict schema with summary, dominant emotion, concern level, and suggestion objects (title, description, target emotion, estimated impact, rationale, modification type).

5. **Streaming**: An SSE endpoint streams the interpretation in real time.

---

## Key Differentiators

- **Real neuroscience model**: TRIBE v2 is trained on actual fMRI data from 720 human subjects. This is not sentiment analysis — it predicts cortical activation at 20,484 vertices.

- **Temporal brain reaction viewer**: For video content, watch the brain's response animate in sync with your video. Scrub to any moment and see exactly which frame triggered which brain reaction.

- **Human-in-the-loop**: The AI interprets and suggests, but the user always decides what changes to make. Creative control is preserved.

- **Grounded in research**: Every interpretation is backed by real-time web search of neuroscience literature via the Perplexity Agent API.

- **Performance uplift verification**: After optimization, the content is re-scanned through TRIBE v2 for a measurable before-and-after comparison.

---

## References

- [Meta TRIBE v2](https://ai.meta.com/blog/tribe-v2-brain-predictive-foundation-model/) - A Predictive Foundation Model Trained to Understand How the Human Brain Processes Complex Stimuli
- [TRIBE v2 Code](https://github.com/facebookresearch/tribev2) - Open source under CC BY-NC-4.0
- [TRIBE v2 Model Weights](https://huggingface.co/facebook/tribev2) - Available on HuggingFace
- [Perplexity Agent API](https://docs.perplexity.ai/docs/agent-api/quickstart) - Multi-provider LLM API with integrated web search
- [HCP MMP1.0 Parcellation](https://www.nature.com/articles/nature18933) - A multi-modal parcellation of human cerebral cortex

---

## License

MIT
