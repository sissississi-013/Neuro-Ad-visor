"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Play, Clock } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface TimelinePoint {
  t: number;
  seconds: number;
  scores: Record<string, number>;
}

interface Props {
  timeline: TimelinePoint[];
  onTimestepSelect?: (t: number) => void;
}

const EMOTIONS = [
  { key: "fear", color: "#ff2d8a", label: "Fear" },
  { key: "anxiety", color: "#ff6b35", label: "Anxiety" },
  { key: "reward", color: "#00ff94", label: "Reward" },
  { key: "visual_attention", color: "#00f0ff", label: "Visual" },
  { key: "social_connection", color: "#a78bfa", label: "Social" },
  { key: "empathy", color: "#f0abfc", label: "Empathy" },
];

export default function BrainTimeline({ timeline, onTimestepSelect }: Props) {
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);
  const [selectedEmotions, setSelectedEmotions] = useState<Set<string>>(
    new Set(["fear", "reward", "visual_attention", "anxiety"])
  );

  const chartData = useMemo(
    () =>
      timeline.map((point) => ({
        time: `${point.seconds.toFixed(0)}s`,
        seconds: point.seconds,
        ...Object.fromEntries(
          Object.entries(point.scores).map(([k, v]) => [k, Math.round(v * 100)])
        ),
      })),
    [timeline]
  );

  const toggle = (key: string) => {
    setSelectedEmotions((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  if (timeline.length <= 1) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock size={14} className="text-[var(--cyan)]" />
          <span className="font-mono text-xs text-[var(--cyan)] uppercase tracking-[0.2em]">
            Temporal Brain Journey
          </span>
        </div>
        <span className="font-mono text-xs text-[var(--dim)]">
          {timeline.length} timesteps &bull; {(timeline[timeline.length - 1]?.seconds ?? 0).toFixed(0)}s total
        </span>
      </div>

      {/* Emotion toggles */}
      <div className="flex flex-wrap gap-2 mb-4">
        {EMOTIONS.map((e) => (
          <button
            key={e.key}
            onClick={() => toggle(e.key)}
            className={`px-2.5 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider border transition-all ${
              selectedEmotions.has(e.key)
                ? "border-current opacity-100"
                : "border-[var(--border)] opacity-30 hover:opacity-50"
            }`}
            style={{ color: selectedEmotions.has(e.key) ? e.color : "var(--dim)" }}
          >
            <span
              className="inline-block w-1.5 h-1.5 rounded-full mr-1.5"
              style={{ backgroundColor: e.color }}
            />
            {e.label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <XAxis
              dataKey="time"
              tick={{ fill: "var(--dim)", fontSize: 10, fontFamily: "'JetBrains Mono'" }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: "var(--dim)", fontSize: 10, fontFamily: "'JetBrains Mono'" }}
              axisLine={false}
              tickLine={false}
              width={30}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--surface-raised)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontFamily: "'JetBrains Mono'",
                fontSize: "11px",
              }}
              labelStyle={{ color: "var(--foreground)" }}
            />
            {EMOTIONS.filter((e) => selectedEmotions.has(e.key)).map((e) => (
              <Area
                key={e.key}
                type="monotone"
                dataKey={e.key}
                stroke={e.color}
                fill={e.color}
                fillOpacity={0.08}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3, fill: e.color }}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
