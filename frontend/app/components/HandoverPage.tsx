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
  revivalIntent: string;
  onStateChange: (state: "not_started" | "in_progress" | "prepared") => void;
  onNotesChange: (notes: string) => void;
  onRevivalIntentChange: (intent: string) => void;
}

interface GithubContentItem {
  name: string;
  type: string;
  path: string;
}

const RenderHonestyBadge = ({ state }: { state: "confirmed" | "signal" | "unavailable" }) => {
  switch (state) {
    case "confirmed":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider text-semantic-healthy border border-semantic-healthy/20 bg-semantic-healthy/5 rounded-none select-none">
          ● Confirmed Info
        </span>
      );
    case "signal":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider text-brand-accent border border-brand-accent/20 bg-brand-accent/5 rounded-none select-none">
          ▲ Inferred Signal
        </span>
      );
    case "unavailable":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider text-text-muted border border-border-muted bg-surface-secondary rounded-none select-none">
          ✕ Unavailable
        </span>
      );
  }
};

const REVIVAL_INTENT_OPTIONS = [
  {
    key: "looking_for_maintainer",
    title: "Looking for a maintainer",
    description: "Someone who can take primary responsibility for continuing the project."
  },
  {
    key: "looking_for_contributors",
    title: "Looking for contributors",
    description: "The owner wants other developers to contribute while retaining ownership."
  },
  {
    key: "looking_for_collaborator",
    title: "Looking for a collaborator",
    description: "The owner wants to work together with another developer."
  },
  {
    key: "take_over",
    title: "Looking for someone to take over",
    description: "The owner is open to another developer taking over the project's future direction."
  },
  {
    key: "future_revival",
    title: "Preserving for future revival",
    description: "The owner is not actively looking for someone right now, but wants the project's context preserved for future revival."
  }
];

