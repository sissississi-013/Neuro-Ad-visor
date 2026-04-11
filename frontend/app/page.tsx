"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Activity, Lightbulb, Sparkles, GitCompare, ChevronRight } from "lucide-react";

import UploadZone from "./components/UploadZone";
import BrainViewer from "./components/BrainViewer";
import BrainTimeline from "./components/BrainTimeline";
import EmotionRadar from "./components/EmotionRadar";
import SuggestionCards from "./components/SuggestionCards";
import CompareView from "./components/CompareView";

import {
  uploadContent,
  runSimulation,
  getInterpretation,
  runPolishing,
  runComparison,
} from "@/lib/api";

type Phase = "upload" | "simulation" | "interpretation" | "polishing" | "comparison";

const PHASE_META: Record<Phase, { icon: React.ReactNode; label: string; step: number }> = {
  upload:         { icon: <Brain size={14} />,       label: "Upload",        step: 1 },
  simulation:     { icon: <Activity size={14} />,    label: "Neuro Scan",   step: 2 },
  interpretation: { icon: <Lightbulb size={14} />,   label: "Insights",      step: 3 },
  polishing:      { icon: <Sparkles size={14} />,    label: "Optimize",      step: 4 },
  comparison:     { icon: <GitCompare size={14} />,  label: "Results",       step: 5 },
};

