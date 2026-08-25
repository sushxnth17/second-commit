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
        return "text-semantic-healthy border border-semantic-healthy/20 bg-semantic-healthy/10";
      case "B":
        return "text-teal-600 border border-teal-250 bg-teal-50";
      case "C":
        return "text-semantic-warning border border-semantic-warning/20 bg-semantic-warning/10";
      default:
        return "text-semantic-critical border border-semantic-critical/20 bg-semantic-critical/10";
    }
  };

  const getDormancyBadgeColor = (status?: string) => {
    if (status?.toLowerCase() === "active") {
      return "text-semantic-healthy border border-semantic-healthy/20 bg-semantic-healthy/10";
    }
    return "text-semantic-critical border border-semantic-critical/20 bg-semantic-critical/10";
  };

  const getGradeBarColor = (grade: "A" | "B" | "C" | "D" | "F") => {
    if (grade === "A" || grade === "B") return "bg-semantic-healthy";
    if (grade === "C") return "bg-semantic-warning";
    return "bg-semantic-critical";
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
    <div className="mx-auto max-w-5xl px-6 py-12 select-none">
      {/* Dashboard Greeting Hero */}
      <div className="mb-12 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-outfit text-text-primary tracking-tight font-extrabold">
            Welcome back, {user.name || user.username}.
          </h1>
          <p className="mt-1.5 text-xs text-text-secondary font-sans select-none">Here's how your repositories are doing.</p>
        </div>
        <button
          onClick={onImportClick}
          className="flex items-center justify-center gap-2.5 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent px-4 py-2.5 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent shadow-sm hover:shadow-md"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-3.5 w-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Import Repository
        </button>
      </div>

      {/* Health Overview & Metrics Row */}
      <div className="grid gap-12 md:grid-cols-5 border-t border-b border-border-muted py-8 mb-12 bg-transparent select-none">
        {/* Left column: Repository Health distribution */}
        <div className="md:col-span-3 flex flex-col justify-between pr-0 md:pr-10 border-r-0 md:border-r border-border-muted">
          <div>
            <h3 className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-widest mb-5">Repository Health</h3>
            <div className="flex items-baseline gap-4 mb-6">
              <span className="text-6xl font-mono text-text-primary tracking-tighter leading-none font-bold">
                {analytics?.average_health_score !== null && analytics?.average_health_score !== undefined
                  ? Math.round(analytics.average_health_score)
                  : "—"}
              </span>
              <div className="flex flex-col">
                <span className="text-[9px] font-mono tracking-widest uppercase text-text-muted font-bold block leading-none">AVERAGE HEALTH</span>
                <span className="text-[10px] font-mono text-text-secondary mt-1 font-bold block leading-none">GRADE {
                  analytics?.average_health_score !== null && analytics?.average_health_score !== undefined
                    ? (analytics.average_health_score >= 90 ? "A" : analytics.average_health_score >= 80 ? "B" : analytics.average_health_score >= 70 ? "C" : "D")
                    : "—"
                }</span>
              </div>
            </div>
          </div>

          {/* Distribution list */}
          <div className="space-y-2.5 text-xs text-text-secondary max-w-sm">
            {(["A", "B", "C", "D", "F"] as const).map((grade) => (
              <div key={grade} className="flex items-center gap-3">
                <span className="w-3 font-mono text-[10px] text-text-secondary text-right select-none">{grade}</span>
                <div className="h-[1.5px] flex-1 bg-border-muted">
                  <div
                    className={`h-full ${getGradeBarColor(grade)} transition-all`}
                    style={{
                      width: `${(gradeCounts[grade] / Math.max(repos.length, 1)) * 100}%`,
                    }}
                  />
                </div>
                <span className="w-4 text-right font-mono text-[9px] text-text-secondary select-none">
                  {gradeCounts[grade]}
                </span>
              </div>
            ))}
            <div className="mt-6 pt-4 text-[10px] font-mono uppercase tracking-wider text-text-secondary border-t border-border-muted">
              {reposNeedingAttention.length > 0 ? (
                <span className="text-semantic-critical font-bold">{reposNeedingAttention.length} {reposNeedingAttention.length === 1 ? "repository requires" : "repositories require"} attention.</span>
              ) : (
                <span className="text-semantic-healthy font-bold">All repositories are currently stable.</span>
              )}
            </div>
          </div>
        </div>

        {/* Right column: Aggregate Metrics */}
        <div className="md:col-span-2 flex flex-col justify-between pl-0 md:pl-2 gap-6 md:gap-0">
          <div>
            <h3 className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-widest mb-4">Portfolio Summary</h3>
            <div className="divide-y divide-border-muted">
              <div className="flex justify-between py-3">
                <span className="text-xs text-text-secondary font-medium">Total Repositories</span>
                <span className="text-xs font-mono text-text-primary font-bold tracking-tight">{repos.length}</span>
              </div>
              <div className="flex justify-between py-3">
                <span className="text-xs text-text-secondary font-medium">Active / Dormant</span>
                <span className="text-xs font-mono text-text-primary font-bold tracking-tight">
                  <span className="text-semantic-healthy">{analytics?.active_repositories ?? 0}</span>
                  <span className="text-text-muted mx-1.5 font-normal">/</span>
                  <span className="text-semantic-critical">{analytics?.dormant_repositories ?? 0}</span>
                </span>
              </div>
              <div className="flex justify-between py-3">
                <span className="text-xs text-text-secondary font-medium">Total Stars</span>
                <span className="text-xs font-mono text-text-primary font-bold tracking-tight">{analytics?.total_stars ?? 0}</span>
              </div>
              <div className="flex justify-between py-3">
                <span className="text-xs text-text-secondary font-medium">Total Forks</span>
                <span className="text-xs font-mono text-text-primary font-bold tracking-tight">{analytics?.total_forks ?? 0}</span>
              </div>
            </div>
          </div>
          <p className="text-[9px] font-mono text-text-muted leading-normal">
            Updated via GitHub webhooks. Run sync inside repository details to force refresh active metrics.
          </p>
        </div>
      </div>

      {/* Needs Attention Section */}
      {reposNeedingAttention.length > 0 && (
        <div className="mb-12">
          <div className="flex items-baseline justify-between border-b border-border-muted pb-3 mb-4 select-none">
            <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-semantic-critical">Needs attention</h2>
            <span className="text-[10px] font-mono uppercase tracking-widest text-text-secondary font-bold">
              {reposNeedingAttention.length} {reposNeedingAttention.length === 1 ? "repository" : "repositories"}
            </span>
          </div>
          <div className="divide-y divide-border-muted border-t border-b border-border-muted bg-transparent">
            {reposNeedingAttention.slice(0, 3).map((repo) => (
              <div
                key={repo.id}
                onClick={() => onSelectRepo(repo.id)}
                className="flex items-center justify-between py-5 px-2 hover:bg-surface-secondary/40 transition-all duration-150 cursor-pointer group"
              >
                <div className="flex-1 min-w-0 pr-4">
                  <h4 className="font-outfit text-sm font-bold text-text-primary group-hover:text-brand-accent transition-colors duration-150 truncate">
                    {repo.name}
                  </h4>
                  <p className="text-[8px] font-mono uppercase tracking-widest text-text-muted mt-1 select-none">
                    LAST ACTIVITY: {getDaysAgo(repo.pushed_at)}
                  </p>
                </div>

                <div className="flex items-center gap-8 shrink-0 select-none">
                  {/* Grade badge */}
                  <span className={`rounded-none border px-2 py-0.5 text-[9px] font-mono uppercase font-bold ${getHealthBadgeColor(repo.health_grade)}`}>
                    {repo.health_grade || "F"}
                  </span>
                  {/* Score */}
                  <span className="text-sm font-mono text-text-primary tracking-tight font-bold w-8 text-right">
                    {repo.health_score ?? 0}
                  </span>
                  {/* Action */}
                  <div className="flex items-center text-[10px] font-mono uppercase tracking-widest text-text-secondary group-hover:text-brand-accent transition-colors duration-150 pl-2">
                    <span>View</span>
                    <span className="ml-1.5 transform group-hover:translate-x-1 transition-transform duration-150">→</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Repositories Section */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between">
        <div>
          <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-text-secondary">All Repositories</h2>
          <p className="text-[10px] text-text-secondary mt-1 select-none">Explore metrics, stars, and language details for your codebase.</p>
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
              className="w-full sm:w-48 rounded-none border border-border-muted bg-surface-base py-1.5 pl-8 pr-3 text-xs text-text-primary outline-none transition-all focus:border-brand-accent"
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-secondary"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>

          {/* Language filter */}
          <select
            value={langFilter}
            onChange={(e) => setLangFilter(e.target.value)}
            className="rounded-none border border-border-muted bg-surface-base py-1.5 px-3 text-xs text-text-secondary outline-none cursor-pointer focus:border-brand-accent transition-all"
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
            className="rounded-none border border-border-muted bg-surface-base py-1.5 px-3 text-xs text-text-secondary outline-none cursor-pointer focus:border-brand-accent transition-all"
          >
            <option value="all">All Health</option>
            <option value="healthy">Healthy (A-C)</option>
            <option value="critical">Critical (D/F)</option>
          </select>

          {/* Activity filter */}
          <select
            value={activityFilter}
            onChange={(e) => setActivityFilter(e.target.value)}
            className="rounded-none border border-border-muted bg-surface-base py-1.5 px-3 text-xs text-text-secondary outline-none cursor-pointer focus:border-brand-accent transition-all"
          >
            <option value="all">All Activity</option>
            <option value="active">Active</option>
            <option value="dormant">Dormant</option>
          </select>
        </div>
      </div>

      {/* Repositories Table */}
      {filteredRepos.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-none border border-dashed border-border-muted py-16 text-center bg-surface-base shadow-sm">
          <div className="flex h-10 w-10 items-center justify-center bg-surface-secondary text-text-muted border border-border-muted mb-4 select-none">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.008 1.24l.885 1.77a2.25 2.25 0 002.007 1.24h1.98a2.25 2.25 0 002.007-1.24l.885-1.77a2.25 2.25 0 012.007-1.24h3.86m-18 0h18a2.25 2.25 0 012.25 2.25v4.5A2.25 2.25 0 0118 21H6a2.25 2.25 0 01-2.25-2.25v-4.5a2.25 2.25 0 012.25-2.25z" />
            </svg>
          </div>
          <h3 className="text-xs font-mono uppercase tracking-wider text-text-secondary">No repositories matching filters</h3>
          <p className="mt-1 text-[10px] text-text-secondary max-w-xs leading-normal font-sans">
            Try adjusting your search query, selecting another language filter, or import a new repository.
          </p>
          <button
            onClick={onImportClick}
            className="mt-5 rounded-none border border-border-muted bg-surface-secondary px-4 py-2 text-[10px] font-mono uppercase tracking-widest text-text-secondary hover:text-text-primary hover:border-border-strong hover:bg-surface-base transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent shadow-sm"
          >
            Import Repository
          </button>
        </div>
      ) : (
        <div className="border border-border-muted bg-surface-base overflow-hidden overflow-x-auto shadow-sm">
          <table className="w-full min-w-[750px] border-collapse text-left text-xs text-text-secondary">
            <thead className="bg-surface-base text-[9px] uppercase font-mono tracking-widest text-text-muted border-b border-border-muted select-none font-bold">
              <tr>
                <th className="py-3.5 px-4 font-bold">Repository</th>
                <th className="py-3.5 px-4 font-bold">Language</th>
                <th className="py-3.5 px-4 font-bold">Health</th>
                <th className="py-3.5 px-4 font-bold">Activity</th>
                <th className="py-3.5 px-4 text-center font-bold">Stars</th>
                <th className="py-3.5 px-4 text-center font-bold">Forks</th>
                <th className="py-3.5 px-4 font-bold">Last Updated</th>
                <th className="py-3.5 px-4 text-right font-bold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-muted">
              {filteredRepos.map((repo) => (
                <tr
                  key={repo.id}
                  onClick={() => onSelectRepo(repo.id)}
                  className="hover:bg-surface-secondary/40 transition-colors cursor-pointer group"
                >
                  <td className="py-3.5 px-4 font-outfit text-sm font-bold text-text-primary group-hover:text-brand-accent transition-colors duration-150 max-w-[220px] truncate">
                    {repo.name}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[9px] uppercase select-none">
                    {repo.language ? (
                      <span className="rounded-none bg-surface-secondary border border-border-muted px-2 py-0.5 text-[9px] text-text-secondary font-bold font-mono">
                        {repo.language}
                      </span>
                    ) : (
                      <span className="text-text-muted font-normal">—</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-mono select-none">
                    <span className={`rounded-none border px-1.5 py-0.5 text-[9px] font-bold ${getHealthBadgeColor(repo.health_grade)}`}>
                      {repo.health_grade || "—"}
                    </span>
                    <span className="text-text-secondary text-[10px] ml-2 font-bold">{repo.health_score ?? "—"}</span>
                  </td>
                  <td className="py-3.5 px-4 select-none">
                    <span className={`inline-flex items-center gap-1.5 rounded-none px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider font-bold border ${getDormancyBadgeColor(repo.dormancy_status)}`}>
                      {repo.dormancy_status || "Unknown"}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono text-text-primary font-bold tracking-tight">{repo.stars ?? 0}</td>
                  <td className="py-3.5 px-4 text-center font-mono text-text-primary font-bold tracking-tight">{repo.forks ?? 0}</td>
                  <td className="py-3.5 px-4 text-text-muted font-mono text-[10px] tracking-tight select-none">
                    {getDaysAgo(repo.pushed_at)}
                  </td>
                  <td className="py-3.5 px-4 text-right select-none">
                    <div className="flex items-center justify-end text-[10px] font-mono uppercase tracking-widest text-text-secondary group-hover:text-brand-accent transition-colors duration-150">
                      <span>Analyze</span>
                      <span className="ml-1.5 transform group-hover:translate-x-1 transition-transform duration-150">→</span>
                    </div>
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
