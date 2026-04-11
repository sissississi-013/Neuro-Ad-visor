"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Link, Zap, Image, Film, Music } from "lucide-react";

interface Props {
  onUpload: (file: File | null, url: string | null, platform: string, caption: string) => void;
  loading: boolean;
}

const PLATFORMS = ["instagram", "tiktok", "twitter", "youtube", "facebook"];

export default function UploadZone({ onUpload, loading }: Props) {
  const [mode, setMode] = useState<"file" | "url">("file");
  const [url, setUrl] = useState("");
  const [caption, setCaption] = useState("");
  const [platform, setPlatform] = useState("instagram");
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const handleSubmit = () => {
    if (mode === "file" && file) {
      onUpload(file, null, platform, caption);
    } else if (mode === "url" && url.trim()) {
      onUpload(null, url.trim(), platform, caption);
    }
  };

  const ready = mode === "file" ? !!file : !!url.trim();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto"
    >
      {/* Mode toggle */}
      <div className="flex gap-2 mb-6">
        {(["file", "url"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
              mode === m
                ? "bg-[var(--cyan)]/10 text-[var(--cyan)] border border-[var(--cyan)]/30"
                : "bg-[var(--surface-raised)] text-[var(--dim)] border border-[var(--border)] hover:text-[var(--foreground)]"
            }`}
          >
            {m === "file" ? <Upload size={14} /> : <Link size={14} />}
            {m === "file" ? "Upload File" : "Paste URL"}
          </button>
        ))}
      </div>

      {/* Drop zone / URL input */}
      <AnimatePresence mode="wait">
        {mode === "file" ? (
          <motion.div
            key="file"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
              dragOver
                ? "border-[var(--cyan)] bg-[var(--cyan)]/5"
                : "border-[var(--border)] bg-[var(--surface)] hover:border-[var(--dim)]"
            }`}
            onClick={() => {
              const inp = document.createElement("input");
              inp.type = "file";
              inp.accept = "image/*,video/*,audio/*";
              inp.onchange = () => inp.files?.[0] && handleFile(inp.files[0]);
              inp.click();
            }}
          >
            {preview && file ? (
              <div className="flex flex-col items-center gap-4">
                {file.type.startsWith("video/") ? (
                  <video
                    src={preview}
                    controls
                    muted
                    className="max-h-48 rounded-xl border border-[var(--border)]"
                  />
                ) : (
                  <img
                    src={preview}
                    alt="Preview"
                    className="max-h-48 rounded-xl border border-[var(--border)]"
                  />
                )}
                <p className="font-mono text-sm text-[var(--dim)]">
                  {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="flex gap-3 text-[var(--dim)]">
                  <Image size={24} />
                  <Film size={24} />
                  <Music size={24} />
                </div>
                <p className="text-[var(--dim)] font-medium">
                  Drop your creative to analyze
                </p>
                <p className="text-xs text-[var(--dim)]/60 font-mono">
                  MP4, MOV, WebM, AVI &bull; PNG, JPG, WebP &bull; up to 100 MB
                </p>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="url"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://instagram.com/p/... or any social media URL"
              className="w-full px-5 py-4 bg-[var(--surface)] border border-[var(--border)] rounded-xl font-mono text-sm text-[var(--foreground)] placeholder:text-[var(--dim)]/40 focus:outline-none focus:border-[var(--cyan)]/50 transition-colors"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Caption + platform */}
      <div className="mt-4 flex gap-3">
        <input
          type="text"
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder="Ad copy / caption text (optional)"
          className="flex-1 px-4 py-3 bg-[var(--surface)] border border-[var(--border)] rounded-xl font-mono text-sm text-[var(--foreground)] placeholder:text-[var(--dim)]/40 focus:outline-none focus:border-[var(--cyan)]/50 transition-colors"
        />
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="px-4 py-3 bg-[var(--surface)] border border-[var(--border)] rounded-xl font-mono text-sm text-[var(--foreground)] focus:outline-none focus:border-[var(--cyan)]/50 transition-colors appearance-none"
        >
          {PLATFORMS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      {/* Submit */}
      <motion.button
        onClick={handleSubmit}
        disabled={!ready || loading}
        whileHover={ready && !loading ? { scale: 1.02 } : {}}
        whileTap={ready && !loading ? { scale: 0.98 } : {}}
        className={`mt-6 w-full py-4 rounded-xl font-semibold text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-all ${
          ready && !loading
            ? "bg-[var(--cyan)] text-[var(--background)] glow-cyan cursor-pointer"
            : "bg-[var(--surface-raised)] text-[var(--dim)] cursor-not-allowed"
        }`}
      >
        {loading ? (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
            >
              <Zap size={16} />
            </motion.div>
            Analyzing Audience Response...
          </>
        ) : (
          <>
            <Zap size={16} />
            Predict Audience Response
          </>
        )}
      </motion.button>
    </motion.div>
  );
}
