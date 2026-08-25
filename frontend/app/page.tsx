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
    // Clear local session state (session cookie is HttpOnly, so we clear UI state)
    setUser(null);
    setRepos([]);
    setAnalytics(null);
    setSelectedRepoId(null);
    setActiveTab("dashboard");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-950 text-zinc-100 font-sans">
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-1 rounded-full bg-zinc-400 animate-pulse" />
          <div className="h-1 w-1 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.2s]" />
          <div className="h-1 w-1 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.4s]" />
        </div>
        <span className="text-[10px] font-mono tracking-wider uppercase text-zinc-550">Securing environment</span>
      </div>
    );
  }

  // Unauthenticated Landing View
  if (!user) {
    return (
      <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100 font-sans selection:bg-zinc-800">
        <main className="flex flex-1 flex-col items-center justify-center px-6 py-24 sm:px-12 lg:px-16">
          <div className="w-full max-w-lg">
            {/* Header / Brand */}
            <div className="flex flex-col items-center mb-16 text-center">
              <div className="font-serif italic text-4xl font-normal tracking-wide text-zinc-200 mb-8 select-none">
                SecondCommit
              </div>
              
              <h1 className="text-5xl font-serif text-white tracking-tight leading-tight max-w-md font-light">
                Your codebase has a story.
              </h1>
              <p className="mt-5 text-sm font-sans text-zinc-400 max-w-md leading-relaxed">
                A premium developer intelligence workspace delivering rigorous repository grading, activity metrics, and structural recommendations.
              </p>
            </div>

            {/* Login Box / Call to action */}
            <div className="border border-zinc-900 bg-zinc-950/20 p-8 text-center backdrop-blur-sm">
              <button
                onClick={handleLogin}
                className="flex w-full items-center justify-center gap-2.5 rounded-none bg-zinc-100 text-zinc-950 px-4 py-3.5 text-xs font-mono uppercase tracking-wider hover:bg-white transition-colors cursor-pointer focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
              >
                <svg className="h-4 w-4 fill-current text-zinc-950" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                Connect with GitHub
              </button>
              <p className="mt-4 text-[10px] font-mono text-zinc-550 leading-normal">
                Requires read access to public and private repository metadata.
              </p>
            </div>

            {/* Feature List (Sleek Flat Table) */}
            <div className="mt-16 border-t border-zinc-900 divide-y divide-zinc-900/60">
              <div className="py-6 flex gap-6 text-left">
                <span className="text-xs font-mono text-zinc-600 font-bold select-none">01</span>
                <div>
                  <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-widest block">Automated Grading</span>
                  <p className="mt-1.5 text-xs text-zinc-500 leading-relaxed font-sans">
                    Compute health grades (A to D) based on documentation, activity, and codebase structure.
                  </p>
                </div>
              </div>
              <div className="py-6 flex gap-6 text-left">
                <span className="text-xs font-mono text-zinc-600 font-bold select-none">02</span>
                <div>
                  <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-widest block">Dormancy Tracking</span>
                  <p className="mt-1.5 text-xs text-zinc-500 leading-relaxed font-sans">
                    Monitor repository freshness, push cycles, and get flagged for inactive maintenance.
                  </p>
                </div>
              </div>
              <div className="py-6 flex gap-6 text-left">
                <span className="text-xs font-mono text-zinc-600 font-bold select-none">03</span>
                <div>
                  <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-widest block">AI Recommendations</span>
                  <p className="mt-1.5 text-xs text-zinc-500 leading-relaxed font-sans">
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
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100 font-sans selection:bg-zinc-800">
      <Navbar
        user={user}
        activeTab={activeTab}
        setActiveTab={(tab) => {
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
          <div className="mx-auto max-w-5xl px-6 py-10">
            <div className="mb-8 border-b border-zinc-900 pb-5">
              <h1 className="text-2xl font-serif text-white tracking-tight">Developer Analytics</h1>
              <p className="mt-1 text-xs text-zinc-500 font-sans">Aggregate statistics and code metrics from your portfolio.</p>
            </div>

            {analytics ? (
              <div className="border border-zinc-900 bg-zinc-950/20 p-8 rounded-none">
                <div className="grid gap-10 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-zinc-900/60">
                  {/* Language & Popularity */}
                  <div className="pr-0 md:pr-8">
                    <h3 className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-5">Language & Popularity</h3>
                    
                    <div className="divide-y divide-zinc-900/60">
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-zinc-400">Primary Language</span>
                        <span className="rounded-none bg-zinc-900 border border-zinc-850 px-2 py-0.5 text-[9px] font-mono font-semibold text-zinc-300">
                          {analytics.primary_language || "None detected"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-zinc-400">Most Popular Repository</span>
                        <span className="text-xs font-mono font-medium text-zinc-300 truncate max-w-[220px]">
                          {analytics.most_popular_repository || "N/A"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-zinc-400">Most Active Repository</span>
                        <span className="text-xs font-mono font-medium text-zinc-300 truncate max-w-[220px]">
                          {analytics.most_active_repository || "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Maintenance Index */}
                  <div className="pt-6 md:pt-0 pl-0 md:pl-10">
                    <h3 className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-5">Maintenance Metrics</h3>
                    
                    <div className="divide-y divide-zinc-900/60">
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-zinc-400">Active Repositories</span>
                        <span className="text-xs font-mono text-emerald-400 tracking-tight font-medium">
                          {analytics.active_repositories}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-zinc-400">Dormant Repositories</span>
                        <span className="text-xs font-mono text-rose-450 tracking-tight font-medium">
                          {analytics.dormant_repositories}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-3">
                        <span className="text-xs text-zinc-400">Average Health Score</span>
                        <span className="text-xs font-mono text-white tracking-tight font-medium">
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
              <div className="border border-dashed border-zinc-900 p-12 text-center rounded-none">
                <p className="text-xs font-mono uppercase tracking-wider text-zinc-500">Analytics data is not loaded yet.</p>
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
