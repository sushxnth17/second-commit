"use client";

import { useEffect, useState } from "react";
import {
  api,
  RepositoryResponse,
  HealthResponse,
  DormancyResponse,
  AIInsightsResponse,
} from "@/lib/api";
import HandoverPage from "./HandoverPage";

interface RepoDetailsProps {
  repoId: number;
  onBack: () => void;
  onSyncSuccess: () => void;
  handoverState: "not_started" | "in_progress" | "prepared";
  developerNotes: string;
  revivalIntent: string;
  publicationState: "unpublished" | "published";
  onStateChange: (state: "not_started" | "in_progress" | "prepared") => Promise<void> | void;
  onNotesChange: (notes: string) => void;
  onRevivalIntentChange: (intent: string) => void;
  onPublicationStateChange: (status: "unpublished" | "published") => Promise<void> | void;
}

export default function RepoDetails({
  repoId,
  onBack,
  onSyncSuccess,
  handoverState,
  developerNotes,
  revivalIntent,
  publicationState,
  onStateChange,
  onNotesChange,
  onRevivalIntentChange,
  onPublicationStateChange,
}: RepoDetailsProps) {
  const [repo, setRepo] = useState<RepositoryResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dormancy, setDormancy] = useState<DormancyResponse | null>(null);
  const [aiInsights, setAIInsights] = useState<AIInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [showHandover, setShowHandover] = useState(false);

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
    if (score >= 90) return "text-semantic-healthy border border-semantic-healthy/20 bg-semantic-healthy/10";
    if (score >= 80) return "text-teal-600 border border-teal-200 bg-teal-50";
    if (score >= 70) return "text-semantic-warning border border-semantic-warning/20 bg-semantic-warning/10";
    return "text-semantic-critical border border-semantic-critical/20 bg-semantic-critical/10";
  };

  const getDormancyColor = (status: string) => {
    if (status.toLowerCase() === "active") return "text-semantic-healthy border border-semantic-healthy/20 bg-semantic-healthy/10";
    return "text-semantic-critical border border-semantic-critical/20 bg-semantic-critical/10";
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4 bg-background select-none">
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse" />
          <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse [animation-delay:0.2s]" />
          <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse [animation-delay:0.4s]" />
        </div>
        <span className="text-[10px] font-mono tracking-wider uppercase text-text-secondary">Loading codebase metrics</span>
      </div>
    );
  }

  if (error || !repo) {
    return (
      <div className="mx-auto max-w-xl px-6 py-16 text-center select-none">
        <div className="border border-semantic-critical/30 bg-semantic-critical/5 p-6 rounded-none shadow-sm">
          <h3 className="text-xs font-mono uppercase tracking-widest text-semantic-critical font-bold">Error Loading Details</h3>
          <p className="mt-2 text-xs text-text-secondary leading-relaxed">{error || "Repository details not found."}</p>
          <button
            onClick={onBack}
            className="mt-5 rounded-none border border-border-muted bg-surface-secondary px-4 py-2 text-[10px] font-mono uppercase tracking-widest text-text-secondary hover:text-text-primary hover:border-border-strong transition-all duration-150 cursor-pointer outline-none"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (showHandover && repo) {
    return (
      <HandoverPage
        repo={repo}
        health={health}
        dormancy={dormancy}
        aiInsights={aiInsights}
        onBack={() => setShowHandover(false)}
        handoverState={handoverState}
        developerNotes={developerNotes}
        revivalIntent={revivalIntent}
        publicationState={publicationState}
        onStateChange={onStateChange}
        onNotesChange={onNotesChange}
        onRevivalIntentChange={onRevivalIntentChange}
        onPublicationStateChange={onPublicationStateChange}
      />
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      {/* Back button & Action Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between mb-10 select-none">
        <div className="flex items-baseline gap-4">
          <button
            onClick={onBack}
            className="rounded-none border border-border-muted bg-surface-secondary p-1.5 text-text-secondary hover:text-text-primary hover:border-border-strong transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-3.5 w-3.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <div>
            <h1 className="text-3xl font-outfit text-text-primary font-extrabold tracking-tight">{repo.name}</h1>
            <p className="text-[10px] text-text-muted font-mono mt-1.5">{repo.full_name}</p>
          </div>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing}
          className={`flex items-center justify-center gap-2.5 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent px-4 py-2.5 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent shadow-sm hover:shadow-md ${
            syncing ? "cursor-not-allowed bg-surface-base text-text-secondary border-border-muted shadow-none" : ""
          }`}
        >
          {!syncing && (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-3.5 w-3.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          )}
          {syncing ? "Syncing..." : "Sync GitHub Data"}
        </button>
      </div>

      {/* Repo quick metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-6 border-t border-b border-border-muted mb-10 select-none">
        <div>
          <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest">GitHub Stars</span>
          <p className="text-3xl font-mono text-text-primary mt-1.5 tracking-tight font-bold">{repo.stars ?? 0}</p>
        </div>
        <div className="border-l border-border-muted pl-6">
          <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest">Forks</span>
          <p className="text-3xl font-mono text-text-primary mt-1.5 tracking-tight font-bold">{repo.forks ?? 0}</p>
        </div>
        <div className="border-l border-border-muted pl-6">
          <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest">Open Issues</span>
          <p className="text-3xl font-mono text-text-primary mt-1.5 tracking-tight font-bold">{repo.open_issues ?? 0}</p>
        </div>
        <div className="border-l border-border-muted pl-6">
          <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest">Storage Size</span>
          <p className="text-3xl font-mono text-text-primary mt-1.5 tracking-tight font-bold">
            {repo.size ? `${(repo.size / 1024).toFixed(1)} MB` : "—"}
          </p>
        </div>
      </div>

      {/* Health, Grading & Maintenance Details */}
      <div className="grid gap-8 md:grid-cols-3 mb-10">
        {/* Health score gauge */}
        {health && (
          <div className="border border-border-muted bg-surface-base p-6 flex flex-col justify-between rounded-none min-h-[195px] shadow-sm">
            <div>
              <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest select-none">Health Rating</span>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-4xl font-mono text-text-primary font-bold tracking-tighter">{health.health_score}/100</p>
                  <p className="text-[10px] text-text-secondary mt-1.5 font-mono select-none">Grade: <span className="font-bold text-text-primary">{health.grade}</span></p>
                </div>
                <div className={`h-11 w-11 rounded-none border flex items-center justify-center text-sm font-mono font-bold select-none ${getScoreColor(health.health_score)}`}>
                  {health.grade}
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3.5 border-t border-border-muted">
              <h4 className="text-[9px] font-mono font-bold text-text-secondary uppercase tracking-widest mb-1.5 select-none">Health Summary</h4>
              <p className="text-xs text-text-secondary leading-relaxed font-sans">{health.summary}</p>
            </div>
          </div>
        )}

        {/* Dormancy Maintenance status */}
        {dormancy && (
          <div className="border border-border-muted bg-surface-base p-6 flex flex-col justify-between rounded-none min-h-[195px] shadow-sm">
            <div>
              <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest select-none">Activity Status</span>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-4xl font-mono text-text-primary font-bold tracking-tighter">
                    {dormancy.days_since_last_push} {dormancy.days_since_last_push === 1 ? "day" : "days"}
                  </p>
                  <p className="text-[10px] text-text-secondary mt-1.5 font-sans select-none">Since last repository push</p>
                </div>
                <div className={`rounded-none px-2.5 py-1 text-[10px] font-mono uppercase font-bold border select-none ${getDormancyColor(dormancy.status)}`}>
                  {dormancy.status}
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3.5 border-t border-border-muted">
              <h4 className="text-[9px] font-mono font-bold text-text-secondary uppercase tracking-widest mb-1.5 select-none">Maintenance Summary</h4>
              <p className="text-xs text-text-secondary leading-relaxed font-sans">{dormancy.message}</p>
            </div>
          </div>
        )}

        {/* Developer complexity & AI score */}
        {aiInsights && (
          <div className="border border-border-muted bg-surface-base p-6 flex flex-col justify-between rounded-none min-h-[195px] shadow-sm">
            <div>
              <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest select-none">AI Quality Score</span>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-4xl font-mono text-text-primary font-bold tracking-tighter">{aiInsights.ai_score}/100</p>
                  <p className="text-[10px] text-text-secondary mt-1.5 font-sans select-none">Complexity: <span className="font-bold text-text-primary font-mono">{aiInsights.complexity}</span></p>
                </div>
                <div className="flex flex-col items-end gap-1 select-none">
                  <span className={`rounded-none px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider font-bold border ${
                    aiInsights.beginner_friendly
                      ? "text-semantic-healthy border-semantic-healthy/20 bg-semantic-healthy/10"
                      : "text-semantic-warning border-semantic-warning/20 bg-semantic-warning/10"
                  }`}>
                    {aiInsights.beginner_friendly ? "Intro friendly" : "Complex"}
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-5 pt-3.5 border-t border-border-muted">
              <h4 className="text-[9px] font-mono font-bold text-text-secondary uppercase tracking-widest mb-1.5 select-none">AI Recommendation</h4>
              <p className="text-xs text-text-secondary leading-relaxed truncate font-sans">{aiInsights.summary}</p>
            </div>
          </div>
        )}

        {!aiInsights && !aiLoading && !aiError && (
          <div className="border border-border-muted bg-surface-base p-6 flex flex-col justify-between rounded-none min-h-[195px] shadow-sm">
            <div>
              <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest select-none">AI Repository Analysis</span>
              <p className="mt-3 text-xs text-text-secondary leading-relaxed font-sans">
                Generate an AI-powered analysis of this repository, including strengths, weaknesses, and actionable recommendations.
              </p>
            </div>
            <button
              onClick={handleGenerateAI}
              className="mt-5 w-full rounded-none border border-border-muted bg-surface-secondary px-4 py-2.5 text-[10px] font-mono uppercase tracking-widest text-text-secondary hover:text-text-primary hover:border-border-strong hover:bg-surface-base transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent shadow-sm"
            >
              Generate AI Analysis
            </button>
          </div>
        )}

        {aiLoading && (
          <div className="border border-border-muted bg-surface-base p-6 flex flex-col justify-center items-center rounded-none min-h-[195px] text-center select-none shadow-sm">
            <div className="flex items-center gap-1.5 mb-3">
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse" />
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.2s]" />
              <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.4s]" />
            </div>
            <span className="text-xs font-bold text-text-primary">Analyzing codebase...</span>
            <span className="text-[9px] text-text-muted mt-1.5 font-mono uppercase tracking-wider">Requesting LLM assessment</span>
          </div>
        )}

        {aiError && (
          <div className="border border-border-muted bg-surface-base p-6 flex flex-col justify-between rounded-none min-h-[195px] shadow-sm">
            <div>
              <span className="text-[10px] font-mono font-bold text-semantic-critical uppercase tracking-widest select-none">AI Analysis Failed</span>
              <p className="mt-3 text-xs text-semantic-critical/80 leading-relaxed line-clamp-3">
                {aiError}
              </p>
            </div>
            <button
              onClick={handleGenerateAI}
              className="mt-5 w-full rounded-none border border-semantic-critical/30 bg-semantic-critical/5 px-4 py-2.5 text-[10px] font-mono uppercase tracking-widest text-semantic-critical hover:bg-semantic-critical/10 transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
            >
              Retry AI Analysis
            </button>
          </div>
        )}
      </div>

      {/* AI Detailed Insights */}
      {aiInsights && (
        <div className="border border-border-muted bg-surface-base p-8 rounded-none shadow-sm">
          <div className="mb-8 border-b border-border-muted pb-5 select-none">
            <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-brand-accent">✦ AI INSIGHT</h2>
            <p className="text-[10px] text-text-secondary mt-1 font-sans">Machine learning analysis and structural recommendations.</p>
          </div>

          <div className="grid gap-10 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-border-muted">
            {/* Core Strengths */}
            <div className="pr-0 md:pr-6">
              <h3 className="flex items-center gap-2 text-[10px] font-mono font-bold text-semantic-healthy uppercase tracking-widest mb-5 select-none">
                <span className="h-1.5 w-1.5 rounded-full bg-semantic-healthy" />
                Core Strengths
              </h3>
              <ul className="space-y-3.5">
                {aiInsights.strengths.map((strength, idx) => (
                  <li key={idx} className="flex gap-2.5 text-xs text-text-secondary leading-relaxed font-sans">
                    <span className="text-brand-accent shrink-0 select-none font-mono font-bold">-</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div className="pt-6 md:pt-0 pl-0 md:pl-8 pr-0 md:pr-6">
              <h3 className="flex items-center gap-2 text-[10px] font-mono font-bold text-semantic-critical uppercase tracking-widest mb-5 select-none">
                <span className="h-1.5 w-1.5 rounded-full bg-semantic-critical" />
                Weaknesses
              </h3>
              <ul className="space-y-3.5">
                {aiInsights.weaknesses.map((weakness, idx) => (
                  <li key={idx} className="flex gap-2.5 text-xs text-text-secondary leading-relaxed font-sans">
                    <span className="text-brand-accent shrink-0 select-none font-mono font-bold">-</span>
                    <span>{weakness}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Suggestions */}
            <div className="pt-6 md:pt-0 pl-0 md:pl-8">
              <h3 className="flex items-center gap-2 text-[10px] font-mono font-bold text-text-primary uppercase tracking-widest mb-5 select-none">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />
                Action Items
              </h3>
              <ul className="space-y-3.5">
                {aiInsights.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex gap-2.5 text-xs text-text-secondary leading-relaxed font-sans">
                    <span className="text-brand-accent shrink-0 select-none font-mono font-bold">-</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Handover Card */}
      <div className="border border-border-muted bg-surface-base p-8 mb-10 shadow-sm relative overflow-hidden select-none mt-10">
        {/* Subtle background decoration to emphasize the feature */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-[radial-gradient(circle_at_100%_0%,rgba(232,121,42,0.04)_0%,transparent_70%)] pointer-events-none" />

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 relative z-10">
          <div className="flex-1">
            <span className="text-[10px] font-mono tracking-widest uppercase text-brand-accent font-bold block mb-2">HANDOVER</span>
            <h3 className="text-lg font-outfit text-text-primary font-bold mb-2">
              Prepare this repository for the next developer.
            </h3>
            <p className="text-xs text-text-secondary font-sans leading-relaxed max-w-2xl">
              Create a structured handover that explains the project, important areas, current state, and things the next developer should know.
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-3">
            {handoverState === "prepared" ? (
              <div className="flex items-center gap-2 text-semantic-healthy font-mono text-[10px] uppercase font-bold border border-semantic-healthy/20 bg-semantic-healthy/5 px-3 py-1.5 rounded-none">
                <span className="h-1.5 w-1.5 rounded-full bg-semantic-healthy" />
                Prepared
              </div>
            ) : handoverState === "in_progress" ? (
              <div className="flex items-center gap-2 text-brand-accent font-mono text-[10px] uppercase font-bold border border-brand-accent/20 bg-brand-accent/5 px-3 py-1.5 rounded-none animate-pulse">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />
                In Progress
              </div>
            ) : null}

            <button
              onClick={() => setShowHandover(true)}
              className="flex items-center justify-center gap-2 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent px-5 py-3 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
            >
              {handoverState === "not_started" ? "Prepare Handover" : "View Handover"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
