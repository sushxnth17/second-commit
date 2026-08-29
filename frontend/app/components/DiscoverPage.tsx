"use client";

import { useEffect, useState } from "react";
import { api, RepositoryResponse } from "@/lib/api";

interface DiscoverPageProps {
  onSelectRepo: (repoId: number) => void;
}

export default function DiscoverPage({ onSelectRepo }: DiscoverPageProps) {
  const [projects, setProjects] = useState<RepositoryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("All");

  const fetchDiscoverProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.discoverRepositories();
      setProjects(res);
    } catch (err: any) {
      setError(err.message || "Failed to fetch discoverable projects.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiscoverProjects();
  }, []);

  // Collect unique languages for dropdown
  const languages = ["All", ...Array.from(new Set(projects.map((p) => p.language).filter(Boolean))) as string[]];

  // Filtered projects
  const filteredProjects = projects.filter((project) => {
    const matchesSearch =
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (project.description && project.description.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesLanguage = selectedLanguage === "All" || project.language === selectedLanguage;

    return matchesSearch && matchesLanguage;
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      {/* Editorial Header */}
      <div className="mb-12 border-b border-border-muted pb-8 select-none">
        <h1 className="text-4xl font-outfit font-extrabold tracking-tight text-text-primary leading-tight">
          Projects looking for a <span className="text-brand-accent">SecondCommit</span>.
        </h1>
        <p className="text-sm text-text-secondary mt-3 font-sans max-w-2xl leading-relaxed">
          These are projects their original developers have intentionally opened up for revival. Preserving the context behind the code so someone else can continue the work.
        </p>
      </div>

      {/* Filter Section */}
      <div className="mb-10 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:max-w-md">
          <input
            type="text"
            placeholder="Search projects by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-none border border-border-muted bg-surface-base px-4 py-2.5 text-xs text-text-primary placeholder-text-muted focus:border-brand-accent focus:outline-none transition-colors"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <span className="text-[10px] font-mono font-bold text-text-secondary uppercase tracking-widest shrink-0">
            Language:
          </span>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="w-full md:w-48 rounded-none border border-border-muted bg-surface-base px-3 py-2.5 text-xs text-text-primary focus:border-brand-accent focus:outline-none transition-colors cursor-pointer"
          >
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {lang}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        /* Loading Skeleton */
        <div className="space-y-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="border border-border-muted bg-surface-base p-6 animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 rounded-full bg-border-muted" />
                  <div className="h-4 w-32 bg-border-muted" />
                </div>
                <div className="h-4 w-20 bg-border-muted" />
              </div>
              <div className="h-4 w-full bg-border-muted mb-2" />
              <div className="h-4 w-2/3 bg-border-muted" />
            </div>
          ))}
        </div>
      ) : error ? (
        /* Error State */
        <div className="border border-semantic-critical/20 bg-semantic-critical/5 p-8 text-center animate-fade-in">
          <h3 className="text-sm font-mono uppercase tracking-widest text-semantic-critical font-bold">
            Failed to Load Projects
          </h3>
          <p className="mt-2 text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
            {error}
          </p>
          <button
            onClick={fetchDiscoverProjects}
            className="mt-5 rounded-none border border-semantic-critical/30 bg-surface-base px-5 py-2.5 text-[10px] font-mono uppercase tracking-widest text-semantic-critical hover:bg-semantic-critical/10 transition-all cursor-pointer outline-none"
          >
            Retry
          </button>
        </div>
      ) : filteredProjects.length === 0 ? (
        /* Empty State */
        <div className="border border-border-muted bg-surface-secondary/40 py-16 px-6 text-center select-none animate-fade-in">
          <svg
            className="mx-auto h-8 w-8 text-text-muted mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
          <h3 className="text-xs font-mono uppercase tracking-widest text-text-primary font-bold">
            No projects are looking for a SecondCommit yet
          </h3>
          <p className="mt-2 text-xs text-text-secondary leading-relaxed max-w-md mx-auto font-sans">
            Published projects will appear here when developers choose to hand them over for revival.
          </p>
        </div>
      ) : (
        /* Project Rows - Editorial List Layout */
        <div className="space-y-6 animate-fade-in">
          {filteredProjects.map((project) => {
            const owner = project.owner;
            const ownerName = owner ? (owner.name || owner.username) : "Owner";
            const ownerAvatarUrl = owner?.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${ownerName}`;
            const pushedDate = project.pushed_at ? new Date(project.pushed_at).toLocaleDateString() : "Never";

            return (
              <div
                key={project.id}
                className="border border-border-muted bg-surface-base hover:border-border-strong hover:shadow-sm transition-all duration-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6"
              >
                <div className="flex-1 min-w-0">
                  {/* Owner Header */}
                  <div className="flex items-center gap-2 mb-2.5 select-none">
                    <img
                      src={ownerAvatarUrl}
                      alt={ownerName}
                      className="h-4.5 w-4.5 rounded-full border border-border-muted object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${ownerName}`;
                      }}
                    />
                    <span className="text-[10px] font-bold text-text-secondary leading-none">
                      {ownerName}
                    </span>
                    {owner?.username && (
                      <span className="text-[9px] font-mono text-text-muted leading-none">
                        @{owner.username.toLowerCase()}
                      </span>
                    )}
                  </div>

                  {/* Project Title & Description */}
                  <h3 className="text-base font-outfit text-text-primary font-bold leading-snug">
                    {project.name}
                  </h3>
                  <p className="text-xs text-text-secondary font-sans leading-relaxed mt-1.5 line-clamp-2 max-w-3xl">
                    {project.description || "No description provided."}
                  </p>

                  {/* Technical Metadata Row */}
                  <div className="flex flex-wrap items-center gap-4 mt-4 font-mono text-[9px] text-text-muted select-none">
                    {project.language && (
                      <span className="flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-brand-accent/70" />
                        {project.language}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      STARS: {project.stars ?? 0}
                    </span>
                    <span className="flex items-center gap-1">
                      FORKS: {project.forks ?? 0}
                    </span>
                    <span>
                      LAST ACTIVITY: {pushedDate}
                    </span>
                  </div>
                </div>

                {/* View Project Action */}
                <button
                  onClick={() => onSelectRepo(project.id)}
                  className="w-full md:w-auto shrink-0 flex items-center justify-center gap-2 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent px-5 py-3 text-[9px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
                >
                  View Project
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
