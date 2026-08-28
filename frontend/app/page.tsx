"use client";

import { useEffect, useState } from "react";
import { api, UserSummary, RepositorySummary, AnalyticsResponse } from "@/lib/api";
import Navbar from "./components/Navbar";
import Dashboard from "./components/Dashboard";
import RepoDetails from "./components/RepoDetails";
import ImportModal from "./components/ImportModal";

export default function Home() {
  const [user, setUser] = useState<UserSummary | null>(null);
  const [repos, setRepos] = useState<RepositorySummary[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "analytics">("dashboard");
  const [selectedRepoId, setSelectedRepoId] = useState<number | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Local handover states
  const [handoverStates, setHandoverStates] = useState<Record<number, "not_started" | "in_progress" | "prepared">>({});
  const [developerNotes, setDeveloperNotes] = useState<Record<number, string>>({});
  const [revivalIntents, setRevivalIntents] = useState<Record<number, string>>({});
  const [publicationStates, setPublicationStates] = useState<Record<number, "unpublished" | "published">>({});

  // Load handover state from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedStates = localStorage.getItem("secondcommit_handover_states");
      const storedNotes = localStorage.getItem("secondcommit_developer_notes");
      const storedIntents = localStorage.getItem("secondcommit_revival_intents");
      const storedPublications = localStorage.getItem("secondcommit_publication_states");
      if (storedStates) {
        try {
          setHandoverStates(JSON.parse(storedStates));
        } catch (e) {
          console.error("Failed to parse handover states:", e);
        }
      }
      if (storedNotes) {
        try {
          setDeveloperNotes(JSON.parse(storedNotes));
        } catch (e) {
          console.error("Failed to parse developer notes:", e);
        }
      }
      if (storedIntents) {
        try {
          setRevivalIntents(JSON.parse(storedIntents));
        } catch (e) {
          console.error("Failed to parse revival intents:", e);
        }
      }
      if (storedPublications) {
        try {
          setPublicationStates(JSON.parse(storedPublications));
        } catch (e) {
          console.error("Failed to parse publication states:", e);
        }
      }
    }
  }, []);

  const updateHandoverState = (repoId: number, state: "not_started" | "in_progress" | "prepared") => {
    const updated = { ...handoverStates, [repoId]: state };
    setHandoverStates(updated);
    localStorage.setItem("secondcommit_handover_states", JSON.stringify(updated));

    // When editing (state === in_progress), set publication state back to unpublished
    if (state === "in_progress") {
      setPublicationStates((prev) => {
        const next = { ...prev, [repoId]: "unpublished" as const };
        localStorage.setItem("secondcommit_publication_states", JSON.stringify(next));
        return next;
      });
    }
  };

  const updateDeveloperNotes = (repoId: number, notes: string) => {
    const updated = { ...developerNotes, [repoId]: notes };
    setDeveloperNotes(updated);
    localStorage.setItem("secondcommit_developer_notes", JSON.stringify(updated));
  };

  const updateRevivalIntent = (repoId: number, intent: string) => {
    const updated = { ...revivalIntents, [repoId]: intent };
    setRevivalIntents(updated);
    localStorage.setItem("secondcommit_revival_intents", JSON.stringify(updated));
  };

  const updatePublicationState = (repoId: number, status: "unpublished" | "published") => {
    const updated = { ...publicationStates, [repoId]: status };
    setPublicationStates(updated);
    localStorage.setItem("secondcommit_publication_states", JSON.stringify(updated));
  };

  // Authenticate user on mount
  const checkAuth = async () => {
    try {
      const res = await api.getDashboard();
      setUser(res.user);
      setRepos(res.repositories);
      
      const analyticsRes = await api.getAnalytics();
      setAnalytics(analyticsRes);
    } catch (err: any) {
      if (err.message !== "UNAUTHORIZED") {
        setError(err.message || "Failed to check authentication.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogin = () => {
    const loginUrl = api.getLoginUrl();
    const width = 600;
    const height = 750;
    const left = window.screen.width / 2 - width / 2;
    const top = window.screen.height / 2 - height / 2;

    const popup = window.open(
      loginUrl,
      "github-oauth",
      `width=${width},height=${height},left=${left},top=${top},status=no,resizable=yes`
    );

    if (popup) {
      const timer = setInterval(async () => {
        if (popup.closed) {
          clearInterval(timer);
          setLoading(true);
          await checkAuth();
        }
      }, 500);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err: any) {
      console.error("Failed to log out from server:", err);
    }
    // Clear local session state
    setUser(null);
    setRepos([]);
    setAnalytics(null);
    setSelectedRepoId(null);
    setActiveTab("dashboard");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background text-text-primary font-sans select-none">
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse" />
          <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse [animation-delay:0.2s]" />
          <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse [animation-delay:0.4s]" />
        </div>
        <span className="text-[10px] font-mono tracking-wider uppercase text-text-secondary">Securing environment</span>
      </div>
    );
  }

  // Unauthenticated Landing View
  if (!user) {
    return (
      <div className="flex min-h-screen flex-col bg-background text-text-primary font-sans selection:bg-[#E8792A]/15 selection:text-text-primary relative overflow-hidden">
        {/* Radial gradient wash to mirror Zoren's hero background wash */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_35%,rgba(232,121,42,0.08)_0%,transparent_60%)] pointer-events-none z-0" />

        <main className="flex flex-1 flex-col items-center justify-center px-6 py-12 sm:px-12 lg:px-16 relative z-10">
          <div className="w-full max-w-lg">
            {/* Header / Brand */}
            <div className="flex flex-col items-center mb-10 text-center">
              {/* Zoren-style pill dot */}
              <div className="inline-flex items-center gap-2 bg-surface-secondary border border-border-strong px-4 py-1.5 rounded-full mb-8 select-none">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-accent animate-pulse" />
                <span className="text-[10px] font-mono tracking-widest uppercase text-text-secondary font-bold">
                  Codebase · Health · Analysis
                </span>
              </div>

              <div className="font-outfit text-base font-extrabold tracking-wider text-text-primary uppercase mb-6 select-none">
                SecondCommit
              </div>
              
              <h1 className="text-4xl sm:text-5xl font-outfit text-text-primary tracking-tight leading-tight max-w-md font-extrabold">
                Your codebase has a <span className="bg-gradient-to-r from-[#E8792A] to-[#F2A654] bg-clip-text text-transparent">story.</span>
              </h1>
              <p className="mt-4 text-xs font-sans text-text-secondary max-w-md leading-relaxed">
                A premier developer intelligence workspace delivering rigorous repository grading, activity metrics, and structural recommendations.
              </p>
            </div>

            {/* Login Box / Call to action */}
            <div className="border border-border-muted bg-surface-base p-8 text-center shadow-sm">
              <button
                onClick={handleLogin}
                className="flex w-full items-center justify-center gap-2.5 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent hover:-translate-y-0.5 px-4 py-3.5 text-[10px] font-mono uppercase font-bold tracking-widest transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
              >
                <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                Connect with GitHub
              </button>
              <p className="mt-4 text-[9px] font-mono text-text-secondary leading-normal select-none">
                Requires read access to public and private repository metadata.
              </p>
            </div>

            {/* Product Preview Card */}
            <div className="mt-8 border border-border-muted bg-surface-base p-6 text-left select-none shadow-sm hover:border-brand-accent hover:shadow-lg transition-all duration-300">
              <div className="flex items-center justify-between border-b border-border-muted pb-4 mb-4">
                <div>
                  <span className="text-[8px] font-mono tracking-widest uppercase text-text-muted font-bold block">✦ CODEBASE ANALYSIS</span>
                  <span className="font-outfit text-base font-extrabold text-text-primary mt-1 block">strix-dashboard</span>
                </div>
                <span className="rounded-none border border-semantic-critical/30 bg-semantic-critical/10 text-semantic-critical px-2 py-0.5 text-[9px] font-mono uppercase font-bold">
                  GRADE D
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <span className="text-[8px] font-mono uppercase tracking-widest text-text-muted font-bold block">Health Score</span>
                  <span className="text-xl font-mono font-bold text-text-primary mt-1 block">60 <span className="text-xs text-text-secondary font-normal">/ 100</span></span>
                </div>
                <div className="border-l border-border-muted pl-4">
                  <span className="text-[8px] font-mono uppercase tracking-widest text-text-muted font-bold block">Status</span>
                  <span className="inline-flex items-center gap-1.5 mt-2 text-[9px] font-mono uppercase text-semantic-critical font-bold">
                    <span className="h-1.5 w-1.5 rounded-full bg-semantic-critical animate-pulse" />
                    CRITICAL
                  </span>
                </div>
                <div className="border-l border-border-muted pl-4">
                  <span className="text-[8px] font-mono uppercase tracking-widest text-text-muted font-bold block">Dormancy</span>
                  <span className="text-xs font-mono font-bold text-text-primary mt-2 block">95d ago</span>
                </div>
              </div>

              <div className="space-y-2.5 pt-4 border-t border-border-muted text-[9px] font-mono text-text-secondary">
                <div className="flex justify-between items-center">
                  <span className="tracking-wide">CODEBASE DOCUMENTATION CHECK</span>
                  <span className="text-semantic-critical uppercase font-bold">INCOMPLETE</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="tracking-wide">RECENT PUSH & COMMIT ACTIVITY</span>
                  <span className="text-semantic-warning uppercase font-bold">INACTIVE</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="tracking-wide">DIRECTORY & FILE STRUCTURE</span>
                  <span className="text-semantic-healthy uppercase font-bold">HEALTHY</span>
                </div>
              </div>
            </div>

            {/* Feature List (Sleek Flat Table) */}
            <div className="mt-12 border-t border-border-muted divide-y divide-border-muted">
              <div className="py-6 flex gap-6 text-left">
                <span className="text-xs font-mono text-text-secondary font-bold select-none">01</span>
                <div>
                  <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest block">Automated Grading</span>
                  <p className="mt-1.5 text-xs text-text-secondary leading-relaxed font-sans">
                    Compute health grades (A to D) based on documentation, activity, and codebase structure.
                  </p>
                </div>
              </div>
              <div className="py-6 flex gap-6 text-left">
                <span className="text-xs font-mono text-text-secondary font-bold select-none">02</span>
                <div>
                  <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest block">Dormancy Tracking</span>
                  <p className="mt-1.5 text-xs text-text-secondary leading-relaxed font-sans">
                    Monitor repository freshness, push cycles, and get flagged for inactive maintenance.
                  </p>
                </div>
              </div>
              <div className="py-6 flex gap-6 text-left">
                <span className="text-xs font-mono text-text-secondary font-bold select-none">03</span>
                <div>
                  <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest block">AI Recommendations</span>
                  <p className="mt-1.5 text-xs text-text-secondary leading-relaxed font-sans">
                    Analyze repository metadata and receive actionable suggestions for improvement.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Authenticated Views Orchestrator
  return (
    <div className="flex min-h-screen flex-col bg-background text-text-primary font-sans selection:bg-[#E8792A]/15 selection:text-text-primary">
      <Navbar
        user={user}
        activeTab={activeTab}
        setActiveTab={(tab: "dashboard" | "analytics") => {
          setActiveTab(tab);
          setSelectedRepoId(null); // Clear selected repo when switching tabs
        }}
        onLogout={handleLogout}
      />

      <main className="flex-1">
        {activeTab === "dashboard" ? (
          selectedRepoId !== null ? (
            <RepoDetails
              repoId={selectedRepoId}
              onBack={() => setSelectedRepoId(null)}
              onSyncSuccess={checkAuth}
              handoverState={handoverStates[selectedRepoId] || "not_started"}
              developerNotes={developerNotes[selectedRepoId] || ""}
              revivalIntent={revivalIntents[selectedRepoId] || ""}
              publicationState={publicationStates[selectedRepoId] || "unpublished"}
              onStateChange={(state) => updateHandoverState(selectedRepoId, state)}
              onNotesChange={(notes) => updateDeveloperNotes(selectedRepoId, notes)}
              onRevivalIntentChange={(intent) => updateRevivalIntent(selectedRepoId, intent)}
              onPublicationStateChange={(status) => updatePublicationState(selectedRepoId, status)}
            />
          ) : (
            <Dashboard
              user={user}
              repos={repos}
              analytics={analytics}
              onImportClick={() => setShowImportModal(true)}
              onSelectRepo={setSelectedRepoId}
              onSyncSuccess={checkAuth}
            />
          )
        ) : (
          /* Analytics Tab Panel */
          <div className="mx-auto max-w-5xl px-6 py-10 select-none">
            <div className="mb-8 border-b border-border-muted pb-5">
              <h1 className="text-2xl font-outfit text-text-primary font-bold tracking-tight">Developer Analytics</h1>
              <p className="mt-1 text-xs text-text-secondary font-sans">Aggregate statistics and code metrics from your portfolio.</p>
            </div>

            {analytics ? (
              <div className="border border-border-muted bg-surface-base p-8 rounded-none shadow-sm">
                <div className="grid gap-10 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-border-muted">
                  {/* Language & Popularity */}
                  <div className="pr-0 md:pr-8">
                    <h3 className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest mb-5">Language & Popularity</h3>
                    
                    <div className="divide-y divide-border-muted">
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-text-secondary">Primary Language</span>
                        <span className="rounded-none bg-surface-secondary border border-border-muted px-2 py-0.5 text-[9px] font-mono font-bold text-text-primary font-mono">
                          {analytics.primary_language || "None detected"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-text-secondary">Most Popular Repository</span>
                        <span className="text-xs font-mono font-bold text-text-primary truncate max-w-[220px]">
                          {analytics.most_popular_repository || "N/A"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-text-secondary">Most Active Repository</span>
                        <span className="text-xs font-mono font-bold text-text-primary truncate max-w-[220px]">
                          {analytics.most_active_repository || "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Maintenance Index */}
                  <div className="pt-6 md:pt-0 pl-0 md:pl-10">
                    <h3 className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest mb-5">Maintenance Metrics</h3>
                    
                    <div className="divide-y divide-border-muted">
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-text-secondary">Active Repositories</span>
                        <span className="text-xs font-mono text-semantic-healthy tracking-tight font-bold">
                          {analytics.active_repositories}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-text-secondary">Dormant Repositories</span>
                        <span className="text-xs font-mono text-semantic-critical tracking-tight font-bold">
                          {analytics.dormant_repositories}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-text-secondary">Average Health Score</span>
                        <span className="text-xs font-mono text-text-primary tracking-tight font-bold">
                          {analytics.average_health_score !== null && analytics.average_health_score !== undefined
                            ? `${Math.round(analytics.average_health_score)}/100`
                            : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="border border-dashed border-border-muted p-12 text-center rounded-none bg-surface-base">
                <p className="text-xs font-mono uppercase tracking-wider text-text-secondary">Analytics data is not loaded yet.</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Import Modal Overlay */}
      {showImportModal && (
        <ImportModal
          onClose={() => setShowImportModal(false)}
          onImportSuccess={() => {
            checkAuth(); // Refresh dashboard repo list
          }}
        />
      )}
    </div>
  );
}
