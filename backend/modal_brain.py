"""
Modal serverless GPU deployment for TRIBE v2 brain simulation.

Deploys TRIBE v2 on an A100 GPU via Modal, exposes it as an HTTP endpoint.
Scales to zero when not in use -- you only pay per-second of actual inference.

Deploy:  modal deploy backend/modal_brain.py
Test:    modal run backend/modal_brain.py
Serve:   modal serve backend/modal_brain.py  (hot-reload for dev)
"""

import modal

# ---------------------------------------------------------------------------
# Modal app + image setup
# ---------------------------------------------------------------------------

app = modal.App("feedyourbrain-tribe")

tribe_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg")
    .env({"HF_HOME": "/cache/huggingface"})
    .pip_install(
        "torch>=2.5.1,<2.7",
        "torchvision>=0.20,<0.22",
        "numpy==2.2.6",
        "huggingface_hub",
        "transformers",
        "moviepy>=2.2.1",
        "gtts",
        "langdetect",
        "spacy",
        "soundfile",
        "julius",
        "Levenshtein",
        "einops",
        "pyyaml",
        "x_transformers==1.27.20",
        "nibabel",
        "matplotlib",
        "nilearn",
        "scipy",
        "Pillow",
    )
    .pip_install("tribev2[plotting] @ git+https://github.com/facebookresearch/tribev2.git")
    .pip_install("fastapi[standard]")
    .run_commands("python -m spacy download en_core_web_sm")
)

# Persistent volume for caching model weights across cold starts
cache_vol = modal.Volume.from_name("tribe-cache", create_if_missing=True)

CACHE_DIR = "/cache"


# ---------------------------------------------------------------------------
# Model class -- loaded once, reused across requests
# ---------------------------------------------------------------------------

@app.cls(
    image=tribe_image,
    gpu="A100",
    timeout=900,
    scaledown_window=300,
    volumes={CACHE_DIR: cache_vol},
)
class BrainSimulator:
    @modal.enter()
    def load_model(self):
        """Load TRIBE v2 model once when the container starts."""
        from tribev2 import TribeModel

        print("Loading TRIBE v2 model...")
        self.model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=CACHE_DIR,
            device="cuda",
        )
        print("TRIBE v2 loaded on GPU.")

        # Pre-import ROI utilities
        from tribev2.utils import get_hcp_labels, get_topk_rois, summarize_by_roi
        self.summarize_by_roi = summarize_by_roi
        self.get_topk_rois = get_topk_rois
        self.get_hcp_labels = get_hcp_labels

    @modal.method()
    def simulate(self, content_bytes: bytes, filename: str) -> dict:
        """Run brain simulation on content bytes.

        Args:
            content_bytes: raw file bytes (video, image, or audio)
            filename: original filename (used to determine type)

        Returns:
            dict with roi_means, top_regions, n_timesteps, predictions_stats
        """
        import subprocess
        import tempfile
        import numpy as np
        from pathlib import Path

        suffix = Path(filename).suffix.lower() or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(content_bytes)
            temp_path = f.name

        IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
        AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg"}

        if suffix in IMAGE_EXTS:
            video_path = temp_path.replace(suffix, ".mp4")
            print(f"Converting image {suffix} to video for TRIBE v2...")
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", temp_path,
                "-c:v", "libx264", "-t", "3",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                video_path,
            ], check=True, capture_output=True, timeout=60)
            temp_path = video_path
            print("Image converted to 3-second video.")

        print(f"Running simulation on {filename} ({len(content_bytes)} bytes)...")

        if suffix in AUDIO_EXTS:
            events = self.model.get_events_dataframe(audio_path=temp_path)
        else:
            events = self.model.get_events_dataframe(video_path=temp_path)
        preds, segments = self.model.predict(events, verbose=True)

        mean_activation = preds.mean(axis=0)
        roi_means_arr = self.summarize_by_roi(mean_activation, hemi="both", mesh="fsaverage5")
        top_rois = self.get_topk_rois(mean_activation, hemi="both", mesh="fsaverage5", k=20)

        labels = self.get_hcp_labels(mesh="fsaverage5", combine=False, hemi="both")
        roi_means = dict(zip(labels, roi_means_arr.tolist()))

        import os
        os.unlink(temp_path)

        return {
            "roi_means": roi_means,
            "top_regions": top_rois,
            "n_timesteps": int(preds.shape[0]),
            "predictions_mean": preds.mean(axis=0).tolist(),
            "predictions_std": float(preds.std()),
            "predictions_shape": list(preds.shape),
        }

    @modal.method()
    def generate_heatmap(self, predictions_mean: list) -> bytes:
        """Generate a cortical heatmap PNG from mean predictions."""
        import io
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        mean_act = np.array(predictions_mean)

        try:
            from tribev2.plotting.cortical import PlotBrainNilearn

            plotter = PlotBrainNilearn(mesh="fsaverage5", inflate="half", bg_map="sulcal")
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
        except Exception as e:
            print(f"Nilearn plotting failed ({e}), using fallback")
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            half = len(mean_act) // 2
            for ax, data, title in [
                (axes[0], mean_act[:half], "Left Hemisphere"),
                (axes[1], mean_act[half:], "Right Hemisphere"),
            ]:
                n = int(np.sqrt(len(data)))
                ax.imshow(data[:n*n].reshape(n, n), cmap="hot", interpolation="bilinear")
                ax.set_title(title, fontsize=11)
                ax.axis("off")
            fig.suptitle("Cortical Activation", fontsize=13, fontweight="bold")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="#050508", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.read()


