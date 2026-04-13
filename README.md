# Neuro-Advisor

**Predict how audiences emotionally react to your content before you post it.**

Neuro-Advisor is an AI neuromarketing tool that uses Meta's TRIBE v2 fMRI model (trained on 720 human subjects) to predict real brain activation patterns in response to video and image content. Upload a creative, get a full cortical activation map, watch the brain react in sync with your video, and receive AI-powered optimization suggestions grounded in neuroscience research.

Shoutout to Codeology & Perplexity for this amazing event!

> **[Watch the full demo video](readmemedia/demo.mp4)** (click to download and play)

---

## Upload Your Creative

Drop a video or image, select your target platform, and hit "Predict Audience Response." The content is sent to an A100 GPU running TRIBE v2 for brain simulation.

![Upload page with video preview and platform selector](readmemedia/upload.png)

---

## Cortical Activation Map

TRIBE v2 predicts brain activity across 20,484 cortical vertices on the fsaverage5 brain surface. The 4-view heatmap (left lateral, left medial, right medial, right lateral) shows the overall activation pattern. Below it, the Temporal Brain Journey chart tracks how 9 emotional dimensions change across each 2-second timestep of the video.

![4-view cortical heatmap and temporal brain journey chart](readmemedia/cortical%20activation.png)

---

## Temporal Brain Reaction: Video + Brain Side by Side

For video content, you can watch your creative play on the left while the brain's cortical response animates on the right. Shared play/pause/scrub controls keep both in sync. Scrub to any moment to see exactly which frame triggered which brain response.

![Side-by-side video and brain reaction with synced playback controls](readmemedia/frame%26video%20side%20by%20side.png)

---

## Emotional Profile and AI Interpretation

The 9-axis emotional radar chart maps brain regions to emotional dimensions (fear, anxiety, reward, visual attention, social connection, empathy, cognition, auditory engagement, disgust). The Perplexity Agent API uses web search grounded in neuroscience research to explain what the brain data means and identifies the dominant emotional response.

![Emotional radar chart and AI interpretation panel](readmemedia/emotionalmap%26agent%20interpreter.png)

---

## AI Optimization Suggestions

The AI generates specific, actionable suggestions organized by type: image modifications, text/caption rewrites, layout changes, and audio improvements. Each suggestion includes its target emotion, estimated impact percentage, and neuroscience rationale. Toggle the ones you want to apply.

![Optimization suggestion cards with toggles, impact scores, and target emotions](readmemedia/ai%20suggestions.png)

---

## Modal GPU Dashboard

TRIBE v2 runs on Modal's serverless A100 GPUs. The dashboard shows function call history, execution times, and container status. The system scales to zero when idle, so you only pay for actual compute time.

![Modal dashboard showing function calls, execution times, and container status](readmemedia/modal%20run.png)

---

## How It Works

Neuro-Advisor runs a five-phase pipeline with the human in the loop at every decision point.

1. **Upload** your video, image, or social media URL with optional caption and platform selection.
2. **Neuro Scan** runs TRIBE v2 on an A100 GPU. For video, it generates per-timestep predictions every 2 seconds, producing both a static overall heatmap and animated temporal frames.
3. **Insights** from the Perplexity Agent API interpret the brain data using real-time web search of neuroscience literature. The AI explains what emotions are triggered, which brain regions drive them, and delivers ranked suggestions.
4. **Optimize** by selecting which AI suggestions to apply. OpenAI handles image regeneration (gpt-image-1) and caption rewriting (gpt-4o).
5. **Results** re-run the polished content through TRIBE v2 and show a before-and-after comparison with per-dimension performance uplift scores.

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
    +---> Per-timestep heatmaps (temporal animation frames)
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
| Brain Visualization | TRIBE v2 PlotBrainNilearn (nilearn cortical surface rendering) |

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
  readmemedia/             # Screenshots and demo video
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

- **Real neuroscience model**: TRIBE v2 is trained on actual fMRI data from 720 human subjects. This is not sentiment analysis. It predicts cortical activation at 20,484 vertices.
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
