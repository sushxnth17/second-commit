"use client";

import { useEffect, useState } from "react";
import {
  api,
  RepositoryResponse,
  HealthResponse,
  DormancyResponse,
  AIInsightsResponse,
  RevivalRequestResponse,
  RevivalTeamResponse,
} from "@/lib/api";
import HandoverPage from "./HandoverPage";
import RevivalTeam from "./RevivalTeam";

interface RepoDetailsProps {
  repoId: number;
  onBack: () => void;
  onSyncSuccess: () => void;
  isOwner: boolean;
}

export default function RepoDetails({
  repoId,
  onBack,
  onSyncSuccess,
  isOwner,
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

  // Local brief and publication states
  const [handoverState, setHandoverState] = useState<"not_started" | "in_progress" | "prepared">("not_started");
  const [developerNotes, setDeveloperNotes] = useState("");
  const [revivalIntent, setRevivalIntent] = useState("");
  const [publicationState, setPublicationState] = useState<"unpublished" | "published">("unpublished");

  // Revival request states
  const [pendingRequest, setPendingRequest] = useState<RevivalRequestResponse | null>(null);
  const [requestMessage, setRequestMessage] = useState("");
  const [requestingState, setRequestingState] = useState<"idle" | "sending" | "success" | "already_requested" | "error">("idle");
  const [requestError, setRequestError] = useState<string | null>(null);
  const [showRequestForm, setShowRequestForm] = useState(false);

  // Owner requests list states
  const [incomingRequests, setIncomingRequests] = useState<RevivalRequestResponse[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(false);
  const [requestsError, setRequestsError] = useState<string | null>(null);

  // State to track decision confirmation: { requestId: number, action: "approve" | "reject" | null }
  const [decisionConfirm, setDecisionConfirm] = useState<{ requestId: number; action: "approve" | "reject" | null }>({
    requestId: 0,
    action: null,
  });
  // Revival team states
  const [team, setTeam] = useState<RevivalTeamResponse | null>(null);
  const [loadingTeam, setLoadingTeam] = useState(false);
  const [teamError, setTeamError] = useState<string | null>(null);

  const fetchTeam = async () => {
    setLoadingTeam(true);
    setTeamError(null);
    try {
      const t = await api.getRevivalTeam(repoId);
      setTeam(t);
    } catch (err: any) {
      setTeamError(err.message || "Failed to load revival team.");
    } finally {
      setLoadingTeam(false);
    }
  };

  // State to track currently updating requests: { [requestId: number]: "approving" | "rejecting" }
  const [updatingRequests, setUpdatingRequests] = useState<{ [key: number]: "approving" | "rejecting" }>({});

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    setAIInsights(null);
    setAiLoading(false);
    setAiError(null);
    try {
      const [r, h, d, brief, req] = await Promise.all([
        api.getRepository(repoId),
        api.getRepositoryHealth(repoId),
        api.getRepositoryDormancy(repoId),
        api.getHandover(repoId).catch(() => null),
        api.getMyRevivalRequest(repoId).catch(() => null),
      ]);
      setRepo(r);
      setHealth(h);
      setDormancy(d);
      setPublicationState(r.published ? "published" : "unpublished");
      if (brief) {
        setHandoverState(brief.status === "prepared" ? "prepared" : "in_progress");
        setDeveloperNotes(brief.developer_notes);
        setRevivalIntent(brief.revival_intent);
      } else {
        setHandoverState("not_started");
        setDeveloperNotes("");
        setRevivalIntent("");
      }
      setPendingRequest(req);
      if (req) {
        setRequestingState("already_requested");
      } else {
        setRequestingState("idle");
      }

      if (isOwner) {
        setLoadingRequests(true);
        setRequestsError(null);
        try {
          const reqs = await api.getRevivalRequests(repoId);
          setIncomingRequests(reqs);
        } catch (err: any) {
          setRequestsError(err.message || "Failed to load revival requests.");
        } finally {
          setLoadingRequests(false);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch repository details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchTeam();
  }, [repoId]);

  const handleNotesChange = async (notes: string) => {
    setDeveloperNotes(notes);
    try {
      await api.saveHandover(repoId, {
        developer_notes: notes,
        revival_intent: revivalIntent,
        status: "draft",
      });
    } catch (err) {
      console.error("Failed to save developer notes:", err);
    }
  };

  const handleRevivalIntentChange = async (intent: string) => {
    setRevivalIntent(intent);
    try {
      await api.saveHandover(repoId, {
        developer_notes: developerNotes,
        revival_intent: intent,
        status: "draft",
      });
    } catch (err) {
      console.error("Failed to save revival intent:", err);
    }
  };

  const handleStateChange = async (state: "not_started" | "in_progress" | "prepared") => {
    try {
      if (state === "in_progress") {
        if (handoverState === "prepared") {
          await api.unpublishRepository(repoId);
          setPublicationState("unpublished");
        }
        await api.saveHandover(repoId, {
          developer_notes: developerNotes,
          revival_intent: revivalIntent,
          status: "draft",
        });
        setHandoverState("in_progress");
      } else if (state === "prepared") {
        await api.saveHandover(repoId, {
          developer_notes: developerNotes,
          revival_intent: revivalIntent,
          status: "prepared",
        });
        setHandoverState("prepared");
      } else if (state === "not_started") {
        await api.deleteHandover(repoId);
        setHandoverState("not_started");
        setDeveloperNotes("");
        setRevivalIntent("");
      }
    } catch (err: any) {
      console.error("Failed to update handover state:", err);
      throw err;
    }
  };

  const handlePublicationStateChange = async (status: "unpublished" | "published") => {
    try {
      if (status === "published") {
        await api.publishRepository(repoId);
      } else {
        await api.unpublishRepository(repoId);
      }
      setPublicationState(status);
    } catch (err: any) {
      console.error("Failed to update publication state:", err);
      throw err;
    }
  };

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

  const handleSendRevivalRequest = async (message: string) => {
    setRequestingState("sending");
    setRequestError(null);
    try {
      const res = await api.createRevivalRequest(repoId, message);
      setPendingRequest(res);
      setRequestingState("success");
      setShowRequestForm(false);
    } catch (err: any) {
      setRequestError(err.message || "Failed to submit revival request.");
      setRequestingState("error");
    }
  };

  const handleApproveRequest = async (requestId: number) => {
    setUpdatingRequests((prev) => ({ ...prev, [requestId]: "approving" }));
    setDecisionConfirm({ requestId: 0, action: null });
    try {
      const updated = await api.approveRevivalRequest(repoId, requestId);
      setIncomingRequests((prev) =>
        prev.map((req) => (req.id === requestId ? updated : req))
      );
      fetchTeam();
    } catch (err: any) {
      alert(err.message || "Failed to approve request.");
    } finally {
      setUpdatingRequests((prev) => {
        const copy = { ...prev };
        delete copy[requestId];
        return copy;
      });
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    setUpdatingRequests((prev) => ({ ...prev, [requestId]: "rejecting" }));
    setDecisionConfirm({ requestId: 0, action: null });
    try {
      const updated = await api.rejectRevivalRequest(repoId, requestId);
      setIncomingRequests((prev) =>
        prev.map((req) => (req.id === requestId ? updated : req))
      );
    } catch (err: any) {
      alert(err.message || "Failed to reject request.");
    } finally {
      setUpdatingRequests((prev) => {
        const copy = { ...prev };
        delete copy[requestId];
        return copy;
      });
    }
  };

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
        onStateChange={handleStateChange}
        onNotesChange={handleNotesChange}
        onRevivalIntentChange={handleRevivalIntentChange}
        onPublicationStateChange={handlePublicationStateChange}
        isOwner={isOwner}
        pendingRequest={pendingRequest}
        requestingState={requestingState}
        requestError={requestError}
        onSendRevivalRequest={handleSendRevivalRequest}
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

        {isOwner && (
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
        )}
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

        <div className="flex flex-col gap-6 relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            <div className="flex-1">
              <span className="text-[10px] font-mono tracking-widest uppercase text-brand-accent font-bold block mb-2">
                {isOwner ? "HANDOVER" : "REVIVAL BRIEF"}
              </span>
              <h3 className="text-lg font-outfit text-text-primary font-bold mb-2">
                {isOwner ? "Prepare this repository for the next developer." : "Handover context from the owner."}
              </h3>
              <p className="text-xs text-text-secondary font-sans leading-relaxed max-w-2xl">
                {isOwner
                  ? "Create a structured handover that explains the project, important areas, current state, and things the next developer should know."
                  : "Read the custom developer notes and revival intent to understand what you are inheriting."}
              </p>
            </div>

            <div className="shrink-0 flex flex-wrap items-center gap-3">
              {isOwner && (
                <>
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
                </>
              )}

              <button
                onClick={() => setShowHandover(true)}
                className={`flex items-center justify-center gap-2 rounded-none px-5 py-3 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-brand-accent ${
                  isOwner
                    ? "bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent hover:shadow-md"
                    : "bg-surface-secondary border border-border-strong text-text-primary hover:bg-surface-base"
                }`}
              >
                {isOwner
                  ? handoverState === "not_started" ? "Prepare Handover" : "View Handover"
                  : "Read Revival Brief"}
              </button>

              {/* Request to Revive button for non-owners */}
              {!isOwner && repo.published && (
                <>
                  {pendingRequest ? (
                    <div className={`flex items-center justify-center gap-2 rounded-none border px-5 py-3 text-[10px] font-mono uppercase font-bold select-none ${
                      pendingRequest.status === "approved"
                        ? "border-semantic-healthy/20 bg-semantic-healthy/5 text-semantic-healthy"
                        : pendingRequest.status === "rejected"
                        ? "border-semantic-critical/20 bg-semantic-critical/5 text-semantic-critical"
                        : "border-brand-accent/20 bg-brand-accent/5 text-brand-accent"
                    }`}>
                      {pendingRequest.status === "approved"
                        ? "REVIVAL REQUEST APPROVED"
                        : pendingRequest.status === "rejected"
                        ? "REVIVAL REQUEST REJECTED"
                        : "REVIVAL REQUEST PENDING"}
                    </div>
                  ) : requestingState === "success" ? (
                    <div className="flex items-center justify-center gap-2 rounded-none border border-semantic-healthy/20 bg-semantic-healthy/5 text-semantic-healthy px-5 py-3 text-[10px] font-mono uppercase font-bold select-none">
                      REVIVAL REQUEST SENT
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowRequestForm(!showRequestForm)}
                      className="flex items-center justify-center gap-2 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent px-5 py-3 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
                    >
                      {showRequestForm ? "Cancel Request" : "REQUEST TO REVIVE"}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Simple Revival Request Form */}
          {!isOwner && repo.published && showRequestForm && (
            <div className="border-t border-border-muted pt-6 mt-4 select-text animate-fade-in">
              <h4 className="text-xs font-mono uppercase tracking-widest text-text-primary font-bold mb-3">
                REQUEST TO REVIVE
              </h4>
              <p className="text-xs text-text-secondary mb-4">
                Why are you interested in this project?
              </p>

              {requestError && (
                <div className="mb-4 p-3 border border-semantic-critical/20 bg-semantic-critical/5 text-semantic-critical font-mono text-[11px] leading-relaxed">
                  {requestError}
                </div>
              )}

              <div className="space-y-4">
                <textarea
                  value={requestMessage}
                  onChange={(e) => setRequestMessage(e.target.value.slice(0, 1000))}
                  placeholder="I've worked with React and FastAPI before and would like to help continue this project..."
                  rows={4}
                  className="w-full p-3 text-xs font-sans border border-border-strong bg-surface-secondary text-text-primary placeholder:text-text-muted focus:border-brand-accent focus:outline-none transition-all duration-150 resize-y rounded-none"
                  disabled={requestingState === "sending"}
                />
                <div className="flex justify-between items-center select-none">
                  <span className="text-[9px] font-mono text-text-muted">
                    {requestMessage.length}/1000 characters
                  </span>
                  <button
                    onClick={() => handleSendRevivalRequest(requestMessage)}
                    disabled={requestingState === "sending"}
                    className="flex items-center justify-center gap-2 rounded-none bg-brand-accent border border-brand-accent text-white hover:bg-text-primary hover:border-text-primary px-5 py-3 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md outline-none focus-visible:ring-1 focus-visible:ring-brand-accent disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {requestingState === "sending" ? "SENDING..." : "SEND REVIVAL REQUEST"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Developer request status details */}
          {!isOwner && repo.published && pendingRequest && (
            <div className={`border-t border-border-muted pt-4 mt-2 select-text text-xs font-sans leading-relaxed flex items-center gap-2 animate-fade-in ${
              pendingRequest.status === "approved"
                ? "text-semantic-healthy"
                : pendingRequest.status === "rejected"
                ? "text-semantic-critical"
                : "text-brand-accent"
            }`}>
              {pendingRequest.status === "approved" ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4.5 w-4.5 text-semantic-healthy">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Your request to revive this project has been approved by the owner.</span>
                </>
              ) : pendingRequest.status === "rejected" ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4.5 w-4.5 text-semantic-critical">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Your request to revive this project was declined by the owner.</span>
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4.5 w-4.5 text-brand-accent">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Your request is currently awaiting review by the owner.</span>
                </>
              )}
            </div>
          )}

          {!isOwner && repo.published && !pendingRequest && requestingState === "success" && (
            <div className="border-t border-border-muted pt-4 mt-2 select-text text-xs text-semantic-healthy font-sans leading-relaxed flex items-center gap-2 animate-fade-in">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4.5 w-4.5 text-semantic-healthy">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Your request to revive this project has been submitted successfully to the owner.</span>
            </div>
          )}
        </div>
      </div>

      {/* Revival Team Section */}
      <RevivalTeam
        team={team}
        loading={loadingTeam}
        error={teamError}
        isOwner={isOwner}
        onRetry={fetchTeam}
      />

      {/* Owner-only Revival Requests Section */}
      {isOwner && (
        <div className="border border-border-muted bg-surface-base p-8 mb-10 shadow-sm mt-10">
          <div className="border-b border-border-muted pb-4 mb-6 select-none flex justify-between items-baseline">
            <div>
              <span className="text-[10px] font-mono tracking-widest uppercase text-brand-accent font-bold block mb-1">
                REVIVAL REQUESTS
              </span>
              <p className="text-xs text-text-secondary font-sans leading-relaxed">
                Developers interested in continuing this project
              </p>
            </div>
            {incomingRequests.length > 0 && (
              <span className="rounded-none border border-brand-accent/30 bg-brand-accent/10 text-brand-accent px-2 py-0.5 text-[9px] font-mono uppercase font-bold">
                {incomingRequests.length} {incomingRequests.length === 1 ? "REQUEST" : "REQUESTS"}
              </span>
            )}
          </div>

          {loadingRequests ? (
            <div className="flex flex-col items-center justify-center py-10 gap-3 select-none">
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse" />
                <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.2s]" />
                <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.4s]" />
              </div>
              <span className="text-[10px] font-mono uppercase text-text-muted">Loading requests</span>
            </div>
          ) : requestsError ? (
            <div className="border border-semantic-critical/20 bg-semantic-critical/5 p-6 text-center">
              <span className="text-[10px] font-mono uppercase text-semantic-critical font-bold">Failed to load requests</span>
              <p className="text-xs text-text-secondary mt-1.5">{requestsError}</p>
            </div>
          ) : incomingRequests.length === 0 ? (
            <div className="border border-dashed border-border-strong py-10 px-6 text-center select-none bg-surface-secondary/20">
              <h4 className="text-xs font-mono uppercase tracking-widest text-text-muted font-bold">
                NO REVIVAL REQUESTS YET
              </h4>
              <p className="text-[11px] text-text-secondary font-sans mt-2 max-w-md mx-auto">
                When developers discover and request to revive the project, their requests will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {incomingRequests.map((request) => {
                const requester = request.requester;
                const requesterName = requester ? (requester.name || requester.username) : "Developer";
                const requesterAvatar = requester?.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${requesterName}`;
                const createdDate = new Date(request.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                });

                return (
                  <div key={request.id} className="border border-border-muted p-5 bg-surface-secondary/15 flex flex-col md:flex-row gap-5 items-start md:items-center justify-between animate-fade-in">
                    <div className="flex-1">
                      {/* Requester Info Header */}
                      <div className="flex items-center gap-3 mb-3 select-none">
                        <img
                          src={requesterAvatar}
                          alt={requesterName}
                          className="h-8 w-8 rounded-full border border-border-muted object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${requesterName}`;
                          }}
                        />
                        <div>
                          <strong className="text-xs font-outfit text-text-primary block font-bold">
                            {requesterName}
                          </strong>
                          {requester?.username && (
                            <span className="text-[10px] font-mono text-text-muted block">
                              @{requester.username.toLowerCase()}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Request Message */}
                      <blockquote className="text-xs text-text-secondary bg-surface-base border-l-2 border-brand-accent/50 pl-3 py-1 font-sans leading-relaxed select-text whitespace-pre-wrap">
                        {request.message || <span className="text-text-muted italic">No message attached to request.</span>}
                      </blockquote>
                    </div>

                    {/* Metadata, Status & Actions */}
                    <div className="flex flex-col items-start md:items-end gap-3 shrink-0 select-none">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider border ${
                          request.status === "approved"
                            ? "text-semantic-healthy border-semantic-healthy/20 bg-semantic-healthy/5"
                            : request.status === "rejected"
                            ? "text-semantic-critical border-semantic-critical/20 bg-semantic-critical/5"
                            : "text-brand-accent border-brand-accent/20 bg-brand-accent/5"
                        }`}>
                          {request.status}
                        </span>
                      </div>

                      <span className="text-[10px] font-mono text-text-muted">
                        Requested: {createdDate}
                      </span>

                      {/* Approve / Reject actions for pending requests */}
                      {request.status === "pending" && (
                        <div className="mt-2 flex flex-col md:flex-row gap-2 items-stretch md:items-center">
                          {decisionConfirm.requestId === request.id && decisionConfirm.action !== null ? (
                            <div className="flex flex-col gap-2 items-end border border-border-muted p-2.5 bg-surface-secondary/20">
                              <span className="text-[10px] font-sans text-text-primary">
                                {decisionConfirm.action === "approve" ? "Approve this revival request?" : "Reject this revival request?"}
                              </span>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => setDecisionConfirm({ requestId: 0, action: null })}
                                  className="px-2.5 py-1 text-[9px] font-mono uppercase tracking-wider border border-border-strong text-text-secondary bg-surface-base hover:text-text-primary cursor-pointer transition-all"
                                  disabled={updatingRequests[request.id] !== undefined}
                                >
                                  Cancel
                                </button>
                                <button
                                  onClick={() => decisionConfirm.action === "approve" ? handleApproveRequest(request.id) : handleRejectRequest(request.id)}
                                  className={`px-2.5 py-1 text-[9px] font-mono uppercase tracking-wider text-white cursor-pointer transition-all ${
                                    decisionConfirm.action === "approve"
                                      ? "bg-semantic-healthy border border-semantic-healthy hover:bg-emerald-600"
                                      : "bg-semantic-critical border border-semantic-critical hover:bg-red-600"
                                  }`}
                                  disabled={updatingRequests[request.id] !== undefined}
                                >
                                  {updatingRequests[request.id] === "approving"
                                    ? "APPROVING..."
                                    : updatingRequests[request.id] === "rejecting"
                                    ? "REJECTING..."
                                    : decisionConfirm.action === "approve"
                                    ? "APPROVE"
                                    : "REJECT"}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="flex gap-2">
                              <button
                                onClick={() => setDecisionConfirm({ requestId: request.id, action: "approve" })}
                                className="px-3 py-1.5 text-[9px] font-mono uppercase tracking-wider bg-semantic-healthy border border-semantic-healthy text-white hover:bg-emerald-600 cursor-pointer shadow-sm transition-all"
                              >
                                APPROVE
                              </button>
                              <button
                                onClick={() => setDecisionConfirm({ requestId: request.id, action: "reject" })}
                                className="px-3 py-1.5 text-[9px] font-mono uppercase tracking-wider border border-semantic-critical/20 bg-surface-base text-semantic-critical hover:bg-semantic-critical/5 cursor-pointer shadow-sm transition-all"
                              >
                                REJECT
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
