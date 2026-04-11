"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import BrainViewer from "./BrainViewer";
import EmotionRadar from "./EmotionRadar";

interface Delta {
  before: number;
  after: number;
  delta: number;
  percent_change: number;
}

interface Props {
  originalHeatmap: string;
  polishedHeatmap: string;
  originalRadar: Record<string, number>;
  polishedRadar: Record<string, number>;
  deltas: Record<string, Delta>;
  polishedImageBase64?: string | null;
  polishedCaption?: string | null;
}

const LABELS: Record<string, string> = {
  fear: "Fear",
  disgust: "Disgust",
  reward: "Reward",
  social_connection: "Social",
  visual_attention: "Visual",
  cognitive_load: "Cognition",
  anxiety: "Anxiety",
  empathy: "Empathy",
  auditory_engagement: "Audio",
};

export default function CompareView({
  originalHeatmap,
  polishedHeatmap,
  originalRadar,
  polishedRadar,
  deltas,
  polishedImageBase64,
  polishedCaption,
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-8"
    >
      {/* Brain heatmaps side-by-side */}
      <div className="grid grid-cols-2 gap-4">
        <BrainViewer heatmapBase64={originalHeatmap} label="Original" />
        <BrainViewer heatmapBase64={polishedHeatmap} label="Polished" />
      </div>

      {/* Radar overlay */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6">
        <h3 className="font-mono text-xs text-[var(--dim)] uppercase tracking-wider mb-4">
          Emotional Profile Comparison
        </h3>
        <EmotionRadar data={originalRadar} comparisonData={polishedRadar} />
      </div>

      {/* Delta scores */}
      <div className="grid grid-cols-3 gap-3">
        {Object.entries(deltas).map(([dim, d]) => {
          const improving =
            (dim === "fear" || dim === "anxiety" || dim === "disgust")
              ? d.delta < 0
              : d.delta > 0;
          const neutral = Math.abs(d.percent_change) < 5;

          return (
            <motion.div
              key={dim}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border ${
                neutral
                  ? "border-[var(--border)] bg-[var(--surface)]"
                  : improving
                  ? "border-[var(--emerald)]/20 bg-[var(--emerald)]/5"
                  : "border-[var(--magenta)]/20 bg-[var(--magenta)]/5"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs text-[var(--dim)] uppercase">
                  {LABELS[dim] || dim}
                </span>
                {neutral ? (
                  <Minus size={12} className="text-[var(--dim)]" />
                ) : improving ? (
                  <TrendingUp size={12} className="text-[var(--emerald)]" />
                ) : (
                  <TrendingDown size={12} className="text-[var(--magenta)]" />
                )}
              </div>
              <div className="font-mono text-lg font-bold">
                <span
                  className={
                    neutral
                      ? "text-[var(--dim)]"
                      : improving
                      ? "text-[var(--emerald)]"
                      : "text-[var(--magenta)]"
                  }
                >
                  {d.percent_change > 0 ? "+" : ""}
                  {d.percent_change.toFixed(0)}%
                </span>
              </div>
              <div className="font-mono text-xs text-[var(--dim)] mt-0.5">
                {(d.before * 100).toFixed(0)} → {(d.after * 100).toFixed(0)}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Polished content preview */}
      {(polishedImageBase64 || polishedCaption) && (
        <div className="bg-[var(--surface)] border border-[var(--emerald)]/20 rounded-2xl p-6 glow-emerald">
          <h3 className="font-mono text-xs text-[var(--emerald)] uppercase tracking-wider mb-4">
            Polished Content
          </h3>
          {polishedImageBase64 && (
            <img
              src={`data:image/png;base64,${polishedImageBase64}`}
              alt="Polished content"
              className="w-full max-h-96 object-contain rounded-xl mb-4"
            />
          )}
          {polishedCaption && (
            <p className="text-sm text-[var(--foreground)] leading-relaxed whitespace-pre-wrap">
              {polishedCaption}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
