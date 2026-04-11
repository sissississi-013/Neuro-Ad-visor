"use client";

import { motion } from "framer-motion";

interface Props {
  heatmapBase64: string;
  topRegions?: string[];
  label?: string;
  compact?: boolean;
}

export default function BrainViewer({
  heatmapBase64,
  topRegions,
  label,
  compact = false,
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="relative"
    >
      {label && (
        <div className="flex items-center gap-3 mb-4">
          <div className="w-2 h-2 rounded-full bg-[var(--cyan)] brain-pulse" />
          <span className="font-mono text-xs text-[var(--cyan)] uppercase tracking-[0.2em]">
            {label}
          </span>
        </div>
      )}

      {/* Brain heatmap -- full width, high quality */}
      <div className={`relative rounded-2xl overflow-hidden border border-[var(--border)] bg-[#080810] ${compact ? "" : "glow-cyan"}`}>
        <img
          src={`data:image/png;base64,${heatmapBase64}`}
          alt="Cortical activation heatmap"
          className="w-full h-auto"
          style={{ imageRendering: "auto" }}
        />
      </div>

      {/* Top activated regions */}
      {topRegions && topRegions.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {topRegions.map((r, i) => (
            <motion.span
              key={r}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className={`px-3 py-1.5 rounded-lg font-mono text-xs border ${
                i < 3
                  ? "bg-[var(--cyan)]/10 border-[var(--cyan)]/20 text-[var(--cyan)]"
                  : "bg-[var(--surface-raised)] border-[var(--border)] text-[var(--dim)]"
              }`}
            >
              {i < 3 && <span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--cyan)] mr-1.5 brain-pulse" />}
              {r}
            </motion.span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
