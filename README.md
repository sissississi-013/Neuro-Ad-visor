# FeedYourBrain

**Simulate how the human brain reacts to your social media content before you post it.**

FeedYourBrain is a neuro-powered content intelligence tool that uses Meta's TRIBE v2 brain encoding model to predict fMRI-level brain activation patterns in response to video and image content. An AI interpreter (powered by the Perplexity Agent API) then explains what emotions the content triggers, why, and how to improve it. The user stays in control: they review suggestions, choose which to apply, and specialized models polish the content accordingly.

Built for the Perplexity Hackathon 2026.

---

## How It Works

FeedYourBrain follows a five-phase pipeline with the human in the loop at every step.

### Phase 1: Upload

Upload a video (MP4, MOV, WebM) or image (PNG, JPG, WebP). You can also paste a social media URL. The content is sent to an A100 GPU running Meta's TRIBE v2 model.

### Phase 2: Brain Simulation

TRIBE v2 predicts how the human brain responds to your content across 20,484 cortical vertices on the fsaverage5 brain surface. The model was trained on 720 subjects and 1,115 hours of fMRI data. For video content, predictions are generated every 2 seconds, capturing how the brain's response changes over time.

### Phase 3: AI Interpretation

The Perplexity Agent API receives the brain activation data alongside a visual of the content. It uses real-time web search to ground its analysis in neuroscience research and platform-specific best practices. The output is a plain-English explanation of what emotions are triggered, which brain regions drive them, and a ranked list of specific, actionable suggestions for improvement.

### Phase 4: Human Decision

Suggestions are presented as toggleable cards. Each card includes the modification, which emotion it targets, its estimated impact, and the neuroscience rationale. The user decides which suggestions to apply. The AI advises; the human decides.

### Phase 5: Multimodal Polishing and Verification

Selected suggestions are dispatched to specialized models: OpenAI for image regeneration and caption rewriting. The polished content is then re-run through TRIBE v2 for a second brain simulation. A side-by-side comparison shows the before-and-after brain activation maps, emotional profile overlay, and per-dimension delta scores.

---

## Architecture

```
User uploads video/image
    |
    v
Content Processor (format detection, image-to-video conversion)
    |
    v
TRIBE v2 on Modal A100 GPU (20,484 cortical vertex predictions)
    |
    v
ROI Emotion Analyzer (HCP MMP1.0 parcellation, 9-axis emotional profile)
    |
    v
Perplexity Agent API (web_search for neuroscience grounding, structured JSON suggestions)
    |
    v
User reviews and selects suggestions (human-in-the-loop)
    |
    v
OpenAI image generation + text rewriting (multimodal polishing)
    |
    v
TRIBE v2 re-simulation (before/after brain diff)
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

TRIBE v2 predictions are mapped to emotional dimensions using the HCP MMP1.0 brain parcellation (180 cortical regions per hemisphere). Each dimension corresponds to a well-characterized set of brain regions:

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
    app.py                 # FastAPI server (8 endpoints, 5 pipeline phases)
    brain_engine.py        # TRIBE v2 wrapper (Modal GPU / local / mock modes)
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
        UploadZone.tsx     # Drag-and-drop upload with video preview
        BrainViewer.tsx    # Full-width cortical heatmap display
        BrainTimeline.tsx  # Temporal brain journey (per-2s emotion chart)
        EmotionRadar.tsx   # 9-axis radar chart
        SuggestionCards.tsx # Toggleable suggestion cards
        CompareView.tsx    # Before/after brain diff with delta scores
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
git clone https://github.com/sissississi-013/feed_your_brain.git
cd feed_your_brain
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

Open http://localhost:3000 in your browser.

---

## How Perplexity Agent API Is Used

The Perplexity Agent API serves as the interpretation layer between raw brain simulation data and human-understandable insights. Specifically:

1. **Model access**: We use `openai/gpt-5.4` through Perplexity's multi-provider Agent API for high-quality reasoning about neuroscience data.

2. **Web search grounding**: The agent uses `web_search` (filtered to neuroscience domains like nature.com, ncbi.nlm.nih.gov, and .edu sites) to back its interpretations with real research. Every recommendation references actual brain region functions documented in the literature.

3. **Image attachments**: When analyzing images, the content is attached directly to the agent so it can see what the viewer sees alongside the brain activation data. For video, a representative frame is extracted and attached.

4. **Structured output**: The agent returns JSON conforming to a strict schema (`brain_analysis`) with fields for summary, dominant emotion, concern level, and an array of suggestion objects (each with title, description, target emotion, estimated impact, rationale, and modification type). This enables clean parsing and direct rendering as UI cards.

5. **Streaming**: An SSE endpoint streams the interpretation in real time for responsive UI updates.

---

## Key Differentiators

- **Real neuroscience model**: TRIBE v2 is trained on actual fMRI data from 720 human subjects. This is not sentiment analysis or keyword matching. It predicts cortical activation patterns at 20,484 vertices.

- **Temporal brain journey**: For video content, the system shows how brain activation changes every 2 seconds. You can see exactly when fear spikes, when attention drops, when reward peaks.

- **Human-in-the-loop**: The AI interprets and suggests, but the user always decides what changes to make. Creative control is preserved.

- **Grounded in research**: Every interpretation is backed by real-time web search of neuroscience literature via the Perplexity Agent API. Not vibes. Science.

- **Ethical content guardian**: Beyond marketing optimization, this tool can identify and help remove manipulative emotional triggers like fear-mongering in news thumbnails or anxiety exploitation in ads.

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
