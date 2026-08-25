"use client";

import { useEffect, useState } from "react";
import {
  api,
  RepositoryResponse,
  HealthResponse,
  DormancyResponse,
  AIInsightsResponse,
} from "@/lib/api";

interface RepoDetailsProps {
  repoId: number;
  onBack: () => void;
  onSyncSuccess: () => void;
}

export default function RepoDetails({ repoId, onBack, onSyncSuccess }: RepoDetailsProps) {
  const [repo, setRepo] = useState<RepositoryResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dormancy, setDormancy] = useState<DormancyResponse | null>(null);
  const [aiInsights, setAIInsights] = useState<AIInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    setAIInsights(null);
    setAiLoading(false);
    setAiError(null);
    try {
      const [r, h, d] = await Promise.all([
        api.getRepository(repoId),
        api.getRepositoryHealth(repoId),
        api.getRepositoryDormancy(repoId),
      ]);
      setRepo(r);
      setHealth(h);
      setDormancy(d);
    } catch (err: any) {
      setError(err.message || "Failed to fetch repository details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [repoId]);

  const handleGenerateAI = async () => {
    setAiLoading(true);
    setAiError(null);
    try {
      const ai = await api.getRepositoryAIInsights(repoId);
      setAIInsights(ai);
    } catch (err: any) {
      setAiError(err.message || "Failed to generate AI insights.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleSync = async () => {
    if (!repo) return;
    setSyncing(true);
    setError(null);
    try {
      await api.syncRepository(repo.id);
      setAIInsights(null);
      setAiError(null);
      // Re-fetch everything after sync
      await fetchData();
      onSyncSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to sync repository.");
    } finally {
      setSyncing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-400 border-emerald-900/50 bg-emerald-950/20";
    if (score >= 80) return "text-teal-400 border-teal-900/50 bg-teal-950/20";
    if (score >= 70) return "text-amber-400 border-amber-900/50 bg-amber-950/20";
    return "text-rose-450 border-rose-950/30 bg-rose-950/10";
  };

  const getDormancyColor = (status: string) => {
    if (status.toLowerCase() === "active") return "text-emerald-400 border-emerald-900/50 bg-emerald-950/20";
    return "text-rose-450 border-rose-950/30 bg-rose-950/10";
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4 bg-zinc-950">
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-1 rounded-full bg-zinc-400 animate-pulse" />
          <div className="h-1 w-1 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.2s]" />
          <div className="h-1 w-1 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.4s]" />
        </div>
        <span className="text-[10px] font-mono tracking-wider uppercase text-zinc-550">Loading codebase metrics</span>
      </div>
    );
  }

  if (error || !repo) {
    return (
      <div className="mx-auto max-w-xl px-6 py-16 text-center">
        <div className="border border-red-950 bg-red-950/10 p-6 rounded-none">
          <h3 className="text-xs font-mono uppercase tracking-widest text-red-400">Error Loading Details</h3>
          <p className="mt-2 text-xs text-red-400/80 leading-relaxed">{error || "Repository details not found."}</p>
          <button
            onClick={onBack}
            className="mt-5 rounded-none border border-red-900 bg-red-950/50 px-4 py-2 text-[10px] font-mono uppercase tracking-wider text-red-400 hover:bg-red-900 hover:text-white transition-all cursor-pointer"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      {/* Back button & Action Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between mb-10">
        <div className="flex items-baseline gap-4">
          <button
            onClick={onBack}
            className="rounded-none border border-zinc-900 p-1.5 text-zinc-500 hover:bg-zinc-900 hover:text-white transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-zinc-600"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-3.5 w-3.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <div>
            <h1 className="text-3xl font-serif text-white tracking-tight font-light">{repo.name}</h1>
            <p className="text-[10px] text-zinc-500 font-mono mt-1">{repo.full_name}</p>
          </div>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing}
          className={`flex items-center justify-center gap-2.5 rounded-none bg-zinc-100 text-zinc-950 px-4 py-2.5 text-[10px] font-mono uppercase tracking-wider hover:bg-white transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 ${
            syncing ? "cursor-not-allowed bg-zinc-900 text-zinc-650 border border-zinc-850 hover:bg-zinc-900" : ""
          }`}
        >
          {!syncing && (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-3.5 w-3.5 text-zinc-950"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          )}
          {syncing ? "Syncing..." : "Sync GitHub Data"}
        </button>
      </div>

      {/* Repo quick metadata (Single Row Divider) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-6 border-t border-b border-zinc-900 mb-10">
        <div>
          <span className="text-[10px] font-mono font-bold text-zinc-550 uppercase tracking-widest">GitHub Stars</span>
          <p className="text-3xl font-mono text-white mt-1.5 tracking-tight font-normal">{repo.stars ?? 0}</p>
        </div>
        <div className="border-l border-zinc-900/60 pl-6">
          <span className="text-[10px] font-mono font-bold text-zinc-550 uppercase tracking-widest">Forks</span>
          <p className="text-3xl font-mono text-white mt-1.5 tracking-tight font-normal">{repo.forks ?? 0}</p>
        </div>
        <div className="border-l border-zinc-900/60 pl-6">
          <span className="text-[10px] font-mono font-bold text-zinc-550 uppercase tracking-widest">Open Issues</span>
          <p className="text-3xl font-mono text-white mt-1.5 tracking-tight font-normal">{repo.open_issues ?? 0}</p>
        </div>
        <div className="border-l border-zinc-900/60 pl-6">
          <span className="text-[10px] font-mono font-bold text-zinc-550 uppercase tracking-widest">Storage Size</span>
          <p className="text-3xl font-mono text-white mt-1.5 tracking-tight font-normal">
            {repo.size ? `${(repo.size / 1024).toFixed(1)} MB` : "—"}
          </p>
        </div>
      </div>

      {/* Health, Grading & Maintenance Details */}
      <div className="grid gap-8 md:grid-cols-3 mb-10">
        {/* Health score gauge */}
        {health && (
          <div className="border border-zinc-900 bg-zinc-950/20 p-6 flex flex-col justify-between rounded-none min-h-[195px]">
            <div>
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">Health Rating</span>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-4xl font-mono text-white font-normal tracking-tighter">{health.health_score}/100</p>
                  <p className="text-[10px] text-zinc-550 mt-1 font-mono">Grade: <span className="font-semibold text-zinc-350">{health.grade}</span></p>
                </div>
                <div className={`h-11 w-11 rounded-none border flex items-center justify-center text-sm font-mono font-bold ${getScoreColor(health.health_score)}`}>
                  {health.grade}
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3.5 border-t border-zinc-900/60">
              <h4 className="text-[9px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-1.5">Health Summary</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">{health.summary}</p>
            </div>
          </div>
        )}

        {/* Dormancy Maintenance status */}
        {dormancy && (
          <div className="border border-zinc-900 bg-zinc-950/20 p-6 flex flex-col justify-between rounded-none min-h-[195px]">
            <div>
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">Activity Status</span>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-4xl font-mono text-white font-normal tracking-tighter">
                    {dormancy.days_since_last_push} {dormancy.days_since_last_push === 1 ? "day" : "days"}
                  </p>
                  <p className="text-[10px] text-zinc-555 mt-1 font-sans">Since last repository push</p>
                </div>
                <div className={`rounded-none px-2.5 py-1 text-[10px] font-mono uppercase font-semibold border ${getDormancyColor(dormancy.status)}`}>
                  {dormancy.status}
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3.5 border-t border-zinc-900/60">
              <h4 className="text-[9px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-1.5">Maintenance Summary</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">{dormancy.message}</p>
            </div>
          </div>
        )}

        {/* Developer complexity & AI score */}
        {aiInsights && (
          <div className="border border-zinc-900 bg-zinc-950/20 p-6 flex flex-col justify-between rounded-none min-h-[195px]">
            <div>
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">AI Quality Score</span>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-4xl font-mono text-white font-normal tracking-tighter">{aiInsights.ai_score}/100</p>
                  <p className="text-[10px] text-zinc-550 mt-1 font-sans">Complexity: <span className="font-semibold text-zinc-350 font-mono">{aiInsights.complexity}</span></p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`rounded-none px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider font-semibold border ${
                    aiInsights.beginner_friendly
                      ? "text-emerald-400 border-emerald-900/30 bg-emerald-955/10"
                      : "text-amber-400 border-amber-900/30 bg-amber-955/10"
                  }`}>
                    {aiInsights.beginner_friendly ? "Intro friendly" : "Complex"}
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3.5 border-t border-zinc-900/60">
              <h4 className="text-[9px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-1.5">AI Recommendation</h4>
              <p className="text-xs text-zinc-400 leading-relaxed truncate font-sans">{aiInsights.summary}</p>
            </div>
          </div>
        )}

        {!aiInsights && !aiLoading && !aiError && (
          <div className="border border-zinc-900 bg-zinc-950/20 p-6 flex flex-col justify-between rounded-none min-h-[195px]">
            <div>
              <span className="text-[10px] font-mono font-bold text-zinc-550 uppercase tracking-widest">AI Repository Analysis</span>
              <p className="mt-3 text-xs text-zinc-550 leading-relaxed font-sans">
                Generate an AI-powered analysis of this repository, including strengths, weaknesses, and actionable recommendations.
              </p>
            </div>
            <button
              onClick={handleGenerateAI}
              className="mt-5 w-full rounded-none border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-[10px] font-mono uppercase tracking-wider text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-zinc-650"
            >
              Generate AI Analysis
            </button>
          </div>
        )}

        {aiLoading && (
          <div className="border border-zinc-900 bg-zinc-950/20 p-6 flex flex-col justify-center items-center rounded-none min-h-[195px] text-center">
            <div className="flex items-center gap-1.5 mb-3">
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse" />
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.2s]" />
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.4s]" />
            </div>
            <span className="text-xs font-semibold text-zinc-350">Analyzing codebase...</span>
            <span className="text-[9px] text-zinc-550 mt-1 font-mono uppercase tracking-wider">Requesting LLM assessment</span>
          </div>
        )}

        {aiError && (
          <div className="border border-zinc-900 bg-zinc-950/20 p-6 flex flex-col justify-between rounded-none min-h-[195px]">
            <div>
              <span className="text-[10px] font-mono font-bold text-rose-500 uppercase tracking-widest">AI Analysis Failed</span>
              <p className="mt-3 text-xs text-rose-450/80 leading-relaxed line-clamp-3">
                {aiError}
              </p>
            </div>
            <button
              onClick={handleGenerateAI}
              className="mt-5 w-full rounded-none border border-red-950 bg-red-950/10 px-4 py-2.5 text-[10px] font-mono uppercase tracking-wider text-red-400 hover:text-red-350 transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-red-600"
            >
              Retry AI Analysis
            </button>
          </div>
        )}
      </div>

      {/* AI Detailed Insights */}
      {aiInsights && (
        <div className="border border-zinc-900 bg-zinc-950/40 p-8 rounded-none">
          <div className="mb-8 border-b border-zinc-900/60 pb-5">
            <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-zinc-400">AI Repository Deep Dive</h2>
            <p className="text-[10px] text-zinc-500 mt-1 font-sans">Machine learning analysis and structural recommendations.</p>
          </div>

          <div className="grid gap-10 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-zinc-900/60">
            {/* Strengths */}
            <div className="pr-0 md:pr-6">
              <h3 className="flex items-center gap-2 text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-widest mb-5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Core Strengths
              </h3>
              <ul className="space-y-3.5">
                {aiInsights.strengths.map((strength, idx) => (
                  <li key={idx} className="flex gap-2.5 text-xs text-zinc-400 leading-relaxed font-sans">
                    <span className="text-zinc-600 shrink-0 select-none font-mono">-</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div className="pt-6 md:pt-0 pl-0 md:pl-8 pr-0 md:pr-6">
              <h3 className="flex items-center gap-2 text-[10px] font-mono font-bold text-rose-450 uppercase tracking-widest mb-5">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                Weaknesses
              </h3>
              <ul className="space-y-3.5">
                {aiInsights.weaknesses.map((weakness, idx) => (
                  <li key={idx} className="flex gap-2.5 text-xs text-zinc-400 leading-relaxed font-sans">
                    <span className="text-zinc-600 shrink-0 select-none font-mono">-</span>
                    <span>{weakness}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Suggestions */}
            <div className="pt-6 md:pt-0 pl-0 md:pl-8">
              <h3 className="flex items-center gap-2 text-[10px] font-mono font-bold text-zinc-300 uppercase tracking-widest mb-5">
                <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
                Action Items
              </h3>
              <ul className="space-y-3.5">
                {aiInsights.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex gap-2.5 text-xs text-zinc-400 leading-relaxed font-sans">
                    <span className="text-zinc-600 shrink-0 select-none font-mono">-</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