# ---------------------------------------------------------------------------
# Web endpoint -- runs directly on the GPU container with the model loaded
# ---------------------------------------------------------------------------

@app.function(
    image=tribe_image,
    gpu="A100",
    timeout=900,
    scaledown_window=300,
    volumes={CACHE_DIR: cache_vol},
)
@modal.fastapi_endpoint(method="POST")
def simulate_endpoint(data: dict):
    """HTTP endpoint for brain simulation.

    POST with JSON body:
      { "content_base64": "<base64-encoded file>", "filename": "post.mp4" }

    Returns JSON with roi_means, top_regions, heatmap_base64, etc.
    """
    import base64
    import io
    import subprocess
    import tempfile
    from pathlib import Path

    import numpy as np

    content_b64 = data.get("content_base64", "")
    filename = data.get("filename", "upload.mp4")
    content_bytes = base64.b64decode(content_b64)

    suffix = Path(filename).suffix.lower() or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content_bytes)
        temp_path = f.name

    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
    AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg"}

    if suffix in IMAGE_EXTS:
        video_path = temp_path.replace(suffix, ".mp4")
        print(f"Converting image {suffix} -> mp4 for TRIBE v2...")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", temp_path,
            "-c:v", "libx264", "-t", "3",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            video_path,
        ], check=True, capture_output=True, timeout=60)
        temp_path = video_path
        print("Converted.")

    # Load model (cached after first call via module-level)
    from tribev2 import TribeModel
    from tribev2.utils import get_hcp_labels, get_topk_rois, summarize_by_roi

    global _model
    if "_model" not in dir() or _model is None:
        print("Loading TRIBE v2 model...")
        _model = TribeModel.from_pretrained(
            "facebook/tribev2", cache_folder=CACHE_DIR, device="cuda",
        )
        print("TRIBE v2 loaded on GPU.")

    print(f"Running simulation on {filename} ({len(content_bytes)} bytes)...")

    if suffix in AUDIO_EXTS:
        events = _model.get_events_dataframe(audio_path=temp_path)
    else:
        events = _model.get_events_dataframe(video_path=temp_path)
    preds, segments = _model.predict(events, verbose=True)

    mean_activation = preds.mean(axis=0)
    roi_means_arr = summarize_by_roi(mean_activation, hemi="both", mesh="fsaverage5")
    labels = get_hcp_labels(mesh="fsaverage5", combine=False, hemi="both")
    roi_means = dict(zip(labels, roi_means_arr.tolist()))

    try:
        top_rois = get_topk_rois(mean_activation, hemi="both", mesh="fsaverage5", k=20)
    except (IndexError, ValueError):
        sorted_rois = sorted(roi_means.items(), key=lambda x: abs(x[1]), reverse=True)
        top_rois = [name for name, _ in sorted_rois[:20]]

    # Per-timestep ROI analysis for timeline
    print("Computing per-timestep ROI profiles...")
    temporal_roi_data = []
    for t in range(preds.shape[0]):
        t_roi_arr = summarize_by_roi(preds[t], hemi="both", mesh="fsaverage5")
        t_roi_dict = dict(zip(labels, t_roi_arr.tolist()))
        temporal_roi_data.append(t_roi_dict)

    # Generate hero heatmap: 4 views for full brain coverage
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("Rendering cortical heatmap...")
    view_mapping = ["left", "medial_left", "medial_right", "right"]

    try:
        from tribev2.plotting.cortical import PlotBrainNilearn
        plotter = PlotBrainNilearn(mesh="fsaverage5", inflate="half", bg_map="sulcal")

        fig, axes = plotter.get_fig_axes(views=view_mapping)
        plotter.plot_surf(
            mean_activation, axes=axes, views=view_mapping,
            cmap="hot", norm_percentile=95,
            colorbar=False,
        )
        fig.set_size_inches(16, 4)
        fig.subplots_adjust(wspace=0.02, left=0.01, right=0.99)
        print("4-view cortical heatmap rendered successfully.")
    except Exception as e:
        print(f"Nilearn 4-view failed ({e}), trying 2-view...")
        try:
            plotter = PlotBrainNilearn(mesh="fsaverage5", inflate="half", bg_map="sulcal")
            fig, axes = plotter.get_fig_axes(views=["left", "right"])
            plotter.plot_surf(
                mean_activation, axes=axes, views=["left", "right"],
                cmap="hot", norm_percentile=95,
                colorbar=False,
            )
            fig.set_size_inches(12, 5)
        except Exception as e2:
            print(f"All nilearn plotting failed ({e2}), using fallback")
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            half = len(mean_activation) // 2
            for ax, d, title in [
                (axes[0], mean_activation[:half], "Left Hemisphere"),
                (axes[1], mean_activation[half:], "Right Hemisphere"),
            ]:
                n = int(np.sqrt(len(d)))
                ax.imshow(d[:n*n].reshape(n, n), cmap="hot", interpolation="bilinear")
                ax.set_title(title, fontsize=12, color="white")
                ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                facecolor="#050508", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    heatmap_b64 = base64.b64encode(buf.read()).decode()

    temporal_heatmaps = []
    n_timesteps = preds.shape[0]
    if n_timesteps > 1:
        print(f"Rendering {n_timesteps} temporal brain frames...")
        try:
            from tribev2.plotting.cortical import PlotBrainNilearn
            for t in range(n_timesteps):
                try:
                    tp = PlotBrainNilearn(mesh="fsaverage5", inflate="half", bg_map="sulcal")
                    tf, ta = tp.get_fig_axes(views=["left", "right"])
                    tp.plot_surf(preds[t], axes=ta, views=["left", "right"],
                                 cmap="hot", norm_percentile=95, colorbar=False)
                    tf.set_size_inches(8, 4)
                    tb = io.BytesIO()
                    tf.savefig(tb, format="png", dpi=80, bbox_inches="tight",
                               facecolor="#050508", edgecolor="none")
                    plt.close(tf)
                    tb.seek(0)
                    temporal_heatmaps.append(base64.b64encode(tb.read()).decode())
                except Exception as ex:
                    print(f"  Frame {t+1} failed: {ex}")
                    temporal_heatmaps.append("")
                print(f"  Frame {t+1}/{n_timesteps} done.")
            print(f"All {n_timesteps} temporal frames rendered.")
        except Exception as ex:
            print(f"Temporal rendering setup failed: {ex}")

    import os
    os.unlink(temp_path)

    return {
        "roi_means": roi_means,
        "top_regions": top_rois,
        "n_timesteps": int(preds.shape[0]),
        "heatmap_base64": heatmap_b64,
        "predictions_mean": mean_activation.tolist(),
        "predictions_shape": list(preds.shape),
        "temporal_roi_data": temporal_roi_data,
        "temporal_heatmaps": temporal_heatmaps,
    }


_model = None


# ---------------------------------------------------------------------------
# Local test entrypoint
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main():
    """Quick test: simulate with a tiny dummy video."""
    import tempfile, subprocess

    print("Creating test video...")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        test_path = f.name

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        "testsrc=duration=3:size=256x256:rate=25",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", test_path,
    ], capture_output=True)

    with open(test_path, "rb") as f:
        content_bytes = f.read()

    print(f"Test video: {len(content_bytes)} bytes")

    sim = BrainSimulator()
    result = sim.simulate.remote(content_bytes, "test.mp4")
    print(f"Simulation result: {result['n_timesteps']} timesteps, "
          f"{len(result['roi_means'])} ROIs")
    print(f"Top regions: {result['top_regions'][:5]}")

    heatmap = sim.generate_heatmap.remote(result["predictions_mean"])
    print(f"Heatmap: {len(heatmap)} bytes")

    import os
    os.unlink(test_path)
    print("Done!")
