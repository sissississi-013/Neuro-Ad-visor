"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Image, Type, Volume2, LayoutGrid, ChevronRight } from "lucide-react";

interface Suggestion {
  id: string;
  title: string;
  description: string;
  target_emotion: string;
  estimated_impact: string;
  rationale: string;
  modification_type: string;
}

interface Props {
  suggestions: Suggestion[];
  onApprove: (ids: string[]) => void;
  loading: boolean;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  image: <Image size={14} />,
  text: <Type size={14} />,
  audio: <Volume2 size={14} />,
  layout: <LayoutGrid size={14} />,
};

const TYPE_COLORS: Record<string, string> = {
  image: "var(--cyan)",
  text: "var(--magenta)",
  audio: "var(--emerald)",
  layout: "var(--dim)",
};

export default function SuggestionCards({ suggestions, onApprove, loading }: Props) {
  const [selected, setSelected] = useState<Set<string>>(
    new Set(suggestions.map((s) => s.id))
  );

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <p className="font-mono text-xs text-[var(--dim)] uppercase tracking-wider">
          Toggle suggestions to apply
        </p>
        <p className="font-mono text-xs text-[var(--cyan)]">
          {selected.size}/{suggestions.length} selected
        </p>
      </div>

      {suggestions.map((s, i) => {
        const active = selected.has(s.id);
        const color = TYPE_COLORS[s.modification_type] || "var(--dim)";

        return (
          <motion.div
            key={s.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            onClick={() => toggle(s.id)}
            className={`relative p-5 rounded-xl border cursor-pointer transition-all group ${
              active
                ? "border-[var(--cyan)]/30 bg-[var(--cyan)]/5"
                : "border-[var(--border)] bg-[var(--surface)] opacity-60 hover:opacity-80"
            }`}
          >
            {/* Toggle indicator */}
            <div
              className={`absolute top-5 right-5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                active ? "border-[var(--cyan)] bg-[var(--cyan)]" : "border-[var(--dim)]"
              }`}
            >
              {active && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-2 h-2 rounded-full bg-[var(--background)]"
                />
              )}
            </div>

            {/* Type badge */}
            <div
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider mb-3"
              style={{
                background: `color-mix(in srgb, ${color} 10%, transparent)`,
                color,
                border: `1px solid color-mix(in srgb, ${color} 20%, transparent)`,
              }}
            >
              {TYPE_ICONS[s.modification_type]}
              {s.modification_type}
            </div>

            <h3 className="font-semibold text-[var(--foreground)] pr-8 mb-1.5">
              {s.title}
            </h3>
            <p className="text-sm text-[var(--dim)] mb-3 leading-relaxed">
              {s.description}
            </p>

            <div className="flex flex-wrap gap-3 text-xs font-mono">
              <span className="text-[var(--emerald)]">
                Impact: {s.estimated_impact}
              </span>
              <span className="text-[var(--dim)]">|</span>
              <span className="text-[var(--magenta)]">
                Target: {s.target_emotion}
              </span>
            </div>

            {/* Rationale (expanded on hover) */}
            <div className="mt-3 text-xs text-[var(--dim)]/60 leading-relaxed overflow-hidden max-h-0 group-hover:max-h-20 transition-all duration-300">
              {s.rationale}
            </div>
          </motion.div>
        );
      })}

      {/* Apply button */}
      <motion.button
        onClick={() => onApprove(Array.from(selected))}
        disabled={selected.size === 0 || loading}
        whileHover={selected.size > 0 && !loading ? { scale: 1.02 } : {}}
        whileTap={selected.size > 0 && !loading ? { scale: 0.98 } : {}}
        className={`w-full mt-4 py-4 rounded-xl font-semibold text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-all ${
          selected.size > 0 && !loading
            ? "bg-[var(--magenta)] text-white glow-magenta cursor-pointer"
            : "bg-[var(--surface-raised)] text-[var(--dim)] cursor-not-allowed"
        }`}
      >
        {loading ? (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
            >
              <Sparkles size={16} />
            </motion.div>
            Polishing Content...
          </>
        ) : (
          <>
            <Sparkles size={16} />
            Apply {selected.size} Suggestion{selected.size !== 1 ? "s" : ""}
            <ChevronRight size={14} />
          </>
        )}
      </motion.button>
    </div>
  );
}
