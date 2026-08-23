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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="flex h-full max-h-[80vh] w-full max-w-xl flex-col rounded-lg border border-zinc-900 bg-zinc-950 shadow-2xl transition-colors overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-900 p-5">
          <div>
            <h2 className="text-sm font-semibold text-white">Import Repositories</h2>
            <p className="mt-1 text-[10px] text-zinc-500">
              Select a repository from your GitHub profile to import and analyze.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1.5 text-zinc-550 hover:bg-zinc-900 hover:text-white transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {error && (
            <div className="mb-4 rounded border border-red-900/50 bg-red-950/20 p-3 text-xs text-red-400">
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
              className="w-full rounded border border-zinc-900 bg-zinc-950 py-2 pl-9 pr-4 text-xs text-white outline-none placeholder:text-zinc-550 focus:border-zinc-800 transition-colors"
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-550"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>

          {/* Repos list */}
          {loading ? (
            <div className="flex h-48 flex-col items-center justify-center gap-2">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              <span className="text-xs text-zinc-500">Loading repositories...</span>
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center text-center">
              <span className="text-xs font-medium text-zinc-400">No repositories found</span>
              <span className="mt-1 text-[10px] text-zinc-650">Try adjusting your search query.</span>
            </div>
          ) : (
            <div className="grid gap-2">
              {filteredRepos.map((repo) => {
                const isImported = importedIds.includes(repo.id);
                const isImporting = importingId === repo.id;

                return (
                  <div
                    key={repo.id}
                    className="flex items-center justify-between gap-4 rounded border border-zinc-900 bg-zinc-950/20 p-3 transition-colors hover:bg-zinc-900/30"
                  >
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-xs text-zinc-200 truncate">
                        {repo.name}
                      </h4>
                      <p className="mt-0.5 text-[10px] text-zinc-500 line-clamp-1">
                        {repo.description || "No description provided."}
                      </p>
                      <div className="mt-1.5 flex items-center gap-3">
                        {repo.language && (
                          <span className="inline-flex items-center gap-1 text-[9px] text-zinc-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                            {repo.language}
                          </span>
                        )}
                        <span className="text-[9px] text-zinc-500">
                          branch: {repo.default_branch}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleImport(repo.id)}
                      disabled={isImported || isImporting}
                      className={`rounded px-3 py-1.5 text-[10px] font-semibold transition-all shrink-0 ${
                        isImported
                          ? "bg-zinc-900 text-emerald-400 border border-zinc-800 cursor-default"
                          : isImporting
                          ? "bg-zinc-900 text-zinc-600 border border-zinc-850 cursor-not-allowed"
                          : "bg-white text-zinc-950 hover:bg-zinc-200 cursor-pointer"
                      }`}
                    >
                      {isImported ? "Imported" : isImporting ? "Importing..." : "Import"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-zinc-900 bg-zinc-950 p-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded border border-zinc-800 bg-zinc-900/30 px-3.5 py-1.5 text-[10px] font-semibold text-zinc-400 hover:text-white hover:bg-zinc-900 hover:border-zinc-700 transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
