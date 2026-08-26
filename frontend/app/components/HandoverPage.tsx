"use client";

import { useEffect, useState } from "react";
import {
  RepositoryResponse,
  HealthResponse,
  DormancyResponse,
  AIInsightsResponse,
} from "@/lib/api";

interface HandoverPageProps {
  repo: RepositoryResponse;
  health: HealthResponse | null;
  dormancy: DormancyResponse | null;
  aiInsights: AIInsightsResponse | null;
  onBack: () => void;
  handoverState: "not_started" | "in_progress" | "prepared";
  developerNotes: string;
  onStateChange: (state: "not_started" | "in_progress" | "prepared") => void;
  onNotesChange: (notes: string) => void;
}

interface GithubContentItem {
  name: string;
  type: string;
  path: string;
}

export default function HandoverPage({
  repo,
  health,
  dormancy,
  aiInsights,
  onBack,
  handoverState,
  developerNotes,
  onStateChange,
  onNotesChange,
}: HandoverPageProps) {
  const [readmeContent, setReadmeContent] = useState<string | null>(null);
  const [directoryStructure, setDirectoryStructure] = useState<GithubContentItem[] | null>(null);
  const [loadingReadme, setLoadingReadme] = useState(false);
  const [loadingStructure, setLoadingStructure] = useState(false);

  // Fetch README and file listings on mount or repo change
  useEffect(() => {
    const fetchRepoContext = async () => {
      if (!repo || !repo.full_name) return;

      setLoadingReadme(true);
      setLoadingStructure(true);

      // 1. Fetch README
      try {
        const readmeRes = await fetch(`https://api.github.com/repos/${repo.full_name}/readme`);
        if (readmeRes.ok) {
          const data = await readmeRes.json();
          if (data && data.content) {
            // Decodes base64 content
            const decoded = atob(data.content.replace(/\s/g, ""));
            setReadmeContent(decoded);
          }
        }
      } catch (e) {
        console.error("Failed to fetch README from GitHub API:", e);
      } finally {
        setLoadingReadme(false);
      }

      // 2. Fetch directory file structure
      try {
        const structureRes = await fetch(`https://api.github.com/repos/${repo.full_name}/contents`);
        if (structureRes.ok) {
          const data = await structureRes.json();
          if (Array.isArray(data)) {
            setDirectoryStructure(
              data.map((item: any) => ({
                name: item.name,
                type: item.type,
                path: item.path,
              }))
            );
          }
        }
      } catch (e) {
        console.error("Failed to fetch directory contents from GitHub API:", e);
      } finally {
        setLoadingStructure(false);
      }
    };

    fetchRepoContext();
  }, [repo.full_name]);

  // Section 1: Project Overview
  const getProjectOverview = () => {
    if (readmeContent) {
      let cleaned = readmeContent
        .replace(/#+\s+.+/g, "") // Remove headers
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // Remove markdown links
        .replace(/[*_`]/g, "") // Remove bold/italic formatting
        .replace(/<!--[\s\S]*?-->/g, "") // Remove comments
        .replace(/\s+/g, " ") // Collapse spaces
        .trim();

      if (cleaned.length > 350) {
        return cleaned.substring(0, 350) + "...";
      } else if (cleaned.length > 50) {
        return cleaned;
      }
    }

    if (repo.description) {
      return repo.description;
    }

    return "No project description or README file could be loaded. You can manually enter details in the Developer Notes below.";
  };

  // Section 2: Start Here
  const getStartHerePoints = () => {
    const points: string[] = [];

    if (!directoryStructure) {
      points.push(`Primary language: ${repo.language || "Not specified"}. Look for standard project entry points.`);
      points.push(`Default branch: Inspect branch '${repo.default_branch}' for instructions.`);
      if (loadingStructure) {
        points.push("Fetching directory layout from GitHub...");
      } else {
        points.push("Directory listing is currently unavailable (rate-limited or private repository).");
      }
      return points;
    }

    const files = directoryStructure.map((f) => f.name.toLowerCase());
    const folders = directoryStructure.filter((f) => f.type === "dir").map((f) => f.name.toLowerCase());

    if (files.includes("readme.md")) {
      points.push("README.md: Found at root. Examine this file first for compilation, setup, and deployment notes.");
    }

    if (folders.includes("frontend") && folders.includes("backend")) {
      points.push("Frontend & Backend Separation: Found distinct frontend/backend environments. Verify the setup of both separate services.");
    }

    if (files.includes("package.json")) {
      points.push("NodeJS Environment: Found package.json. Examine scripts, package configurations, and dependency lists.");
      if (files.includes("tsconfig.json")) {
        points.push("TypeScript Config: tsconfig.json is active. The application builds with static types.");
      }
    }

    if (files.includes("requirements.txt") || files.includes("pyproject.toml") || files.includes("pipfile")) {
      points.push("Python Environment: Python configuration files are present in the root. Verify dependencies setup.");
    }

    if (files.includes("go.mod")) {
      points.push("Go Environment: Found go.mod. Compile using standard Go directives.");
    }

    const srcFolder = directoryStructure.find((f) => f.type === "dir" && ["src", "app", "lib", "components"].includes(f.name.toLowerCase()));
    if (srcFolder) {
      points.push(`${srcFolder.name}/: The main codebase directory is located under /${srcFolder.name}. Look here to inspect logic.`);
    }

    const configFiles = directoryStructure.filter((f) => f.type === "file" && (f.name.includes(".env") || f.name.includes("config") || f.name.includes("setting")));
    if (configFiles.length > 0) {
      const names = configFiles.map((c) => c.name).join(", ");
      points.push(`Configuration Templates: Found configuration templates (${names}). Duplicate and configure before executing.`);
    }

    const testFolder = directoryStructure.find((f) => f.type === "dir" && ["tests", "test", "spec"].includes(f.name.toLowerCase()));
    if (testFolder) {
      points.push(`${testFolder.name}/: Found test suite folder. Run test scripts to verify the local build environment.`);
    }

    if (points.length === 0) {
      points.push("Inspect the root directory files to locate entry scripts.");
    }

    return points;
  };

  // Section 3: Important Areas
  const getImportantAreas = () => {
    const areas: { title: string; description: string }[] = [];

    if (!directoryStructure) {
      if (repo.language) {
        areas.push({
          title: `${repo.language} Codebase`,
          description: `The main logic is built in ${repo.language}. Explore files under the default branch: ${repo.default_branch}.`,
        });
      } else {
        areas.push({
          title: "Core Source Files",
          description: `Analyze files located in default branch '${repo.default_branch}' to map out project logic.`,
        });
      }
      return areas;
    }

    const folders = directoryStructure.filter((f) => f.type === "dir").map((f) => f.name.toLowerCase());
    const files = directoryStructure.map((f) => f.name.toLowerCase());

    if (folders.includes("frontend") || folders.includes("public") || folders.includes("client") || (files.includes("package.json") && repo.language !== "Python")) {
      areas.push({
        title: "Frontend Layer",
        description: "Manages page layouts, user interfaces, stylesheet settings, and client navigation routines.",
      });
    }

    if (folders.includes("backend") || folders.includes("server") || folders.includes("api") || folders.includes("app") || files.includes("requirements.txt") || files.includes("go.mod")) {
      areas.push({
        title: "Backend Layer & Server Services",
        description: "Controls the main business rules, database connection layers, web servers, and API routes.",
      });
    }

    if (folders.includes("db") || folders.includes("database") || folders.includes("migrations") || folders.includes("prisma") || files.includes("alembic.ini")) {
      areas.push({
        title: "Database Schemas & Migrations",
        description: "Stores ORM model definitions, database mappings, and structured SQL/migration updates.",
      });
    }

    if (folders.includes("tests") || folders.includes("test") || folders.includes("spec")) {
      areas.push({
        title: "Testing Architecture",
        description: "Houses regression check scripts, unit assertions, and automated coverage validation suites.",
      });
    }

    const hasAI = directoryStructure.some((f) =>
      f.name.toLowerCase().includes("ai") ||
      f.name.toLowerCase().includes("openai") ||
      f.name.toLowerCase().includes("llm") ||
      f.name.toLowerCase().includes("model")
    );
    if (hasAI) {
      areas.push({
        title: "Artificial Intelligence Integrations",
        description: "Connects LLM API helpers, configures model prompts, or coordinates cognitive responses.",
      });
    }

    if (areas.length === 0) {
      areas.push({
        title: "Application Core",
        description: "The primary repository folders containing codebase scripts and logic.",
      });
    }

    return areas;
  };

  // Section 5: Known Risks
  const getKnownRisks = () => {
    const risks: string[] = [];

    if (health && health.health_score < 70) {
      risks.push(`Low Health Index: The repository has a health rating of ${health.health_score}/100 (Grade ${health.grade}). This indicates issues with documentation, activity, or code organization.`);
    }

    if (dormancy && dormancy.status.toLowerCase() !== "active") {
      risks.push(`Maintenance Delay: Marked as ${dormancy.status} (${dormancy.days_since_last_push} days since the last push). Development has stalled or is inactive.`);
    }

    if (repo.open_issues !== null && repo.open_issues > 30) {
      risks.push(`Significant Issue Backlog: The repository has ${repo.open_issues} open issues, indicating potential bugs or unresolved tasks.`);
    }

    return risks;
  };

  const projectOverview = getProjectOverview();
  const startHerePoints = getStartHerePoints();
  const importantAreas = getImportantAreas();
  const knownRisks = getKnownRisks();

  return (
    <div className="mx-auto max-w-5xl px-6 py-12 select-none">
      {/* Header & Back Button */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between mb-10">
        <div className="flex items-baseline gap-4">
          <button
            onClick={onBack}
            className="rounded-none border border-border-muted bg-surface-secondary p-1.5 text-text-secondary hover:text-text-primary hover:border-border-strong transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
            title="Back to Repository Details"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-3.5 w-3.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-text-muted uppercase">SECOND COMMIT</span>
            <div className="flex items-baseline gap-2.5 mt-1.5 font-outfit">
              <h1 className="text-3xl text-text-primary font-extrabold tracking-tight">Repository Handover</h1>
              <span className="text-xs text-brand-accent font-mono font-bold">/ {repo.name}</span>
            </div>
            <p className="text-[10px] text-text-muted font-mono mt-1">Branch: {repo.default_branch}</p>
          </div>
        </div>
      </div>

      {/* Handover Status Section */}
      <div className="border border-border-muted bg-surface-base p-8 mb-12 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex-1">
            <span className="text-[9px] font-mono tracking-widest uppercase text-text-muted font-bold block mb-2">HANDOVER STATUS</span>
            {handoverState === "not_started" && (
              <div>
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-none border border-border-strong bg-surface-secondary text-text-secondary text-[10px] font-mono font-bold uppercase mb-4">
                  <span className="h-1.5 w-1.5 rounded-full bg-text-muted" />
                  Not prepared yet
                </div>
                <p className="text-sm text-text-secondary font-sans leading-relaxed">
                  Prepare a structured knowledge package for the next developer taking over this repository. It derives project history and repository files automatically.
                </p>
              </div>
            )}
            {handoverState === "in_progress" && (
              <div>
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-none border border-brand-accent/30 bg-brand-accent/10 text-brand-accent text-[10px] font-mono font-bold uppercase mb-4 animate-pulse">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />
                  In progress
                </div>
                <p className="text-sm text-text-secondary font-sans leading-relaxed">
                  You are drafting the handover guide. Add your custom context in the **Developer Notes** section below, review the parsed information, and complete the package when ready.
                </p>
              </div>
            )}
            {handoverState === "prepared" && (
              <div>
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-none border border-semantic-healthy/30 bg-semantic-healthy/10 text-semantic-healthy text-[10px] font-mono font-bold uppercase mb-4">
                  <span className="h-1.5 w-1.5 rounded-full bg-semantic-healthy" />
                  Prepared & Ready
                </div>
                <p className="text-sm text-text-secondary font-sans leading-relaxed">
                  Your repository handover package is ready! This package is frozen in its current state. You can share this with incoming developers or reset it to modify contents.
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col gap-3 justify-end shrink-0">
            {handoverState === "not_started" && (
              <button
                onClick={() => onStateChange("in_progress")}
                className="flex items-center justify-center gap-2.5 rounded-none bg-text-primary border border-text-primary text-white hover:bg-brand-accent hover:border-brand-accent px-6 py-3 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
              >
                Start Handover
              </button>
            )}
            {handoverState === "in_progress" && (
              <button
                onClick={() => onStateChange("prepared")}
                className="flex items-center justify-center gap-2.5 rounded-none bg-brand-accent border border-brand-accent text-white hover:bg-text-primary hover:border-text-primary px-6 py-3 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer shadow-sm hover:shadow-md outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
              >
                Complete Handover
              </button>
            )}
            {handoverState === "prepared" && (
              <>
                <button
                  onClick={() => onStateChange("in_progress")}
                  className="flex items-center justify-center gap-2.5 rounded-none border border-border-strong bg-surface-secondary text-text-secondary hover:text-text-primary hover:border-text-primary px-6 py-2.5 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
                >
                  Edit Handover
                </button>
                <button
                  onClick={() => {
                    if (confirm("Are you sure you want to reset the handover? This will clear all developer notes.")) {
                      onNotesChange("");
                      onStateChange("not_started");
                    }
                  }}
                  className="flex items-center justify-center gap-2.5 rounded-none border border-semantic-critical/20 bg-surface-base text-semantic-critical hover:bg-semantic-critical/5 px-6 py-2.5 text-[10px] font-mono uppercase tracking-widest transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
                >
                  Reset Handover
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Sections Header */}
      <div className="mb-8 border-b border-border-muted pb-4">
        <h2 className="text-[10px] font-mono font-bold uppercase tracking-widest text-text-primary">
          {handoverState === "prepared" ? "Handover Package Contents" : "What Will Be Included"}
        </h2>
        <p className="text-[10px] text-text-secondary mt-1 font-sans">
          {handoverState === "prepared"
            ? "Frozen snapshots and developer notes for the next engineer."
            : "The knowledge modules that make up a complete repository handover."}
        </p>
      </div>

      {/* Handover modules stack */}
      <div className="space-y-8">
        {/* 1. PROJECT OVERVIEW */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Project Overview</h3>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Repository Context</span>
          </div>
          {loadingReadme ? (
            <div className="py-4 text-center font-mono text-[10px] text-text-muted uppercase animate-pulse">
              Extracting README information...
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-text-secondary font-sans leading-relaxed whitespace-pre-line">
                {projectOverview}
              </p>
              <div className="flex flex-wrap gap-4 pt-3 border-t border-border-muted/50 select-none">
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Language</span>
                  <span className="text-xs font-mono text-text-primary font-bold">{repo.language || "None"}</span>
                </div>
                <div className="border-l border-border-muted/50 pl-4">
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Size</span>
                  <span className="text-xs font-mono text-text-primary font-bold">
                    {repo.size ? `${(repo.size / 1024).toFixed(1)} MB` : "—"}
                  </span>
                </div>
                <div className="border-l border-border-muted/50 pl-4">
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Default Branch</span>
                  <span className="text-xs font-mono text-text-primary font-bold">{repo.default_branch}</span>
                </div>
                <div className="border-l border-border-muted/50 pl-4">
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Created</span>
                  <span className="text-xs font-mono text-text-primary font-bold">
                    {repo.created_at ? new Date(repo.created_at).toLocaleDateString() : "—"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 2. START HERE */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Start Here</h3>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Onboarding Path</span>
          </div>
          {loadingStructure ? (
            <div className="py-4 text-center font-mono text-[10px] text-text-muted uppercase animate-pulse">
              Analyzing repository structure...
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-text-primary font-sans">
                Below are the recommended entry points and directories discovered in the workspace to begin onboarding:
              </p>
              <ul className="space-y-2.5">
                {startHerePoints.map((point, index) => {
                  const parts = point.split(":");
                  const header = parts[0];
                  const details = parts.slice(1).join(":");
                  return (
                    <li key={index} className="text-xs text-text-secondary leading-relaxed font-sans flex items-start gap-2">
                      <span className="text-brand-accent font-bold select-none mt-0.5">•</span>
                      <span>
                        {details ? (
                          <>
                            <strong className="font-mono text-text-primary text-[11px] bg-surface-secondary px-1.5 py-0.5 border border-border-muted mr-1.5 font-bold">
                              {header}
                            </strong>
                            {details}
                          </>
                        ) : (
                          point
                        )}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>

        {/* 3. IMPORTANT AREAS */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Important Areas</h3>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Codebase Domains</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {importantAreas.map((area, index) => (
              <div key={index} className="border border-border-muted bg-surface-secondary/40 p-4">
                <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-text-primary block mb-1">
                  {area.title}
                </span>
                <p className="text-[11px] text-text-secondary font-sans leading-relaxed">
                  {area.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* 4. DEVELOPMENT HISTORY */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Development History</h3>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Activity Log</span>
          </div>
          <div className="space-y-3">
            <p className="text-xs text-text-primary font-sans leading-relaxed">
              Development history will be available in a future handover analysis.
            </p>
            {repo.pushed_at && (
              <div className="border-t border-border-muted/50 pt-3 select-none flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />
                <span className="text-[10px] font-mono text-text-secondary">
                  Last active push: <strong className="text-text-primary">{new Date(repo.pushed_at).toLocaleDateString()}</strong> ({dormancy?.days_since_last_push ?? 0} days ago)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 5. KNOWN RISKS */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Known Risks</h3>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Maintenance Warnings</span>
          </div>
          {knownRisks.length > 0 ? (
            <ul className="space-y-3">
              {knownRisks.map((risk, index) => (
                <li key={index} className="text-xs border border-semantic-critical/20 bg-semantic-critical/5 text-text-secondary p-3 leading-relaxed font-sans flex items-start gap-2.5">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4 text-semantic-critical shrink-0 mt-0.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-text-muted font-sans italic">
              No handover risks have been identified yet.
            </p>
          )}
        </div>

        {/* 6. UNFINISHED WORK */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Unfinished Work</h3>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">In-Flight Tasks</span>
          </div>
          <p className="text-xs text-text-muted font-sans italic">
            No unfinished work has been identified yet.
          </p>
        </div>

        {/* 7. DEVELOPER NOTES */}
        <div
          className={`border p-6 rounded-none transition-all duration-200 shadow-sm ${
            handoverState === "prepared"
              ? "border-semantic-healthy/20 bg-surface-base"
              : handoverState === "in_progress"
              ? "border-brand-accent/30 bg-surface-base"
              : "border-dashed border-border-strong bg-surface-secondary/20"
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <h3 className="text-sm font-outfit text-text-primary font-bold">Developer Notes</h3>
            <span className={`text-[9px] font-mono tracking-wider uppercase ${
              handoverState === "prepared"
                ? "text-semantic-healthy"
                : handoverState === "in_progress"
                ? "text-brand-accent"
                : "text-text-muted"
            }`}>
              {handoverState === "prepared" ? "Saved" : handoverState === "in_progress" ? "Interactive" : "Manual additions"}
            </span>
          </div>

          <p className="text-xs text-text-secondary font-sans leading-relaxed mb-4">
            Provide additional custom project context that cannot be inferred automatically from repository files.
          </p>

          {handoverState === "not_started" && (
            <div className="border border-border-muted bg-surface-secondary p-4 text-center select-none">
              <p className="text-xs text-text-muted font-mono uppercase">Start Handover to enter notes</p>
            </div>
          )}

          {handoverState === "in_progress" && (
            <div className="space-y-2">
              <label htmlFor="developer-notes-input" className="text-[9px] font-mono uppercase text-text-muted tracking-wider block font-bold">
                Project Context & Notes for the Next Developer
              </label>
              <textarea
                id="developer-notes-input"
                value={developerNotes}
                onChange={(e) => onNotesChange(e.target.value)}
                placeholder="Share architecture details, deployment gotchas, custom system hooks, credentials locations (avoid plain-text secrets), or team contact details..."
                className="w-full h-36 p-3 text-xs font-sans border border-border-strong bg-surface-base text-text-primary placeholder:text-text-muted focus:border-brand-accent focus:outline-none transition-all duration-150 resize-y"
              />
              <span className="text-[9px] font-mono text-text-secondary block text-right">
                {developerNotes.length} characters written (Saved locally)
              </span>
            </div>
          )}

          {handoverState === "prepared" && (
            <div className="border border-semantic-healthy/20 bg-semantic-healthy/5 p-5">
              <span className="text-[9px] font-mono uppercase text-semantic-healthy tracking-wider block mb-2 font-bold select-none">OUTGOING DEVELOPER NOTES</span>
              {developerNotes.trim() ? (
                <div className="text-xs font-mono text-text-primary leading-relaxed whitespace-pre-wrap">
                  {developerNotes}
                </div>
              ) : (
                <p className="text-xs font-sans text-text-muted italic">
                  No custom developer notes were added to this handover.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
