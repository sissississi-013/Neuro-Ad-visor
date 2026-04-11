"use client";

import { motion } from "framer-motion";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface Props {
  data: Record<string, number>;
  comparisonData?: Record<string, number>;
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

export default function EmotionRadar({ data, comparisonData }: Props) {
  const chartData = Object.entries(data).map(([key, value]) => ({
    dimension: LABELS[key] || key,
    current: Math.round(value * 100),
    ...(comparisonData ? { polished: Math.round((comparisonData[key] || 0) * 100) } : {}),
  }));

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-full h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid
            stroke="var(--border)"
            strokeDasharray="2 4"
          />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{
              fill: "var(--dim)",
              fontSize: 11,
              fontFamily: "'JetBrains Mono', monospace",
            }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Original"
            dataKey="current"
            stroke="var(--cyan)"
            fill="var(--cyan)"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          {comparisonData && (
            <Radar
              name="Polished"
              dataKey="polished"
              stroke="var(--emerald)"
              fill="var(--emerald)"
              fillOpacity={0.1}
              strokeWidth={2}
              strokeDasharray="4 2"
            />
          )}
          {comparisonData && (
            <Legend
              wrapperStyle={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 11,
              }}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