export default function HandoverPage({
  repo,
  health,
  dormancy,
  aiInsights,
  onBack,
  handoverState,
  developerNotes,
  revivalIntent,
  onStateChange,
  onNotesChange,
  onRevivalIntentChange,
}: HandoverPageProps) {
  const [readmeContent, setReadmeContent] = useState<string | null>(null);
  const [directoryStructure, setDirectoryStructure] = useState<GithubContentItem[] | null>(null);
  const [loadingReadme, setLoadingReadme] = useState(false);
  const [loadingStructure, setLoadingStructure] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

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

  // Section 1: Project Overview description cleaner
  const getProjectOverview = () => {
    if (readmeContent) {
      const cleaned = readmeContent
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

    return null;
  };

  // Section 2: Start Here detailed onboarding points with concise context
  const getStartHereDetailed = () => {
    const list: { name: string; desc: string }[] = [];

    if (!directoryStructure) {
      return null;
    }

    // 1. README
    const readmeItem = directoryStructure.find(
      (f) => f.name.toLowerCase().startsWith("readme") && f.type === "file"
    );
    if (readmeItem) {
      list.push({
        name: readmeItem.name,
        desc: "Main project documentation containing setup instructions and project overview."
      });
    }

    // 2. frontend / client
    const frontendItem = directoryStructure.find(
      (f) => ["frontend", "client"].includes(f.name.toLowerCase()) && f.type === "dir"
    );
    if (frontendItem) {
      list.push({
        name: `${frontendItem.name}/`,
        desc: "Client-side application codebase directory containing UI and interface views."
      });
    }

    // 3. backend / server / api
    const backendItem = directoryStructure.find(
      (f) => ["backend", "server", "api"].includes(f.name.toLowerCase()) && f.type === "dir"
    );
    if (backendItem) {
      list.push({
        name: `${backendItem.name}/`,
        desc: "Server-side application directory hosting backend business logic and API endpoints."
      });
    }

    // 4. src
    const srcItem = directoryStructure.find(
      (f) => f.name.toLowerCase() === "src" && f.type === "dir"
    );
    if (srcItem) {
      list.push({
        name: `${srcItem.name}/`,
        desc: "Primary source files directory housing core application implementation."
      });
    }

    // 5. app
    const appItem = directoryStructure.find(
      (f) => f.name.toLowerCase() === "app" && f.type === "dir"
    );
    if (appItem && appItem.name.toLowerCase() !== "api") {
      list.push({
        name: `${appItem.name}/`,
        desc: "Framework router, layouts, pages, or views configuration folder."
      });
    }

    // 6. lib
    const libItem = directoryStructure.find(
      (f) => f.name.toLowerCase() === "lib" && f.type === "dir"
    );
    if (libItem) {
      list.push({
        name: `${libItem.name}/`,
        desc: "Internal library directory containing helper utilities and shared modules."
      });
    }

    // 7. tests
    const testItem = directoryStructure.find(
      (f) => ["tests", "test", "spec"].includes(f.name.toLowerCase()) && f.type === "dir"
    );
    if (testItem) {
      list.push({
        name: `${testItem.name}/`,
        desc: "Test suite directory containing test cases and configuration."
      });
    }

    // 8. Key configuration files
    const configChecklist = [
      { filename: "package.json", desc: "Node.js environment settings, run-scripts, and dependencies definitions." },
      { filename: "requirements.txt", desc: "Python application package requirements manifest." },
      { filename: "pyproject.toml", desc: "Python package build system and tool settings configurations." },
      { filename: "go.mod", desc: "Go modules configuration file defining module path and dependencies." },
      { filename: "cargo.toml", desc: "Rust project dependencies and configuration manifest." },
      { filename: "docker-compose.yml", desc: "Docker multi-container configurations." },
      { filename: "dockerfile", desc: "Docker container image specifications." },
      { filename: "tsconfig.json", desc: "TypeScript compiler options settings." },
      { filename: ".env.example", desc: "Required local environment variables template manifest." },
      { filename: ".env", desc: "Local environment variables configuration parameters." }
    ];

    configChecklist.forEach((cfg) => {
      const match = directoryStructure.find(
        (f) => f.name.toLowerCase() === cfg.filename && f.type === "file"
      );
      if (match) {
        list.push({
          name: match.name,
          desc: cfg.desc
        });
      }
    });

    return list;
  };

  // Section 3: Important Areas
  const getImportantAreas = () => {
    const areas: { title: string; description: string }[] = [];

    if (!directoryStructure) {
      return null;
    }

    const fileNames = directoryStructure.map((f) => f.name.toLowerCase());
    const folderNames = directoryStructure.filter((f) => f.type === "dir").map((f) => f.name.toLowerCase());

    // 1. Frontend
    const hasFrontend =
      folderNames.includes("frontend") ||
      folderNames.includes("client") ||
      folderNames.includes("public") ||
      folderNames.includes("components") ||
      folderNames.includes("pages") ||
      fileNames.includes("next.config.js") ||
      fileNames.includes("next.config.ts") ||
      fileNames.includes("vite.config.js") ||
      fileNames.includes("vite.config.ts");

    if (hasFrontend) {
      areas.push({
        title: "Frontend Layer",
        description: "Manages layouts, stylesheet files, interface assets, and client-side page views."
      });
    }

    // 2. Backend
    const hasBackend =
      folderNames.includes("backend") ||
      folderNames.includes("server") ||
      folderNames.includes("api") ||
      fileNames.includes("go.mod") ||
      fileNames.includes("requirements.txt") ||
      fileNames.includes("cargo.toml") ||
      fileNames.includes("gemfile");

    if (hasBackend) {
      areas.push({
        title: "Backend Layer & Services",
        description: "Manages core business rules, server-side APIs, routing mechanisms, and logic functions."
      });
    }

    // 3. Database
    const hasDatabase =
      folderNames.includes("db") ||
      folderNames.includes("database") ||
      folderNames.includes("migrations") ||
      folderNames.includes("prisma") ||
      fileNames.includes("alembic.ini") ||
      fileNames.includes("prisma.schema") ||
      directoryStructure.some(f => f.name.toLowerCase().endsWith(".sql"));

    if (hasDatabase) {
      areas.push({
        title: "Database Schemas & Migrations",
        description: "Defines DB schemas, migration sequences, queries, or model mapper definitions."
      });
    }

    // 4. Testing
    const hasTesting =
      folderNames.includes("tests") ||
      folderNames.includes("test") ||
      folderNames.includes("spec") ||
      fileNames.includes("jest.config.js") ||
      fileNames.includes("jest.config.ts") ||
      fileNames.includes("pytest.ini");

    if (hasTesting) {
      areas.push({
        title: "Testing Architecture",
        description: "Hosts regression tests, unit verification asserts, and environment mock configs."
      });
    }

    // 5. Configuration
    const hasConfig =
      folderNames.includes(".github") ||
      fileNames.includes(".env") ||
      fileNames.includes(".env.example") ||
      fileNames.includes("docker-compose.yml") ||
      fileNames.includes("tsconfig.json") ||
      fileNames.includes(".gitignore");

    if (hasConfig) {
      areas.push({
        title: "Configuration & Deployment",
        description: "Handles environment configuration templates, dependency locks, and integration settings."
      });
    }

    // 6. AI integrations
    const hasAI = directoryStructure.some(
      (f) =>
        f.name.toLowerCase().includes("ai") ||
        f.name.toLowerCase().includes("openai") ||
        f.name.toLowerCase().includes("llm") ||
        f.name.toLowerCase().includes("prompt") ||
        f.name.toLowerCase().includes("agent")
    );

    if (hasAI) {
      areas.push({
        title: "Artificial Intelligence Integrations",
        description: "Connects LLM interface API clients, custom system prompts, or cognitive agents codebase."
      });
    }

    return areas.length > 0 ? areas : [];
  };

  // Section 4: Known Risks
  const getKnownRisks = () => {
    const risks: { type: string; title: string; description: string }[] = [];

    if (health && health.health_score < 70) {
      risks.push({
        type: "health",
        title: "Health score is below the recommended threshold",
        description: `The calculated health rating index is currently at ${health.health_score}/100 (Grade ${health.grade}). The incoming developer should investigate codebase organization or missing configuration guidelines.`
      });
    }

    if (dormancy && dormancy.status.toLowerCase() !== "active") {
      risks.push({
        type: "dormancy",
        title: "Repository has not received recent activity",
        description: `Development pushed to this repository is currently marked as ${dormancy.status} (${dormancy.days_since_last_push} days since the last push). Review the commit history to determine if codebase updates or package versions need adjustment.`
      });
    }

    if (repo.open_issues !== null && repo.open_issues > 30) {
      risks.push({
        type: "backlog",
        title: "Open issue backlog is relatively high",
        description: `There are currently ${repo.open_issues} open issues on GitHub. The incoming developer should review the issues tab to assess unresolved bugs or client feature requests.`
      });
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
            className="rounded-none border border-border-strong bg-surface-secondary p-1.5 text-text-secondary hover:text-text-primary hover:border-text-primary transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
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
            <div className="flex items-center gap-2">
              <span className="text-semantic-healthy select-none font-bold">✓</span> Revival Intent: {REVIVAL_INTENT_OPTIONS.find(o => o.key === revivalIntent)?.title || "Selected"}
            </div>
            {developerNotes.trim() && (
              <div className="flex items-center gap-2">
                <span className="text-semantic-healthy select-none font-bold">✓</span> Developer notes
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="border border-border-muted bg-surface-base p-8 mb-10 shadow-sm">
          {validationError && (
            <div className="mb-6 p-4 border border-semantic-critical/20 bg-semantic-critical/5 text-semantic-critical font-sans text-xs flex items-start gap-2.5 animate-fade-in">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4 shrink-0 mt-0.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <strong className="font-outfit block text-xs mb-0.5 font-bold">Handoff Validation Alert</strong>
                <span>{validationError}</span>
              </div>
            </div>
          )}
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
                  You are building the handover guide. Select a **Revival Intent** below, add your custom context in **From the Previous Developer**, and complete the package when ready.
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
                  onClick={() => {
                    if (!revivalIntent) {
                      setValidationError("Please select a Revival Intent for this project before completing the handover.");
                    } else {
                      setValidationError(null);
                      onStateChange("prepared");
                    }
                  }}
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
              { label: "Revival Intent selected", checked: handoverState === "prepared" || !!revivalIntent },
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
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Project Overview</h3>
              <RenderHonestyBadge state="confirmed" />
            </div>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Repository Context</span>
          </div>
          {loadingReadme ? (
            <div className="py-4 text-center font-mono text-[10px] text-text-muted uppercase animate-pulse">
              Extracting README information...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-1">
                <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Project Description</span>
                <p className="text-xs text-text-secondary font-sans leading-relaxed whitespace-pre-line select-text">
                  {projectOverview || (
                    <span className="text-text-muted italic">Project description and README file contents are not available in this repository.</span>
                  )}
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 pt-4 border-t border-border-muted/50 select-none">
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Repository Name</span>
                  <span className="text-xs font-mono text-text-primary font-bold select-text">{repo.name}</span>
                </div>
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Primary Language</span>
                  <span className="text-xs font-mono text-text-primary font-bold select-text">{repo.language || "Not available"}</span>
                </div>
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Default Branch</span>
                  <span className="text-xs font-mono text-text-primary font-bold select-text">{repo.default_branch || "Not available"}</span>
                </div>
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Size</span>
                  <span className="text-xs font-mono text-text-primary font-bold select-text">
                    {repo.size ? `${(repo.size / 1024).toFixed(2)} MB` : "Not available"}
                  </span>
                </div>
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Created On</span>
                  <span className="text-xs font-mono text-text-primary font-bold select-text">
                    {repo.created_at ? new Date(repo.created_at).toLocaleDateString() : "Not available"}
                  </span>
                </div>
                <div>
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Last Activity</span>
                  <span className="text-xs font-mono text-text-primary font-bold select-text">
                    {repo.pushed_at ? new Date(repo.pushed_at).toLocaleDateString() : "Not available"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 2. START HERE EXPERIENCE */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Start Here</h3>
              <RenderHonestyBadge state={directoryStructure ? "confirmed" : "unavailable"} />
            </div>
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
              {!directoryStructure ? (
                <p className="text-xs text-text-muted font-sans italic">
                  Information unavailable. Could not fetch repository root structure from GitHub.
                </p>
              ) : startHerePoints && startHerePoints.length > 0 ? (
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
              ) : (
                <p className="text-xs text-text-muted font-sans italic">
                  No standard entry-point files or folders were identified in the repository root directory.
                </p>
              )}
            </div>
          )}
        </div>

        {/* 3. IMPORTANT AREAS */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Important Areas</h3>
              <RenderHonestyBadge state={directoryStructure ? "signal" : "unavailable"} />
            </div>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Codebase Domains</span>
          </div>
          {loadingStructure ? (
            <div className="py-4 text-center font-mono text-[10px] text-text-muted uppercase animate-pulse">
              Scanning directories...
            </div>
          ) : !directoryStructure ? (
            <p className="text-xs text-text-muted font-sans italic">
              Information unavailable. Repository structure has not been loaded.
            </p>
          ) : importantAreas && importantAreas.length > 0 ? (
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
          ) : (
            <p className="text-xs text-text-muted font-sans italic">
              No specific codebase layers (such as frontend, backend, or database) could be deterministically inferred from the root folder directory structure.
            </p>
          )}
        </div>

        {/* 4. DEVELOPMENT HISTORY */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Development History</h3>
              <RenderHonestyBadge state="confirmed" />
            </div>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Activity Log</span>
          </div>
          <div className="space-y-4">
            <p className="text-xs text-text-secondary font-sans leading-relaxed">
              This overview shows known activity timelines recorded on GitHub. Note that a complete git commit log analysis is not currently performed in this view.
            </p>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="border border-border-muted p-4 bg-surface-secondary/20">
                <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Known Repository Activity</span>
                <ul className="mt-2 text-xs font-sans text-text-secondary space-y-1">
                  <li>• Created: <strong>{repo.created_at ? new Date(repo.created_at).toLocaleDateString() : "Unavailable"}</strong></li>
                  <li>• Last push: <strong>{repo.pushed_at ? new Date(repo.pushed_at).toLocaleDateString() : "Unavailable"}</strong></li>
                  <li>• Last sync: <strong>{repo.updated_at ? new Date(repo.updated_at).toLocaleDateString() : "Unavailable"}</strong></li>
                </ul>
              </div>
              <div className="border border-border-muted p-4 bg-surface-secondary/20">
                <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Developer-Supplied Info</span>
                <p className="mt-2 text-xs font-sans text-text-secondary leading-normal">
                  Custom timeline context and handoff instructions must be read in the <strong>Developer Notes</strong> section below.
                </p>
              </div>
              <div className="border border-border-muted p-4 bg-surface-secondary/20">
                <div className="flex justify-between items-start">
                  <span className="text-[8px] font-mono text-text-muted uppercase block font-bold">Currently Unavailable</span>
                  <RenderHonestyBadge state="unavailable" />
                </div>
                <p className="mt-2 text-xs font-sans text-text-muted leading-normal italic">
                  Complete branch lists, commit messages history, pull request status, and developer contributions are not available.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 5. KNOWN RISKS */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Known Risks</h3>
              <RenderHonestyBadge state="signal" />
            </div>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">Maintenance Warnings</span>
          </div>
          {knownRisks.length > 0 ? (
            <div className="space-y-3">
              <p className="text-xs text-text-secondary font-sans leading-relaxed select-none">
                The following warning signals were identified from the repository metadata. They represent indicators for the incoming developer to investigate, rather than definitive bugs:
              </p>
              <ul className="space-y-3">
                {knownRisks.map((risk, index) => (
                  <li key={index} className="text-xs border border-semantic-warning/25 bg-semantic-warning/5 text-text-secondary p-3 leading-relaxed font-sans flex items-start gap-2.5">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4 text-semantic-warning shrink-0 mt-0.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <strong className="text-text-primary font-outfit block text-xs mb-0.5">{risk.title}</strong>
                      <span className="select-text">{risk.description}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-xs text-text-muted font-sans italic">
              No standard risk signals (low health, dormancy, or large issue backlogs) were flagged based on repository metadata.
            </p>
          )}
        </div>

        {/* 6. UNFINISHED WORK */}
        <div className="border border-border-muted bg-surface-base p-6 rounded-none shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-muted/65 pb-3 mb-4 select-none">
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Unfinished Work</h3>
              <RenderHonestyBadge state="unavailable" />
            </div>
            <span className="text-[9px] font-mono tracking-wider uppercase text-text-muted">In-Flight Tasks</span>
          </div>
          <div className="space-y-4">
            <p className="text-xs text-text-secondary font-sans leading-relaxed">
              No unfinished work could be automatically inferred from the available GitHub repository metadata.
            </p>
            <div className="border border-dashed border-border-strong bg-surface-secondary/30 p-4">
              <span className="text-[9px] font-mono uppercase text-text-secondary tracking-wider block font-bold mb-1 select-none">Outgoing Developer Note:</span>
              <p className="text-xs font-sans text-text-secondary leading-normal">
                Please document any incomplete tasks, pending feature implementations, or known bugs directly in the <strong>Developer Notes</strong> editor below to preserve them for the next engineer.
              </p>
            </div>
          </div>
        </div>

        {/* 7. REVIVAL INTENT */}
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
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">Revival Intent</h3>
              <RenderHonestyBadge state="confirmed" />
            </div>
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
            Tell the next developer what you want to happen with this project. This selected intent will be presented clearly to any incoming developers.
          </p>

          {handoverState === "not_started" && (
            <div className="border border-border-muted bg-surface-secondary p-4 text-center select-none">
              <p className="text-xs text-text-muted font-mono uppercase">Start Handover to select revival intent</p>
            </div>
          )}

          {handoverState === "in_progress" && (
            <div className="space-y-3">
              <span className="text-[9px] font-mono uppercase text-text-muted tracking-wider block font-bold select-none">Select One Option:</span>
              <div className="grid gap-3 sm:grid-cols-1">
                {REVIVAL_INTENT_OPTIONS.map((option) => {
                  const isSelected = revivalIntent === option.key;
                  return (
                    <button
                      key={option.key}
                      onClick={() => {
                        onRevivalIntentChange(option.key);
                        setValidationError(null);
                      }}
                      className={`w-full text-left p-4 border transition-all duration-150 cursor-pointer focus:outline-none flex flex-col justify-start rounded-none ${
                        isSelected
                          ? "border-brand-accent bg-brand-accent/5 ring-1 ring-brand-accent"
                          : "border-border-strong bg-surface-base hover:border-brand-accent/50 hover:bg-surface-secondary/30"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className={`h-3.5 w-3.5 rounded-full border flex items-center justify-center shrink-0 ${
                          isSelected ? "border-brand-accent" : "border-border-strong bg-surface-secondary"
                        }`}>
                          {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />}
                        </span>
                        <strong className="text-xs font-mono uppercase tracking-wider text-text-primary font-bold">
                          {option.title}
                        </strong>
                      </div>
                      <p className="text-xs font-sans text-text-secondary mt-1.5 pl-6 leading-relaxed">
                        {option.description}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {handoverState === "prepared" && (
            <div className="border border-semantic-healthy/20 bg-semantic-healthy/5 p-5">
              <span className="text-[9px] font-mono uppercase text-semantic-healthy tracking-wider block mb-2 font-bold select-none font-mono">DESIRED OUTCOME</span>
              <strong className="text-sm font-outfit text-text-primary block font-extrabold mb-1">
                {REVIVAL_INTENT_OPTIONS.find(o => o.key === revivalIntent)?.title || "No intent selected"}
              </strong>
              <p className="text-xs font-sans text-text-secondary leading-relaxed">
                {REVIVAL_INTENT_OPTIONS.find(o => o.key === revivalIntent)?.description || "No description available."}
              </p>
            </div>
          )}
        </div>

        {/* 8. DEVELOPER NOTES */}
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
            <div className="flex items-baseline gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">
                {handoverState === "prepared" ? "From the Previous Developer" : "Developer Notes"}
              </h3>
              <RenderHonestyBadge state="confirmed" />
            </div>
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
            Provide additional custom project context that cannot be inferred automatically from repository files. This is the most critical block for capturing developer knowledge.
          </p>

          {handoverState === "not_started" && (
            <div className="border border-border-muted bg-surface-secondary p-4 text-center select-none">
              <p className="text-xs text-text-muted font-mono uppercase">Start Handover to enter notes</p>
            </div>
          )}

          {handoverState === "in_progress" && (
            <div className="space-y-4">
              <div className="bg-surface-secondary border border-border-muted p-4 space-y-2 select-none">
                <span className="text-[9px] font-mono text-text-primary uppercase font-bold block">Guidance Prompts to Consider:</span>
                <div className="grid gap-3 sm:grid-cols-2 text-xs text-text-secondary font-sans">
                  <div>
                    <strong className="text-text-primary font-semibold block mb-0.5">• Current Focus</strong>
                    <span>What were you working on before pausing?</span>
                  </div>
                  <div>
                    <strong className="text-text-primary font-semibold block mb-0.5">• Onboarding Priority</strong>
                    <span>What should the next developer understand first?</span>
                  </div>
                  <div>
                    <strong className="text-text-primary font-semibold block mb-0.5">• Hidden Context</strong>
                    <span>What is not obvious from the codebase or config files?</span>
                  </div>
                  <div>
                    <strong className="text-text-primary font-semibold block mb-0.5">• Warning Areas</strong>
                    <span>What should they be careful about or avoid?</span>
                  </div>
                </div>
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
              <span className="text-[9px] font-mono uppercase text-semantic-healthy tracking-wider block mb-2 font-bold select-none font-mono">OUTGOING DEVELOPER NOTES</span>
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

        {/* 9. NEXT DEVELOPER SECTION */}
        {handoverState === "prepared" && (
          <div className="border border-border-muted bg-surface-secondary/45 p-6 rounded-none shadow-sm">
            <div className="border-b border-border-muted/65 pb-3 mb-4 select-none flex items-center gap-2">
              <h3 className="text-sm font-outfit text-text-primary font-bold">For the Next Developer</h3>
              <RenderHonestyBadge state="confirmed" />
            </div>
            <div className="space-y-3.5">
              {[
                "Read the Project Overview details.",
                "Review the specified Start Here onboarding entries.",
                "Look into the inferred codebase layers inside Important Areas.",
                "Read the previous developer's custom notes and answers to guidance prompts.",
                "Check the identified Known Risks to outline initial test investigations.",
                "Set up and run the codebase local development server.",
                "Implement your first commit changes."
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
              if (confirm("Are you sure you want to reset the handover? This will clear all developer notes and the revival intent.")) {
                onNotesChange("");
                onRevivalIntentChange("");
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
