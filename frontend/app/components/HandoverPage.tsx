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

  // Section 1: Project Overview cleaner
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

  // Section 2: Start Here detailed onboarding points with concise context
  const getStartHereDetailed = () => {
    const list: { name: string; desc: string }[] = [];

    if (!directoryStructure) {
      if (repo.language) {
        list.push({
          name: `${repo.language} source files`,
          desc: `Main source codebase compiled in ${repo.language}.`
        });
      }
      list.push({
        name: `Repository root files`,
        desc: `Examine files on the default branch: '${repo.default_branch}'.`
      });
      if (loadingStructure) {
        list.push({
          name: "Loading layout...",
          desc: "Scanning codebase structure from GitHub API."
        });
      } else {
        list.push({
          name: "Structure analysis limited",
          desc: "Repository directory identified during structure analysis."
        });
      }
      return list;
    }

    const files = directoryStructure.map((f) => f.name.toLowerCase());
    const folders = directoryStructure.filter((f) => f.type === "dir").map((f) => f.name.toLowerCase());

    if (files.includes("readme.md")) {
      list.push({
        name: "README.md",
        desc: "Understand the project's purpose and setup instructions."
      });
    }

    if (folders.includes("frontend")) {
      list.push({
        name: "frontend/",
        desc: "Application interface and client-side code."
      });
    } else if (folders.includes("client")) {
      list.push({
        name: "client/",
        desc: "Application interface and client-side code."
      });
    }

    if (folders.includes("backend")) {
      list.push({
        name: "backend/",
        desc: "API and server-side functionality."
      });
    } else if (folders.includes("server")) {
      list.push({
        name: "server/",
        desc: "API and server-side functionality."
      });
    }

    if (files.includes("package.json")) {
      list.push({
        name: "package.json",
        desc: "NodeJS project settings, scripts, and runtime commands."
      });
    }

    if (files.includes("requirements.txt") || files.includes("pyproject.toml")) {
      list.push({
        name: "requirements.txt",
        desc: "Python dependencies configuration file."
      });
    }

    if (files.includes("go.mod")) {
      list.push({
        name: "go.mod",
        desc: "Go modules configuration file."
      });
    }

    // Source folders
    const srcDirs = directoryStructure.filter(f => f.type === "dir" && ["src", "app", "lib", "components", "pages"].includes(f.name.toLowerCase()));
    srcDirs.forEach(dir => {
      if (["frontend", "backend", "client", "server"].includes(dir.name.toLowerCase())) return;
      list.push({
        name: `${dir.name}/`,
        desc: "Primary source directory identified during structure analysis."
      });
    });

    // Test folders
    const testDirs = directoryStructure.filter(f => f.type === "dir" && ["tests", "test", "spec"].includes(f.name.toLowerCase()));
    testDirs.forEach(dir => {
      list.push({
        name: `${dir.name}/`,
        desc: "Test suite directory. Run tests to confirm local environment stability."
      });
    });

    // Config files
    const configFiles = directoryStructure.filter(f => f.type === "file" && (f.name.includes(".env") || f.name.includes("config")));
    configFiles.forEach(file => {
      list.push({
        name: file.name,
        desc: "Environment or project configuration file."
      });
    });

    if (list.length === 0) {
      list.push({
        name: "Repository root files",
        desc: "Inspect root directory files to locate entry scripts."
      });
    }

    return list;
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
  const startHerePoints = getStartHereDetailed();
  const importantAreas = getImportantAreas();
  const knownRisks = getKnownRisks();

  // Mapping states to progress indicator
  const getStepStatus = (stepIndex: number) => {
    if (handoverState === "not_started") {
      if (stepIndex === 1) return "active";
      return "pending";
    }
    if (handoverState === "in_progress") {
      if (stepIndex <= 3) return "active";
      return "pending";
    }
    // prepared state
    if (stepIndex <= 3) return "complete";
    return "active";
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-12 select-none">
      {/* 1. HANDOVER HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between mb-10 pb-8 border-b border-border-muted">
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
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 sm:gap-4 mt-2 font-outfit">
              <h1 className="text-3xl text-text-primary font-extrabold tracking-tight">Repository Handover</h1>
              <span className="text-sm text-brand-accent font-mono font-bold">/ {repo.name}</span>
            </div>
            <p className="text-xs text-text-secondary font-sans mt-1">Prepared for the developer who comes next.</p>
          </div>
        </div>

        {/* Clear Status Badge */}
        <div className="shrink-0">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 text-[10px] font-mono font-bold uppercase tracking-wider border rounded-none ${
            handoverState === "prepared"
              ? "text-semantic-healthy border-semantic-healthy/25 bg-semantic-healthy/5"
              : handoverState === "in_progress"
              ? "text-brand-accent border-brand-accent/25 bg-brand-accent/5 animate-pulse"
              : "text-text-muted border-border-muted bg-surface-secondary"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${
              handoverState === "prepared"
                ? "bg-semantic-healthy"
                : handoverState === "in_progress"
                ? "bg-brand-accent"
                : "bg-text-muted"
            }`} />
            {handoverState === "prepared"
              ? "READY FOR HANDOVER"
              : handoverState === "in_progress"
              ? "IN PROGRESS"
              : "NOT STARTED"}
          </span>
        </div>
      </div>

      {/* 2. HANDOVER PROGRESS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-6 border-b border-border-muted mb-10 select-none">
        {[
          { step: "01", label: "Understand", status: getStepStatus(1) },
          { step: "02", label: "Review", status: getStepStatus(2) },
          { step: "03", label: "Add Context", status: getStepStatus(3) },
          { step: "04", label: "Ready", status: getStepStatus(4) },
        ].map((item, idx) => (
          <div key={idx} className={`flex flex-col border-l-2 pl-4 py-1.5 ${
            item.status === "complete"
              ? "border-semantic-healthy text-semantic-healthy"
              : item.status === "active"
              ? "border-brand-accent text-text-primary font-bold"
              : "border-border-muted text-text-muted"
          }`}>
            <span className="text-[9px] font-mono tracking-wider font-bold">
              {item.step} {item.status === "complete" ? "✓" : ""}
            </span>
            <span className="text-xs uppercase tracking-widest font-outfit mt-1">
              {item.label}
            </span>
          </div>
        ))}
      </div>

      {/* 3. INCOMING DEVELOPER VIEW & HANDOVER STATUS CARD */}
      {handoverState === "prepared" ? (
        <div className="border border-semantic-healthy/25 bg-semantic-healthy/5 p-8 mb-10 text-left relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-[radial-gradient(circle_at_100%_0%,rgba(10,108,74,0.05)_0%,transparent_70%)] pointer-events-none" />
          <h2 className="text-xl font-outfit text-semantic-healthy font-extrabold tracking-tight mb-3">
            READY FOR THE NEXT DEVELOPER
          </h2>
          <p className="text-xs text-text-secondary leading-relaxed max-w-2xl mb-5 font-sans">
            The knowledge package has been reviewed and is ready for the incoming developer. Below is a summary of what the recipient receives:
          </p>
          <div className="grid gap-2 sm:grid-cols-2 text-xs font-mono text-text-primary">
            <div className="flex items-center gap-2">
              <span className="text-semantic-healthy select-none font-bold">✓</span> Project overview
            </div>
            <div className="flex items-center gap-2">
              <span className="text-semantic-healthy select-none font-bold">✓</span> Starting points
            </div>
            <div className="flex items-center gap-2">
              <span className="text-semantic-healthy select-none font-bold">✓</span> Important areas
            </div>
            {knownRisks.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-semantic-healthy select-none font-bold">✓</span> Current risks
              </div>
            )}
            {developerNotes.trim() && (
              <div className="flex items-center gap-2">
                <span className="text-semantic-healthy select-none font-bold">✓</span> Developer notes
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="border border-border-muted bg-surface-base p-8 mb-10 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="flex-1">
              <span className="text-[9px] font-mono tracking-widest uppercase text-text-muted font-bold block mb-2">HANDOVER ACTION</span>
              {handoverState === "not_started" && (
                <p className="text-sm text-text-secondary font-sans leading-relaxed">
                  Prepare a structured knowledge package for the next developer who takes over this repository. It analyzes project layouts and repository files automatically.
                </p>
              )}
              {handoverState === "in_progress" && (
                <p className="text-sm text-text-secondary font-sans leading-relaxed">
                  You are building the handover guide. Add your custom context in **From the Previous Developer** below, review the package contents, and complete the package when ready.
                </p>
              )}
            </div>

            <div className="shrink-0 flex items-center gap-3">
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
            </div>
          </div>
        </div>
      )}

      {/* 6. HANDOVER CHECKLIST */}
      {(handoverState === "in_progress" || handoverState === "prepared") && (
        <div className="border border-border-muted bg-surface-base p-6 mb-10 shadow-sm select-none">
          <div className="border-b border-border-muted/65 pb-3 mb-4">
            <h3 className="text-xs font-mono font-bold uppercase tracking-widest text-text-primary">
              Handover Checklist
            </h3>
            <span className="text-[9px] text-text-muted font-sans mt-1 block">
              Steps verified by the outgoing developer before packaging:
            </span>
          </div>

          <div className="space-y-3">
            {[
              { label: "Project overview reviewed", checked: true },
              { label: "Important areas reviewed", checked: handoverState === "prepared" || !!directoryStructure },
              { label: "Known risks reviewed", checked: handoverState === "prepared" || (health !== null || dormancy !== null) },
              { label: "Developer notes added", checked: handoverState === "prepared" || developerNotes.trim().length > 0 },
              { label: "Handover ready", checked: handoverState === "prepared" },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-3 text-xs font-sans">
                <span className={`h-4 w-4 border flex items-center justify-center font-bold text-[9px] shrink-0 ${
                  item.checked
                    ? "border-semantic-healthy text-semantic-healthy bg-semantic-healthy/5"
                    : "border-border-strong text-transparent"
                }`}>
                  {item.checked ? "✓" : ""}
                </span>
                <span className={item.checked && handoverState === "prepared" ? "text-text-secondary line-through opacity-70" : "text-text-primary"}>
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Content Header */}
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
              <p className="text-xs text-text-secondary font-sans leading-relaxed whitespace-pre-line select-text">
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

        {/* 2. START HERE EXPERIENCE (actionable, numbered) */}
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
              <p className="text-xs text-text-secondary font-sans leading-relaxed select-none">
                If you just inherited this repository, here is where you should look first:
              </p>
              <div className="space-y-6">
                {startHerePoints.map((item, index) => (
                  <div key={index} className="flex gap-4">
                    <span className="text-xs font-mono font-bold text-brand-accent mt-0.5 select-none">
                      {(index + 1).toString().padStart(2, "0")}
                    </span>
                    <div>
                      <strong className="text-xs font-mono text-text-primary bg-surface-secondary px-2 py-0.5 border border-border-muted select-text">
                        {item.name}
                      </strong>
                      <p className="text-xs text-text-secondary mt-1.5 font-sans leading-relaxed select-text">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
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
                <p className="text-[11px] text-text-secondary font-sans leading-relaxed select-text">
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
            <p className="text-xs text-text-secondary font-sans leading-relaxed">
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
                <li key={index} className="text-xs border border-semantic-critical/25 bg-semantic-critical/5 text-text-secondary p-3 leading-relaxed font-sans flex items-start gap-2.5">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4 text-semantic-critical shrink-0 mt-0.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="select-text">{risk}</span>
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

        {/* 5. DEVELOPER NOTES (FROM THE PREVIOUS DEVELOPER) */}
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
            <h3 className="text-sm font-outfit text-text-primary font-bold">
              {handoverState === "prepared" ? "From the Previous Developer" : "Developer Notes"}
            </h3>
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
            <div className="space-y-4">
              <div className="bg-surface-secondary border border-border-muted p-4 space-y-1.5 select-none">
                <span className="text-[9px] font-mono text-text-muted uppercase font-bold block">Prompts for Context:</span>
                <ul className="text-xs text-text-secondary space-y-1 font-sans">
                  <li>• What were you working on?</li>
                  <li>• What should the next developer understand first?</li>
                  <li>• Is there anything that isn't obvious from the code?</li>
                  <li>• What should they be careful about?</li>
                </ul>
              </div>
              <div className="space-y-2">
                <label htmlFor="developer-notes-input" className="text-[9px] font-mono uppercase text-text-muted tracking-wider block font-bold">
                  Handover Notes Input
                </label>
                <textarea
                  id="developer-notes-input"
                  value={developerNotes}
                  onChange={(e) => onNotesChange(e.target.value)}
                  placeholder="Share details on architecture, recent WIP features, custom integrations, active branch contexts, or staging configuration gotchas..."
                  className="w-full h-40 p-3 text-xs font-sans border border-border-strong bg-surface-base text-text-primary placeholder:text-text-muted focus:border-brand-accent focus:outline-none transition-all duration-150 resize-y"
                />
                <span className="text-[9px] font-mono text-text-secondary block text-right">
                  {developerNotes.length} characters written (Saved locally)
                </span>
              </div>
            </div>
          )}

          {handoverState === "prepared" && (
            <div className="border border-semantic-healthy/20 bg-semantic-healthy/5 p-5">
              <span className="text-[9px] font-mono uppercase text-semantic-healthy tracking-wider block mb-2 font-bold select-none">OUTGOING DEVELOPER NOTES</span>
              {developerNotes.trim() ? (
                <div className="text-xs font-mono text-text-primary leading-relaxed whitespace-pre-wrap select-text">
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

        {/* 7. NEXT DEVELOPER SECTION (FOR THE NEXT DEVELOPER) */}
        {handoverState === "prepared" && (
          <div className="border border-border-muted bg-surface-secondary/40 p-6 rounded-none shadow-sm">
            <div className="border-b border-border-muted/65 pb-3 mb-4 select-none">
              <h3 className="text-sm font-outfit text-text-primary font-bold">For the Next Developer</h3>
              <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Onboarding Path</span>
            </div>
            <div className="space-y-3.5">
              {[
                "Read the project overview.",
                "Review the Start Here files.",
                "Review current risks.",
                "Read the previous developer's notes.",
                "Run the project locally.",
                "Make your first change.",
              ].map((step, idx) => (
                <div key={idx} className="flex gap-3 text-xs leading-relaxed font-sans text-text-secondary">
                  <span className="font-mono text-brand-accent font-bold select-none">{idx + 1}.</span>
                  <span className="select-text">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Prepare/Edit controls at the bottom for Prepared state */}
      {handoverState === "prepared" && (
        <div className="mt-12 pt-6 border-t border-border-muted flex gap-4 select-none">
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
        </div>
      )}
    </div>
  );
}
