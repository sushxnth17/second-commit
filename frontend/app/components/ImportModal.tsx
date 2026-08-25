"use client";

import { useEffect, useState } from "react";
import { api, GitHubRepo } from "@/lib/api";

interface ImportModalProps {
  onClose: () => void;
  onImportSuccess: () => void;
}

export default function ImportModal({ onClose, onImportSuccess }: ImportModalProps) {
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [importingId, setImportingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importedIds, setImportedIds] = useState<number[]>([]);

  useEffect(() => {
    async function fetchRepos() {
      try {
        const fetched = await api.getGitHubRepositories();
        setRepos(fetched);
      } catch (err: any) {
        setError(err.message || "Failed to load GitHub repositories.");
      } finally {
        setLoading(false);
      }
    }
    fetchRepos();
  }, []);

  const handleImport = async (repoId: number) => {
    setImportingId(repoId);
    setError(null);
    try {
      await api.importRepository(repoId);
      setImportedIds((prev) => [...prev, repoId]);
      onImportSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to import repository.");
    } finally {
      setImportingId(null);
    }
  };

  const filteredRepos = repos.filter(
    (repo) =>
      repo.name.toLowerCase().includes(search.toLowerCase()) ||
      (repo.description && repo.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in">
      <div className="flex h-full max-h-[80vh] w-full max-w-2xl flex-col rounded-none border border-border-muted bg-surface-base shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-muted p-5 bg-surface-base/60 select-none">
          <div>
            <h2 className="text-base font-outfit text-text-primary font-bold tracking-tight">Import Repositories</h2>
            <p className="mt-1.5 text-[10px] text-text-secondary font-sans">
              Select a repository from your GitHub profile to import and analyze.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-none border border-transparent hover:border-border-muted hover:bg-surface-secondary/50 p-1.5 text-text-secondary hover:text-brand-accent transition-colors cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {error && (
            <div className="mb-4 rounded-none border border-semantic-critical/30 bg-semantic-critical/5 p-3.5 text-xs text-semantic-critical font-mono">
              <div className="flex gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4 shrink-0">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Search bar */}
          <div className="relative mb-4">
            <input
              type="text"
              placeholder="Search GitHub repositories..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-none border border-border-muted hover:border-border-strong bg-surface-secondary py-2 pl-9 pr-4 text-xs text-text-primary outline-none placeholder:text-text-muted transition-colors focus:border-brand-accent focus:bg-white"
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="absolute left-3 top-2.5 h-3.5 w-3.5 text-text-secondary"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>

          {/* Repos list */}
          {loading ? (
            <div className="flex h-48 flex-col items-center justify-center gap-4 select-none">
              <div className="flex items-center gap-1.5">
                <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse" />
                <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse [animation-delay:0.2s]" />
                <div className="h-1 w-1 rounded-full bg-border-strong animate-pulse [animation-delay:0.4s]" />
              </div>
              <span className="text-[10px] font-mono tracking-wider uppercase text-text-secondary">Loading repositories</span>
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center text-center select-none">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">No repositories found</span>
              <span className="mt-1.5 text-[10px] text-text-secondary font-mono">Try adjusting your search query.</span>
            </div>
          ) : (
            <div className="grid gap-2">
              {filteredRepos.map((repo) => {
                const isImported = importedIds.includes(repo.id);
                const isImporting = importingId === repo.id;

                return (
                  <div
                    key={repo.id}
                    className="flex items-center justify-between gap-4 rounded-none border border-border-muted bg-surface-secondary/40 p-3.5 transition-colors hover:bg-surface-base"
                  >
                    <div className="flex-1 min-w-0">
                      <h4 className="font-outfit text-sm font-bold text-text-primary truncate">
                        {repo.name}
                      </h4>
                      <p className="mt-1 text-[10px] text-text-secondary line-clamp-1 leading-normal font-sans">
                        {repo.description || "No description provided."}
                      </p>
                      <div className="mt-2 flex items-center gap-3">
                        {repo.language && (
                          <span className="inline-flex items-center gap-1.5 text-[9px] text-text-secondary font-mono select-none font-bold">
                            <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
                            {repo.language}
                          </span>
                        )}
                        <span className="text-[9px] text-text-muted font-mono select-none">
                          default branch: {repo.default_branch}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleImport(repo.id)}
                      disabled={isImported || isImporting}
                      className={`rounded-none px-3.5 py-2 text-[10px] font-mono uppercase font-bold tracking-widest transition-all duration-150 shrink-0 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent shadow-sm ${
                        isImported
                          ? "bg-surface-base text-semantic-healthy border border-border-muted cursor-default shadow-none"
                          : isImporting
                          ? "bg-surface-base text-text-secondary border border-border-muted cursor-not-allowed animate-pulse shadow-none"
                          : "bg-surface-secondary text-text-secondary border border-border-muted hover:border-brand-accent hover:text-brand-accent hover:bg-surface-base"
                      }`}
                    >
                      {isImported ? "Imported" : isImporting ? "Importing" : "Import"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border-muted bg-surface-base p-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-none border border-border-muted bg-surface-secondary px-4 py-2 text-[10px] font-mono uppercase font-bold tracking-widest text-text-secondary hover:text-brand-accent hover:border-brand-accent transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent shadow-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
