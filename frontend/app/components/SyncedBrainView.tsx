"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { Play, Pause, SkipBack, SkipForward, Brain, Film } from "lucide-react";

interface Props {
  mediaUrl: string;
  mediaType: "video" | "image";
  frames: string[];
  videoDuration?: number;
  currentTimestep: number;
  onTimestepChange: (t: number) => void;
}

export default function SyncedBrainView({
  mediaUrl,
  mediaType,
  frames,
  videoDuration,
  currentTimestep,
  onTimestepChange,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const rafRef = useRef<number | null>(null);
  const nFrames = frames.length;

  const syncBrainToVideo = useCallback(() => {
    const video = videoRef.current;
    if (!video || !isPlaying || nFrames === 0) return;

    const duration = video.duration || videoDuration || 1;
    const progress = video.currentTime / duration;
    const frameIdx = Math.min(Math.floor(progress * nFrames), nFrames - 1);

    if (frameIdx !== currentTimestep) {
      onTimestepChange(frameIdx);
    }

    rafRef.current = requestAnimationFrame(syncBrainToVideo);
  }, [isPlaying, nFrames, currentTimestep, onTimestepChange, videoDuration]);

  useEffect(() => {
    if (isPlaying) {
      rafRef.current = requestAnimationFrame(syncBrainToVideo);
    }
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isPlaying, syncBrainToVideo]);

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  const handleScrub = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseInt(e.target.value, 10);
      onTimestepChange(val);

      const video = videoRef.current;
      if (video && video.duration) {
        video.currentTime = (val / nFrames) * video.duration;
      }
    },
    [nFrames, onTimestepChange]
  );

  const stepFrame = useCallback(
    (delta: number) => {
      const next = Math.max(0, Math.min(nFrames - 1, currentTimestep + delta));
      onTimestepChange(next);

      const video = videoRef.current;
      if (video && video.duration) {
        video.currentTime = (next / nFrames) * video.duration;
      }
    },
    [nFrames, currentTimestep, onTimestepChange]
  );

  const handleVideoEnd = useCallback(() => {
    setIsPlaying(false);
    onTimestepChange(nFrames - 1);
  }, [nFrames, onTimestepChange]);

  const currentSeconds = videoDuration
    ? ((currentTimestep / Math.max(nFrames - 1, 1)) * videoDuration).toFixed(1)
    : (currentTimestep * 2).toFixed(1);

  const totalSeconds = videoDuration
    ? videoDuration.toFixed(1)
    : ((nFrames - 1) * 2).toFixed(1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Brain size={14} className="text-[var(--magenta)]" />
        <span className="font-mono text-xs text-[var(--magenta)] uppercase tracking-[0.2em]">
          Temporal Brain Reaction
        </span>
        <span className="ml-auto font-mono text-[10px] text-[var(--dim)]">
          {nFrames} frames &bull; ~{totalSeconds}s
        </span>
      </div>

      {/* Side-by-side panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Left: original video */}
        <div className="relative rounded-xl overflow-hidden border border-[var(--border)] bg-[#080810] flex items-center justify-center min-h-[280px]">
          <div className="absolute top-2 left-2 z-10 flex items-center gap-1.5 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm">
            <Film size={10} className="text-[var(--cyan)]" />
            <span className="font-mono text-[9px] text-[var(--cyan)] uppercase tracking-wider">
              Your Creative
            </span>
          </div>
          {mediaType === "video" ? (
            <video
              ref={videoRef}
              src={mediaUrl}
              className="w-full h-full object-contain"
              muted
              playsInline
              preload="auto"
              onLoadedMetadata={() => setVideoReady(true)}
              onEnded={handleVideoEnd}
            />
          ) : (
            <img
              src={mediaUrl}
              alt="Uploaded content"
              className="w-full h-full object-contain"
            />
          )}
        </div>

        {/* Right: brain 2x2 grid frame */}
        <div className="relative rounded-xl overflow-hidden border border-[var(--border)] bg-[#080810] flex items-center justify-center min-h-[280px]">
          <div className="absolute top-2 left-2 z-10 flex items-center gap-1.5 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm">
            <Brain size={10} className="text-[var(--magenta)]" />
            <span className="font-mono text-[9px] text-[var(--magenta)] uppercase tracking-wider">
              Brain Response
            </span>
          </div>
          <div className="absolute top-2 right-2 z-10 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm">
            <span className="font-mono text-[9px] text-[var(--dim)]">
              t={currentTimestep + 1}/{nFrames}
            </span>
          </div>
          {frames[currentTimestep] ? (
            <img
              src={`data:image/png;base64,${frames[currentTimestep]}`}
              alt={`Brain activation at timestep ${currentTimestep}`}
              className="w-full h-full object-contain p-1"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-[var(--dim)]">
              <Brain size={24} className="opacity-30" />
            </div>
          )}
        </div>
      </div>

      {/* Transport controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => stepFrame(-1)}
          disabled={currentTimestep === 0}
          className="p-1.5 rounded-lg hover:bg-[var(--surface-raised)] text-[var(--dim)] hover:text-[var(--foreground)] transition-colors disabled:opacity-20"
        >
          <SkipBack size={14} />
        </button>

        <button
          onClick={togglePlay}
          disabled={mediaType !== "video" || !videoReady}
          className="p-2 rounded-lg bg-[var(--cyan)]/10 border border-[var(--cyan)]/20 text-[var(--cyan)] hover:bg-[var(--cyan)]/20 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {isPlaying ? <Pause size={14} /> : <Play size={14} />}
        </button>

        <button
          onClick={() => stepFrame(1)}
          disabled={currentTimestep >= nFrames - 1}
          className="p-1.5 rounded-lg hover:bg-[var(--surface-raised)] text-[var(--dim)] hover:text-[var(--foreground)] transition-colors disabled:opacity-20"
        >
          <SkipForward size={14} />
        </button>

        {/* Scrub slider */}
        <div className="flex-1 flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={nFrames - 1}
            value={currentTimestep}
            onChange={handleScrub}
            className="flex-1 h-1 appearance-none bg-[var(--border)] rounded-full cursor-pointer
              [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
              [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--cyan)]
              [&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(0,240,255,0.4)]"
          />
          <span className="font-mono text-[10px] text-[var(--dim)] min-w-[70px] text-right">
            {currentSeconds}s / {totalSeconds}s
          </span>
        </div>
      </div>

      {/* Hemodynamic delay note */}
      <p className="mt-3 font-mono text-[9px] text-[var(--dim)]/50 text-center">
        Brain fMRI response is delayed ~4-6s from visual stimulus (hemodynamic lag)
      </p>
    </motion.div>
  );
}
