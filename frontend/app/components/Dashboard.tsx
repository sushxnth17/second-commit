"use client";

import { useState } from "react";
import { RepositorySummary, AnalyticsResponse, UserSummary } from "@/lib/api";

interface DashboardProps {
  user: UserSummary;
  repos: RepositorySummary[];
  analytics: AnalyticsResponse | null;
  onImportClick: () => void;
  onSelectRepo: (id: number) => void;
  onSyncSuccess: () => void;
}

export default function Dashboard({
  user,
  repos,
  analytics,
  onImportClick,
  onSelectRepo,
  onSyncSuccess,
}: DashboardProps) {
  const [search, setSearch] = useState("");
  const [langFilter, setLangFilter] = useState("all");
  const [healthFilter, setHealthFilter] = useState("all");
  const [activityFilter, setActivityFilter] = useState("all");

  // Get active languages for filter
  const uniqueLanguages = Array.from(
    new Set(repos.map((r) => r.language).filter(Boolean))
  ) as string[];

  // Helpers for formatting date
  const getDaysAgo = (dateStr?: string | null) => {
    if (!dateStr) return "never";
    const date = new Date(dateStr);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return "today";
    return `${diffDays}d ago`;
  };

  // Helper for status colors
  const getHealthBadgeColor = (grade?: string) => {
    switch (grade) {
      case "A":
        return "text-emerald-450 border-emerald-950/30 bg-emerald-950/10";
      case "B":
        return "text-teal-450 border-teal-950/30 bg-teal-950/10";
      case "C":
        return "text-amber-450 border-amber-950/30 bg-amber-950/10";
      default:
        return "text-rose-450 border-rose-950/30 bg-rose-950/10";
    }
  };

  const getDormancyBadgeColor = (status?: string) => {
    if (status?.toLowerCase() === "active") {
      return "text-emerald-450 border-emerald-950/30 bg-emerald-950/10";
    }
    return "text-rose-450 border-rose-950/30 bg-rose-950/10";
  };

  // 1. Calculate Grade distribution
  const gradeCounts = { A: 0, B: 0, C: 0, D: 0, F: 0 };
  repos.forEach((repo) => {
    const grade = repo.health_grade || "F";
    if (grade in gradeCounts) {
      gradeCounts[grade as keyof typeof gradeCounts]++;
    } else {
      gradeCounts.F++;
    }
  });

  // 2. Identify "Needs attention" repositories (< 70 health_score or dormant status)
  const reposNeedingAttention = repos.filter(
    (repo) =>
      (repo.health_score !== undefined && repo.health_score < 70) ||
      (repo.dormancy_status && repo.dormancy_status.toLowerCase() !== "active")
  );

  // 3. Filter Repositories for "All Repositories" view
  const filteredRepos = repos.filter((repo) => {
    const matchesSearch = repo.name.toLowerCase().includes(search.toLowerCase());
    const matchesLang = langFilter === "all" || repo.language === langFilter;
    
    let matchesHealth = true;
    if (healthFilter === "critical") {
      matchesHealth = (repo.health_score !== undefined && repo.health_score < 70);
    } else if (healthFilter === "healthy") {
      matchesHealth = (repo.health_score !== undefined && repo.health_score >= 70);
    }

    let matchesActivity = true;
    if (activityFilter === "active") {
      matchesActivity = repo.dormancy_status?.toLowerCase() === "active";
    } else if (activityFilter === "dormant") {
      matchesActivity = repo.dormancy_status !== undefined && repo.dormancy_status.toLowerCase() !== "active";
    }

    return matchesSearch && matchesLang && matchesHealth && matchesActivity;
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      {/* Dashboard Greeting Hero */}
      <div className="mb-10 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif text-white tracking-tight">
            Welcome back, {user.name || user.username}.
          </h1>
          <p className="mt-1 text-xs text-zinc-500 font-sans">Here's how your repositories are doing.</p>
        </div>
        <button
          onClick={onImportClick}
          className="flex items-center justify-center gap-2 rounded-none border border-zinc-800 bg-zinc-900 px-4 py-2 text-[10px] font-mono uppercase tracking-wider text-zinc-350 hover:text-white hover:bg-zinc-800 hover:border-zinc-700 transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-zinc-650"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-3.5 w-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Import Repository
        </button>
      </div>

      {/* Health Overview & Metrics Row */}
      <div className="grid gap-12 md:grid-cols-5 border-t border-b border-zinc-900 py-8 mb-10">
        {/* Left column: Repository Health distribution */}
        <div className="md:col-span-3 flex flex-col justify-between pr-0 md:pr-10 border-r-0 md:border-r border-zinc-900/60">
          <div>
            <h3 className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-4">Repository Health</h3>
            <div className="flex items-baseline gap-4 mb-6">
              <div>
                <span className="text-5xl font-mono text-white tracking-tighter leading-none">
                  {analytics?.average_health_score !== null && analytics?.average_health_score !== undefined
                    ? Math.round(analytics.average_health_score)
                    : "—"}
                </span>
                <span className="text-xs text-zinc-500 ml-1.5 font-mono">/100 average</span>
              </div>
              <div className={`rounded-none border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider font-semibold ${
                getHealthBadgeColor(
                  analytics?.average_health_score !== null && analytics?.average_health_score !== undefined
                    ? (analytics.average_health_score >= 90 ? "A" : analytics.average_health_score >= 80 ? "B" : analytics.average_health_score >= 70 ? "C" : "D")
                    : undefined
                )
              }`}>
                Grade {
                  analytics?.average_health_score !== null && analytics?.average_health_score !== undefined
                    ? (analytics.average_health_score >= 90 ? "A" : analytics.average_health_score >= 80 ? "B" : analytics.average_health_score >= 70 ? "C" : "D")
                    : "—"
                }
              </div>
            </div>
          </div>

          {/* Distribution list */}
          <div className="space-y-2 text-xs text-zinc-500 max-w-sm">
            {(["A", "B", "C", "D", "F"] as const).map((grade) => (
              <div key={grade} className="flex items-center gap-3">
                <span className="w-3 font-mono text-zinc-500 text-right">{grade}</span>
                <div className="h-[2px] flex-1 bg-zinc-900 overflow-hidden">
                  <div
                    className="h-full bg-zinc-400 transition-all"
                    style={{
                      width: `${(gradeCounts[grade] / Math.max(repos.length, 1)) * 100}%`,
                    }}
                  />
                </div>
                <span className="w-4 text-right font-mono text-[10px] text-zinc-500">
                  {gradeCounts[grade]}
                </span>
              </div>
            ))}
            <div className="mt-5 pt-4 text-[10px] font-mono uppercase tracking-wider text-zinc-550 border-t border-zinc-900/60">
              {reposNeedingAttention.length > 0 ? (
                <span className="text-rose-450 font-semibold">{reposNeedingAttention.length} {reposNeedingAttention.length === 1 ? "repository requires" : "repositories require"} attention.</span>
              ) : (
                <span className="text-emerald-450 font-semibold">All repositories are currently stable.</span>
              )}
            </div>
          </div>
        </div>

        {/* Right column: Aggregate Metrics */}
        <div className="md:col-span-2 flex flex-col justify-between pl-0 md:pl-2 gap-6 md:gap-0">
          <div>
            <h3 className="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest mb-4">Portfolio Summary</h3>
            <div className="divide-y divide-zinc-900/60">
              <div className="flex justify-between py-2.5">
                <span className="text-xs text-zinc-400">Total Repositories</span>
                <span className="text-xs font-mono text-white tracking-tight">{repos.length}</span>
              </div>
              <div className="flex justify-between py-2.5">
                <span className="text-xs text-zinc-400">Active / Dormant</span>
                <span className="text-xs font-mono text-white tracking-tight">
                  <span className="text-emerald-400">{analytics?.active_repositories ?? 0}</span>
                  <span className="text-zinc-700 mx-1.5">/</span>
                  <span className="text-rose-400">{analytics?.dormant_repositories ?? 0}</span>
                </span>
              </div>
              <div className="flex justify-between py-2.5">
                <span className="text-xs text-zinc-400">Total Stars</span>
                <span className="text-xs font-mono text-white tracking-tight">{analytics?.total_stars ?? 0}</span>
              </div>
              <div className="flex justify-between py-2.5">
                <span className="text-xs text-zinc-400">Total Forks</span>
                <span className="text-xs font-mono text-white tracking-tight">{analytics?.total_forks ?? 0}</span>
              </div>
            </div>
          </div>
          <p className="text-[9px] font-mono text-zinc-600 leading-normal">
            Updated via GitHub webhooks. Run sync inside repository details to force refresh active metrics.
          </p>
        </div>
      </div>

      {/* Needs Attention Section */}
      {reposNeedingAttention.length > 0 && (
        <div className="mb-10">
          <div className="mb-4">
            <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-rose-500">Needs attention</h2>
            <p className="text-[10px] text-zinc-500 mt-1">Repositories with low health ratings or inactive pushes.</p>
          </div>
          
          <div className="border border-zinc-900 bg-zinc-950/40 divide-y divide-zinc-900/60">
            {reposNeedingAttention.slice(0, 3).map((repo) => (
              <div
                key={repo.id}
                onClick={() => onSelectRepo(repo.id)}
                className="flex items-center justify-between p-4.5 hover:bg-zinc-900/10 transition-colors cursor-pointer group"
              >
                <div className="flex-1 min-w-0 pr-4">
                  <h4 className="font-serif text-sm font-normal text-zinc-200 group-hover:text-white transition-colors truncate">
                    {repo.name}
                  </h4>
                  <div className="mt-1.5 flex items-center gap-3">
                    {repo.language && (
                      <span className="rounded-none bg-zinc-900 border border-zinc-850 px-1.5 py-0.5 text-[9px] text-zinc-400 font-mono">
                        {repo.language}
                      </span>
                    )}
                    <span className="text-[9px] text-zinc-550 font-mono">
                      last activity: {getDaysAgo(repo.pushed_at)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-5 shrink-0">
                  <div className="text-right hidden sm:block">
                    <span className="text-[9px] text-zinc-500 uppercase tracking-widest font-mono block">Health</span>
                    <span className="text-xs font-semibold text-white font-mono tracking-tight mt-0.5 block">{repo.health_score ?? 0}</span>
                  </div>
                  <span className={`rounded-none border px-2 py-0.5 text-[10px] font-mono uppercase font-semibold ${getHealthBadgeColor(repo.health_grade)}`}>
                    {repo.health_grade || "F"}
                  </span>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 group-hover:text-white transition-colors pl-2 select-none">
                    View
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Repositories Section */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between">
        <div>
          <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-zinc-400">All Repositories</h2>
          <p className="text-[10px] text-zinc-500 mt-1">Explore metrics, stars, and language details for your codebase.</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search repositories..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full sm:w-44 rounded-none border border-zinc-900 bg-zinc-950 py-1.5 pl-8 pr-3 text-xs text-white outline-none placeholder:text-zinc-600 transition-colors focus:border-zinc-700 focus:ring-0 focus-visible:border-zinc-700"
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-600"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>

          {/* Language filter */}
          <select
            value={langFilter}
            onChange={(e) => setLangFilter(e.target.value)}
            className="rounded-none border border-zinc-900 bg-zinc-950 py-1.5 px-3 text-xs text-zinc-400 outline-none hover:border-zinc-800 cursor-pointer focus:border-zinc-700"
          >
            <option value="all">All Languages</option>
            {uniqueLanguages.map((lang) => (
              <option key={lang} value={lang}>
                {lang}
              </option>
            ))}
          </select>

          {/* Health filter */}
          <select
            value={healthFilter}
            onChange={(e) => setHealthFilter(e.target.value)}
            className="rounded-none border border-zinc-900 bg-zinc-950 py-1.5 px-3 text-xs text-zinc-400 outline-none hover:border-zinc-800 cursor-pointer focus:border-zinc-700"
          >
            <option value="all">All Health</option>
            <option value="healthy">Healthy (A-C)</option>
            <option value="critical">Critical (D/F)</option>
          </select>

          {/* Activity filter */}
          <select
            value={activityFilter}
            onChange={(e) => setActivityFilter(e.target.value)}
            className="rounded-none border border-zinc-900 bg-zinc-950 py-1.5 px-3 text-xs text-zinc-400 outline-none hover:border-zinc-800 cursor-pointer focus:border-zinc-700"
          >
            <option value="all">All Activity</option>
            <option value="active">Active</option>
            <option value="dormant">Dormant</option>
          </select>
        </div>
      </div>

      {/* Repositories Table */}
      {filteredRepos.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-none border border-dashed border-zinc-900 py-16 text-center">
          <div className="flex h-10 w-10 items-center justify-center bg-zinc-950 text-zinc-600 border border-zinc-900 mb-4 select-none">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.008 1.24l.885 1.77a2.25 2.25 0 002.007 1.24h1.98a2.25 2.25 0 002.007-1.24l.885-1.77a2.25 2.25 0 012.007-1.24h3.86m-18 0h18a2.25 2.25 0 012.25 2.25v4.5A2.25 2.25 0 0118 21H6a2.25 2.25 0 01-2.25-2.25v-4.5a2.25 2.25 0 012.25-2.25z" />
            </svg>
          </div>
          <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-350">No repositories matching filters</h3>
          <p className="mt-1 text-[10px] text-zinc-550 max-w-xs leading-normal font-sans">
            Try adjusting your search query, selecting another language filter, or import a new repository.
          </p>
          <button
            onClick={onImportClick}
            className="mt-5 rounded-none border border-zinc-800 bg-zinc-900 px-4 py-2 text-[10px] font-mono uppercase tracking-wider text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-zinc-650"
          >
            Import Repository
          </button>
        </div>
      ) : (
        <div className="border border-zinc-900 bg-zinc-950/20 overflow-hidden overflow-x-auto">
          <table className="w-full min-w-[750px] border-collapse text-left text-xs text-zinc-400">
            <thead className="bg-zinc-950/60 text-[9px] uppercase font-mono tracking-widest text-zinc-500 border-b border-zinc-900">
              <tr>
                <th className="py-3 px-4 font-semibold">Repository</th>
                <th className="py-3 px-4 font-semibold">Language</th>
                <th className="py-3 px-4 font-semibold">Health</th>
                <th className="py-3 px-4 font-semibold">Activity</th>
                <th className="py-3 px-4 text-center font-semibold">Stars</th>
                <th className="py-3 px-4 text-center font-semibold">Forks</th>
                <th className="py-3 px-4 font-semibold">Last Updated</th>
                <th className="py-3 px-4 text-right font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900/60">
              {filteredRepos.map((repo) => (
                <tr
                  key={repo.id}
                  onClick={() => onSelectRepo(repo.id)}
                  className="hover:bg-zinc-900/20 transition-colors cursor-pointer group"
                >
                  <td className="py-3.5 px-4 font-serif text-sm font-normal text-zinc-250 group-hover:text-white transition-colors max-w-[220px] truncate">
                    {repo.name}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[10px]">
                    {repo.language ? (
                      <span className="rounded-none bg-zinc-900 border border-zinc-850 px-2 py-0.5 text-[9px] text-zinc-305">
                        {repo.language}
                      </span>
                    ) : (
                      <span className="text-zinc-700">—</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-mono">
                    <span className={`rounded-none border px-1.5 py-0.5 text-[9px] font-semibold ${getHealthBadgeColor(repo.health_grade)}`}>
                      {repo.health_grade || "—"}
                    </span>
                    <span className="text-zinc-500 text-[10px] ml-2">{repo.health_score ?? "—"}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center gap-1.5 rounded-none px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider border ${getDormancyBadgeColor(repo.dormancy_status)}`}>
                      {repo.dormancy_status || "Unknown"}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono text-zinc-300 tracking-tight">{repo.stars ?? 0}</td>
                  <td className="py-3.5 px-4 text-center font-mono text-zinc-300 tracking-tight">{repo.forks ?? 0}</td>
                  <td className="py-3.5 px-4 text-zinc-500 font-mono text-[10px] tracking-tight">
                    {getDaysAgo(repo.pushed_at)}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-550 group-hover:text-white transition-colors select-none">
                      Analyze →
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
