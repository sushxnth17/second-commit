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

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, h, d, ai] = await Promise.all([
        api.getRepository(repoId),
        api.getRepositoryHealth(repoId),
        api.getRepositoryDormancy(repoId),
        api.getRepositoryAIInsights(repoId),
      ]);
      setRepo(r);
      setHealth(h);
      setDormancy(d);
      setAIInsights(ai);
    } catch (err: any) {
      setError(err.message || "Failed to fetch repository details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [repoId]);

  const handleSync = async () => {
    if (!repo) return;
    setSyncing(true);
    setError(null);
    try {
      await api.syncRepository(repo.id);
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
    return "text-rose-400 border-rose-900/50 bg-rose-950/20";
  };

  const getDormancyColor = (status: string) => {
    if (status.toLowerCase() === "active") return "text-emerald-400 border-emerald-900/50 bg-emerald-950/20";
    return "text-rose-400 border-rose-900/50 bg-rose-950/20";
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-2">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        <span className="text-xs text-zinc-550">Loading analysis data...</span>
      </div>
    );
  }

  if (error || !repo) {
    return (
      <div className="mx-auto max-w-xl px-6 py-16 text-center">
        <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-5">
          <h3 className="text-sm font-semibold text-red-400">Error Loading Details</h3>
          <p className="mt-2 text-xs text-red-400/80">{error || "Repository details not found."}</p>
          <button
            onClick={onBack}
            className="mt-4 rounded bg-red-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-red-500 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      {/* Back button & Action Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="rounded border border-zinc-900 p-1.5 text-zinc-500 hover:bg-zinc-900 hover:text-white transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="h-3.5 w-3.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">{repo.name}</h1>
            <p className="text-[10px] text-zinc-550 font-mono mt-0.5">{repo.full_name}</p>
          </div>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing}
          className={`flex items-center justify-center gap-2 rounded border border-zinc-800 bg-zinc-900/30 px-3.5 py-1.5 text-xs font-semibold text-zinc-300 hover:text-white hover:bg-zinc-900 hover:border-zinc-700 transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-indigo-500 ${
            syncing ? "cursor-not-allowed text-zinc-500" : ""
          }`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            className={`h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          {syncing ? "Syncing..." : "Sync GitHub Data"}
        </button>
      </div>

      {/* Repo quick metadata (Single Row Divider) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-4 border-t border-b border-zinc-900 mb-8">
        <div>
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">GitHub Stars</span>
          <p className="text-base font-semibold text-white mt-1 font-mono">{repo.stars ?? 0}</p>
        </div>
        <div className="border-l border-zinc-900/60 pl-6">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Forks</span>
          <p className="text-base font-semibold text-white mt-1 font-mono">{repo.forks ?? 0}</p>
        </div>
        <div className="border-l border-zinc-900/60 pl-6">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Open Issues</span>
          <p className="text-base font-semibold text-white mt-1 font-mono">{repo.open_issues ?? 0}</p>
        </div>
        <div className="border-l border-zinc-900/60 pl-6">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Storage Size</span>
          <p className="text-base font-semibold text-white mt-1 font-mono">
            {repo.size ? `${(repo.size / 1024).toFixed(1)} MB` : "—"}
          </p>
        </div>
      </div>

      {/* Health, Grading & Maintenance Details */}
      <div className="grid gap-6 md:grid-cols-3 mb-8">
        {/* Health score gauge */}
        {health && (
          <div className="rounded-md border border-zinc-900 bg-zinc-950/10 p-5 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Health Rating</span>
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white font-mono">{health.health_score}/100</p>
                  <p className="text-[10px] text-zinc-500 mt-1">Grade: <span className="font-semibold text-zinc-350 font-mono">{health.grade}</span></p>
                </div>
                <div className={`h-10 w-10 rounded border flex items-center justify-center text-sm font-black ${getScoreColor(health.health_score)}`}>
                  {health.grade}
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3 border-t border-zinc-900/60">
              <h4 className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Health Summary</h4>
              <p className="text-xs text-zinc-500 leading-relaxed">{health.summary}</p>
            </div>
          </div>
        )}

        {/* Dormancy Maintenance status */}
        {dormancy && (
          <div className="rounded-md border border-zinc-900 bg-zinc-950/10 p-5 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Activity Status</span>
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white font-mono">
                    {dormancy.days_since_last_push} {dormancy.days_since_last_push === 1 ? "day" : "days"}
                  </p>
                  <p className="text-[10px] text-zinc-500 mt-1">Since last repository push</p>
                </div>
                <div className={`rounded px-2.5 py-1 text-[10px] font-semibold border ${getDormancyColor(dormancy.status)}`}>
                  {dormancy.status}
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3 border-t border-zinc-900/60">
              <h4 className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Maintenance Summary</h4>
              <p className="text-xs text-zinc-500 leading-relaxed">{dormancy.message}</p>
            </div>
          </div>
        )}

        {/* Developer complexity & AI score */}
        {aiInsights && (
          <div className="rounded-md border border-zinc-900 bg-zinc-950/10 p-5 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">AI Quality Score</span>
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white font-mono">{aiInsights.ai_score}/100</p>
                  <p className="text-[10px] text-zinc-500 mt-1">Complexity: <span className="font-semibold text-zinc-350">{aiInsights.complexity}</span></p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`rounded px-2.5 py-1 text-[10px] font-semibold border ${
                    aiInsights.beginner_friendly
                      ? "text-emerald-400 border-emerald-955 bg-emerald-955/20"
                      : "text-amber-400 border-amber-955 bg-amber-955/20"
                  }`}>
                    {aiInsights.beginner_friendly ? "Easy Intro" : "Complex"}
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3 border-t border-zinc-900/60">
              <h4 className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-1">AI Recommendation</h4>
              <p className="text-xs text-zinc-500 leading-relaxed truncate">{aiInsights.summary}</p>
            </div>
          </div>
        )}
      </div>

      {/* AI Detailed Insights */}
      {aiInsights && (
        <div className="rounded-md border border-zinc-900 bg-zinc-950/20 p-6">
          <div className="mb-6 border-b border-zinc-900/60 pb-4">
            <h2 className="text-xs font-semibold uppercase text-zinc-400 tracking-wider">AI Repository Deep Dive</h2>
            <p className="text-[10px] text-zinc-550 mt-0.5">Machine learning analysis and structural recommendations.</p>
          </div>

          <div className="grid gap-8 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-zinc-900">
            {/* Strengths */}
            <div className="pr-0 md:pr-4">
              <h3 className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wide mb-3">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Core Strengths
              </h3>
              <ul className="space-y-2">
                {aiInsights.strengths.map((strength, idx) => (
                  <li key={idx} className="flex gap-2 text-xs text-zinc-400 leading-relaxed">
                    <span className="text-emerald-500 shrink-0 select-none">-</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div className="pt-6 md:pt-0 pl-0 md:pl-8 pr-0 md:pr-4">
              <h3 className="flex items-center gap-1.5 text-xs font-bold text-rose-450 uppercase tracking-wide mb-3">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-450" />
                Weaknesses
              </h3>
              <ul className="space-y-2">
                {aiInsights.weaknesses.map((weakness, idx) => (
                  <li key={idx} className="flex gap-2 text-xs text-zinc-400 leading-relaxed">
                    <span className="text-rose-500 shrink-0 select-none">-</span>
                    <span>{weakness}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Suggestions */}
            <div className="pt-6 md:pt-0 pl-0 md:pl-8">
              <h3 className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 uppercase tracking-wide mb-3">
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                Action Items
              </h3>
              <ul className="space-y-2">
                {aiInsights.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex gap-2 text-xs text-zinc-400 leading-relaxed">
                    <span className="text-indigo-500 shrink-0 select-none">-</span>
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