export default function Home() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Session data
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [simData, setSimData] = useState<any>(null);
  const [interpretation, setInterpretation] = useState<any>(null);
  const [polishData, setPolishData] = useState<any>(null);
  const [compareData, setCompareData] = useState<any>(null);
  const [caption, setCaption] = useState("");
  const [platform, setPlatform] = useState("instagram");

  const handleUpload = async (
    file: File | null,
    url: string | null,
    plat: string,
    cap: string
  ) => {
    setError(null);
    setLoading(true);
    setCaption(cap);
    setPlatform(plat);

    try {
      setLoadingMsg("Uploading content...");
      const upload = await uploadContent(file, url, plat, cap);
      setSessionId(upload.session_id);

      setPhase("simulation");
      setLoadingMsg("Running brain simulation on GPU... (first run may take 2-3 min)");
      const sim = await runSimulation(upload.session_id);
      setSimData(sim);
      setPhase("interpretation");

      // Interpretation is separate -- don't lose brain results if it fails
      try {
        setLoadingMsg("AI is interpreting brain response...");
        const interp = await getInterpretation(upload.session_id);
        setInterpretation(interp);
      } catch (interpErr: any) {
        console.error("Interpretation failed:", interpErr);
        setError("Brain scan complete! AI interpretation failed -- you can still see the brain results above.");
      }
    } catch (e: any) {
      setError(e.message || "Something went wrong");
      if (!simData) setPhase("upload");
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  };

  const handleApprove = async (ids: string[]) => {
    if (!sessionId) return;
    setError(null);
    setLoading(true);

    try {
      setPhase("polishing");
      const result = await runPolishing(sessionId, ids, caption, platform);
      setPolishData(result);

      const cmp = await runComparison(sessionId);
      setCompareData(cmp);
      setPhase("comparison");
    } catch (e: any) {
      setError(e.message || "Polishing failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPhase("upload");
    setSessionId(null);
    setSimData(null);
    setInterpretation(null);
    setPolishData(null);
    setCompareData(null);
    setError(null);
    setCaption("");
  };

  const currentStep = PHASE_META[phase].step;

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)]/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--cyan)]/10 border border-[var(--cyan)]/20 flex items-center justify-center">
              <Brain size={16} className="text-[var(--cyan)]" />
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-tight">Neuro-Advisor</h1>
              <p className="font-mono text-[10px] text-[var(--dim)] uppercase tracking-widest">
                AI Neuromarketing Intelligence
              </p>
            </div>
          </div>

          {/* Phase stepper */}
          <div className="flex items-center gap-1">
            {(Object.keys(PHASE_META) as Phase[]).map((p, i) => {
              const meta = PHASE_META[p];
              const isActive = meta.step <= currentStep;
              const isCurrent = p === phase;

              return (
                <div key={p} className="flex items-center">
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg font-mono text-xs transition-all ${
                      isCurrent
                        ? "bg-[var(--cyan)]/10 text-[var(--cyan)] border border-[var(--cyan)]/20"
                        : isActive
                        ? "text-[var(--foreground)]/60"
                        : "text-[var(--dim)]/30"
                    }`}
                  >
                    {meta.icon}
                    <span className="hidden sm:inline">{meta.label}</span>
                  </div>
                  {i < 4 && (
                    <ChevronRight
                      size={10}
                      className={isActive ? "text-[var(--dim)]" : "text-[var(--dim)]/20"}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {phase !== "upload" && (
            <button
              onClick={handleReset}
              className="font-mono text-xs text-[var(--dim)] hover:text-[var(--foreground)] transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 rounded-xl border border-[var(--magenta)]/30 bg-[var(--magenta)]/5 text-[var(--magenta)] font-mono text-sm"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {/* Phase 1: Upload */}
          {phase === "upload" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, x: -50 }}
              className="flex flex-col items-center pt-12"
            >
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-12"
              >
                <h2 className="text-4xl font-bold tracking-tight mb-3">
                  Know what{" "}
                  <span className="text-[var(--cyan)]">converts</span>{" "}
                  before you post
                </h2>
                <p className="text-[var(--dim)] max-w-lg mx-auto leading-relaxed">
                  Predict your audience&apos;s emotional response to any creative
                  — powered by Meta&apos;s TRIBE v2 fMRI model trained on 720
                  real brain scans. Get AI-driven optimization suggestions that
                  boost engagement.
                </p>
              </motion.div>

              {/* Social proof / value props */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="flex flex-wrap justify-center gap-6 mb-10 font-mono text-[11px] text-[var(--dim)] uppercase tracking-widest"
              >
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--cyan)]" />
                  Real fMRI-based predictions
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--magenta)]" />
                  AI content optimization
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--emerald)]" />
                  Before &amp; after comparison
                </span>
              </motion.div>

              <UploadZone onUpload={handleUpload} loading={loading} />
            </motion.div>
          )}

          {/* Phase 2/3: Loading state while brain sim or interpretation runs */}
          {(phase === "simulation" || phase === "interpretation") &&
            !simData && loading && (
              <motion.div
                key="loading-sim"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-24"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="mb-6"
                >
                  <Brain size={40} className="text-[var(--cyan)]" />
                </motion.div>
                <p className="font-mono text-sm text-[var(--cyan)] uppercase tracking-wider mb-2">
                  {loadingMsg || "Processing..."}
                </p>
                <p className="text-xs text-[var(--dim)] max-w-sm text-center">
                  Running real fMRI-based neural simulation on GPU. First analysis
                  takes ~2 min to load, then ~30 seconds per creative.
                </p>
              </motion.div>
            )}

          {/* Phase 2: Simulation results */}
          {(phase === "simulation" || phase === "interpretation") &&
            simData && (
              <motion.div
                key="sim"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="space-y-8"
              >
                {/* HERO: Full-width brain heatmap */}
                <BrainViewer
                  heatmapBase64={simData.heatmap_base64}
                  topRegions={simData.top_regions}
                  label="Cortical Activation Map"
                />

                {/* Timeline (only for videos with multiple timesteps) */}
                {simData.timeline && simData.timeline.length > 1 && (
                  <BrainTimeline timeline={simData.timeline} />
                )}

                {/* Radar + Interpretation side by side */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Emotional Profile */}
                  <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity size={14} className="text-[var(--cyan)]" />
                      <span className="font-mono text-xs text-[var(--cyan)] uppercase tracking-[0.2em]">
                        Emotional Profile
                      </span>
                    </div>
                    <EmotionRadar data={simData.radar} />
                  </div>

                  {/* AI Interpretation */}
                  <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 flex flex-col">
                    {interpretation ? (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex flex-col h-full"
                      >
                        <div className="flex items-center gap-2 mb-4">
                          <Lightbulb size={14} className="text-[var(--magenta)]" />
                          <span className="font-mono text-xs text-[var(--magenta)] uppercase tracking-[0.2em]">
                            AI Interpretation
                          </span>
                          <span
                            className={`ml-auto px-2.5 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider ${
                              interpretation.concern_level === "high"
                                ? "bg-[var(--magenta)]/10 text-[var(--magenta)] border border-[var(--magenta)]/20"
                                : interpretation.concern_level === "moderate"
                                ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                : "bg-[var(--emerald)]/10 text-[var(--emerald)] border border-[var(--emerald)]/20"
                            }`}
                          >
                            {interpretation.concern_level} concern
                          </span>
                        </div>
                        <p className="text-sm text-[var(--foreground)]/80 leading-relaxed flex-1">
                          {interpretation.summary}
                        </p>
                        <div className="mt-4 pt-4 border-t border-[var(--border)]">
                          <p className="font-mono text-xs text-[var(--dim)]">
                            Dominant response:{" "}
                            <span className="text-[var(--foreground)]">
                              {interpretation.dominant_emotion}
                            </span>
                          </p>
                        </div>
                      </motion.div>
                    ) : loading ? (
                      <div className="flex items-center justify-center h-full py-12">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                        >
                          <Lightbulb size={20} className="text-[var(--dim)]" />
                        </motion.div>
                        <span className="ml-3 font-mono text-xs text-[var(--dim)]">
                          Interpreting brain response...
                        </span>
                      </div>
                    ) : null}
                  </div>
                </div>

                {/* Suggestions */}
                {interpretation?.suggestions?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="mt-10"
                  >
                    <h3 className="font-mono text-xs text-[var(--foreground)]/60 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Sparkles size={14} className="text-[var(--emerald)]" />
                      Optimization Suggestions
                    </h3>
                    <SuggestionCards
                      suggestions={interpretation.suggestions}
                      onApprove={handleApprove}
                      loading={loading}
                    />
                  </motion.div>
                )}
              </motion.div>
            )}

          {/* Phase 4-5: Polishing + Comparison */}
          {phase === "polishing" && (
            <motion.div
              key="polishing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                className="mb-6"
              >
                <Sparkles size={32} className="text-[var(--magenta)]" />
              </motion.div>
              <p className="font-mono text-sm text-[var(--dim)] uppercase tracking-wider">
                Optimizing creative &amp; re-predicting audience response...
              </p>
            </motion.div>
          )}

          {phase === "comparison" && compareData && (
            <motion.div
              key="compare"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold tracking-tight mb-2">
                  Performance{" "}
                  <span className="text-[var(--emerald)]">Uplift</span>
                </h2>
                <p className="text-[var(--dim)] text-sm">
                  See how the optimized creative scores against your original
                </p>
              </div>

              <CompareView
                originalHeatmap={compareData.original_heatmap_base64}
                polishedHeatmap={compareData.polished_heatmap_base64}
                originalRadar={compareData.original_radar}
                polishedRadar={compareData.polished_radar}
                deltas={compareData.deltas}
                polishedImageBase64={polishData?.polished_image_base64}
                polishedCaption={polishData?.polished_caption}
              />

              <div className="mt-8 text-center">
                <button
                  onClick={handleReset}
                  className="px-8 py-3 rounded-xl bg-[var(--surface-raised)] border border-[var(--border)] font-mono text-sm text-[var(--dim)] hover:text-[var(--foreground)] transition-colors"
                >
                  Test Another Creative
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] bg-[var(--surface)]/30">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <p className="font-mono text-[10px] text-[var(--dim)]/40 uppercase tracking-widest">
            Neuro-Advisor &bull; Meta TRIBE v2 &bull; Perplexity Agent API &bull; OpenAI
          </p>
          <p className="font-mono text-[10px] text-[var(--dim)]/40">
            Perplexity Hackathon 2026
          </p>
        </div>
      </footer>
    </main>
  );
}
