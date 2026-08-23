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

  const handleLogout = () => {
    // Clear local session state (session cookie is HttpOnly, so we clear UI state)
    setUser(null);
    setRepos([]);
    setAnalytics(null);
    setSelectedRepoId(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-zinc-50 dark:bg-black">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
        <span className="text-sm font-semibold text-zinc-500 dark:text-zinc-400">Securing environment...</span>
      </div>
    );
  }

  // Unauthenticated Landing View
  if (!user) {
    return (
      <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100 font-sans selection:bg-indigo-500/30">
        <main className="flex flex-1 flex-col items-center justify-center px-6 py-20 sm:px-12 lg:px-16">
          <div className="w-full max-w-xl">
            {/* Header / Brand */}
            <div className="flex flex-col items-center mb-10 text-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900/50 text-indigo-400 mb-6">
                <span className="text-lg font-black tracking-wider">2C</span>
              </div>
              
              <h1 className="text-3xl font-bold tracking-tight text-white leading-tight">
                SecondCommit
              </h1>
              <p className="mt-2 text-sm text-zinc-400 max-w-sm">
                A repository quality dashboard delivering health scoring, activity metrics, and AI recommendations.
              </p>
            </div>

            {/* Login Box / Call to action */}
            <div className="rounded-lg border border-zinc-900 bg-zinc-950 p-6 text-center">
              <button
                onClick={handleLogin}
                className="flex w-full items-center justify-center gap-3 rounded-md bg-white px-4 py-2.5 text-xs font-semibold text-zinc-950 hover:bg-zinc-100 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-zinc-800"
              >
                <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                Connect with GitHub
              </button>
              <p className="mt-3 text-[10px] text-zinc-500 leading-normal">
                Authenticate with your GitHub account to access and analyze your repositories.
              </p>
            </div>

            {/* Feature List (Sleek Flat Table) */}
            <div className="mt-12 rounded-lg border border-zinc-900 bg-zinc-950 overflow-hidden divide-y divide-zinc-900">
              <div className="px-5 py-4">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Automated Grading</span>
                <p className="mt-1 text-xs text-zinc-500 leading-relaxed">
                  Compute health grades (A to D) based on documentation, activity, and codebase structure.
                </p>
              </div>
              <div className="px-5 py-4">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Dormancy Tracking</span>
                <p className="mt-1 text-xs text-zinc-500 leading-relaxed">
                  Monitor repository freshness, push cycles, and get flagged for inactive maintenance.
                </p>
              </div>
              <div className="px-5 py-4">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">AI Recommendations</span>
                <p className="mt-1 text-xs text-zinc-500 leading-relaxed">
                  Analyze repository metadata and receive actionable suggestions for improvement.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Authenticated Views Orchestrator
  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100 font-sans selection:bg-indigo-500/30">
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
              <h1 className="text-xl font-semibold text-white tracking-tight">Developer Analytics</h1>
              <p className="mt-1 text-xs text-zinc-500">Aggregate statistics and code metrics from your portfolio.</p>
            </div>

            {analytics ? (
              <div className="grid gap-6 md:grid-cols-2">
                {/* Language & Popularity */}
                <div className="rounded-lg border border-zinc-900 bg-zinc-950/30 p-6">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-6">Language & Popularity</h3>
                  
                  <div className="divide-y divide-zinc-900">
                    <div className="flex items-center justify-between py-3">
                      <span className="text-xs text-zinc-400">Primary Language</span>
                      <span className="rounded-md bg-zinc-900 border border-zinc-800 px-2 py-0.5 text-xs font-semibold text-zinc-300">
                        {analytics.primary_language || "None detected"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-3">
                      <span className="text-xs text-zinc-400">Most Popular Repository</span>
                      <span className="text-xs font-medium text-white truncate max-w-[200px]">
                        {analytics.most_popular_repository || "N/A"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-3">
                      <span className="text-xs text-zinc-400">Most Active Repository</span>
                      <span className="text-xs font-medium text-white truncate max-w-[200px]">
                        {analytics.most_active_repository || "N/A"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Maintenance Index */}
                <div className="rounded-lg border border-zinc-900 bg-zinc-950/30 p-6">
                  <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-6">Maintenance Metrics</h3>
                  
                  <div className="divide-y divide-zinc-900">
                    <div className="flex items-center justify-between py-3">
                      <span className="text-xs text-zinc-400">Active Repositories</span>
                      <span className="text-xs font-mono text-emerald-400">
                        {analytics.active_repositories}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-3">
                      <span className="text-xs text-zinc-400">Dormant Repositories</span>
                      <span className="text-xs font-mono text-rose-400">
                        {analytics.dormant_repositories}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-3">
                      <span className="text-xs text-zinc-400">Average Health Score</span>
                      <span className="text-xs font-mono text-white">
                        {analytics.average_health_score !== null && analytics.average_health_score !== undefined
                          ? `${Math.round(analytics.average_health_score)}/100`
                          : "N/A"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-zinc-900 bg-zinc-950/50 p-12 text-center">
                <p className="text-xs text-zinc-500">Analytics data is not loaded yet.</p>
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
