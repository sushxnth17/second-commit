"use client";

import { useState, useEffect, useCallback } from "react";
import {
  api,
  RevivalTeamResponse,
  RevivalRoadmapResponse,
  RevivalRoadmapPhaseResponse,
  RevivalRoadmapTaskResponse,
  UserSummary,
} from "@/lib/api";

interface RevivalRoadmapProps {
  repositoryId: number;
  team: RevivalTeamResponse | null;
  currentUser?: UserSummary | null;
}

const STATUS_CONFIG: Record<
  string,
  { label: string; badgeClass: string; dotClass: string }
> = {
  todo: {
    label: "To Do",
    badgeClass: "border-border-strong bg-surface-base text-text-secondary",
    dotClass: "bg-text-muted",
  },
  in_progress: {
    label: "In Progress",
    badgeClass: "border-blue-500/40 bg-blue-500/10 text-blue-400",
    dotClass: "bg-blue-500",
  },
  completed: {
    label: "Completed",
    badgeClass: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
    dotClass: "bg-emerald-500",
  },
};

export default function RevivalRoadmap({
  repositoryId,
  team,
  currentUser = null,
}: RevivalRoadmapProps) {
  const [roadmap, setRoadmap] = useState<RevivalRoadmapResponse>({ phases: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Action states
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Phase modal / form states (Owner only)
  const [isAddingPhase, setIsAddingPhase] = useState(false);
  const [newPhaseTitle, setNewPhaseTitle] = useState("");
  const [newPhaseDescription, setNewPhaseDescription] = useState("");

  const [editingPhaseId, setEditingPhaseId] = useState<number | null>(null);
  const [editPhaseTitle, setEditPhaseTitle] = useState("");
  const [editPhaseDescription, setEditPhaseDescription] = useState("");
  const [editPhasePosition, setEditPhasePosition] = useState<number>(0);

  const [confirmDeletePhaseId, setConfirmDeletePhaseId] = useState<number | null>(null);

  // Task modal / form states (Owner only)
  const [addingTaskPhaseId, setAddingTaskPhaseId] = useState<number | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDescription, setNewTaskDescription] = useState("");

  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [editingTaskPhaseId, setEditingTaskPhaseId] = useState<number | null>(null);
  const [editTaskTitle, setEditTaskTitle] = useState("");
  const [editTaskDescription, setEditTaskDescription] = useState("");
  const [editTaskPosition, setEditTaskPosition] = useState<number>(0);
  const [editTaskStatus, setEditTaskStatus] = useState<string>("todo");

  const [confirmDeleteTaskId, setConfirmDeleteTaskId] = useState<number | null>(null);

  // Role detection strictly based on authenticated user ID and authoritative team IDs
  const currentUserId = currentUser?.id;
  const isTeamOwner = Boolean(
    currentUserId != null && team?.owner?.id != null && currentUserId === team.owner.id
  );
  const isTeamMember = Boolean(
    currentUserId != null &&
      team?.members?.some((m) => m.user_id === currentUserId) &&
      !isTeamOwner
  );
  const canInteract = isTeamOwner || isTeamMember;

  const fetchRoadmap = useCallback(async () => {
    if (!repositoryId || !canInteract) {
      setRoadmap({ phases: [] });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRevivalRoadmap(repositoryId);
      setRoadmap(data);
    } catch (err: any) {
      if (
        err.message === "Revival team not found" ||
        err.message === "Repository not found"
      ) {
        setRoadmap({ phases: [] });
      } else {
        setError(err.message || "Failed to load roadmap");
      }
    } finally {
      setLoading(false);
    }
  }, [repositoryId, canInteract]);

  useEffect(() => {
    fetchRoadmap();
  }, [fetchRoadmap]);

  // Phase handlers
  const handleCreatePhase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isTeamOwner || actionLoading) return;
    const title = newPhaseTitle.trim();
    if (!title) {
      setActionError("Phase title cannot be empty.");
      return;
    }
    if (title.length > 200) {
      setActionError("Phase title cannot exceed 200 characters.");
      return;
    }

    setActionLoading(true);
    setActionError(null);
    try {
      await api.createRevivalRoadmapPhase(repositoryId, {
        title,
        description: newPhaseDescription.trim() || undefined,
      });
      setNewPhaseTitle("");
      setNewPhaseDescription("");
      setIsAddingPhase(false);
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to create roadmap phase.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdatePhase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isTeamOwner || actionLoading || !editingPhaseId) return;
    const title = editPhaseTitle.trim();
    if (!title) {
      setActionError("Phase title cannot be empty.");
      return;
    }
    if (title.length > 200) {
      setActionError("Phase title cannot exceed 200 characters.");
      return;
    }

    setActionLoading(true);
    setActionError(null);
    try {
      await api.updateRevivalRoadmapPhase(repositoryId, editingPhaseId, {
        title,
        description: editPhaseDescription.trim() || null,
        position: editPhasePosition,
      });
      setEditingPhaseId(null);
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to update roadmap phase.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeletePhase = async (phaseId: number) => {
    if (!isTeamOwner || actionLoading) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await api.deleteRevivalRoadmapPhase(repositoryId, phaseId);
      setConfirmDeletePhaseId(null);
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to delete roadmap phase.");
    } finally {
      setActionLoading(false);
    }
  };

  // Task handlers
  const handleCreateTask = async (e: React.FormEvent, phaseId: number) => {
    e.preventDefault();
    if (!isTeamOwner || actionLoading) return;
    const title = newTaskTitle.trim();
    if (!title) {
      setActionError("Task title cannot be empty.");
      return;
    }
    if (title.length > 200) {
      setActionError("Task title cannot exceed 200 characters.");
      return;
    }

    setActionLoading(true);
    setActionError(null);
    try {
      await api.createRevivalRoadmapTask(repositoryId, phaseId, {
        title,
        description: newTaskDescription.trim() || undefined,
      });
      setNewTaskTitle("");
      setNewTaskDescription("");
      setAddingTaskPhaseId(null);
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to create task.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isTeamOwner || actionLoading || !editingTaskId || !editingTaskPhaseId) return;
    const title = editTaskTitle.trim();
    if (!title) {
      setActionError("Task title cannot be empty.");
      return;
    }
    if (title.length > 200) {
      setActionError("Task title cannot exceed 200 characters.");
      return;
    }

    setActionLoading(true);
    setActionError(null);
    try {
      await api.updateRevivalRoadmapTask(
        repositoryId,
        editingTaskPhaseId,
        editingTaskId,
        {
          title,
          description: editTaskDescription.trim() || null,
          position: editTaskPosition,
          status: editTaskStatus,
        }
      );
      setEditingTaskId(null);
      setEditingTaskPhaseId(null);
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to update task.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusChange = async (
    phaseId: number,
    taskId: number,
    newStatus: string
  ) => {
    if (!canInteract || actionLoading) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await api.updateRevivalRoadmapTask(repositoryId, phaseId, taskId, {
        status: newStatus,
      });
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to update task status.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTask = async (phaseId: number, taskId: number) => {
    if (!isTeamOwner || actionLoading) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await api.deleteRevivalRoadmapTask(repositoryId, phaseId, taskId);
      setConfirmDeleteTaskId(null);
      await fetchRoadmap();
    } catch (err: any) {
      setActionError(err.message || "Failed to delete task.");
    } finally {
      setActionLoading(false);
    }
  };

  if (!canInteract) {
    return null;
  }

  const phases = roadmap.phases || [];
  const totalTasks = phases.reduce((acc, p) => acc + (p.tasks?.length || 0), 0);
  const completedTasks = phases.reduce(
    (acc, p) =>
      acc + (p.tasks?.filter((t) => t.status === "completed").length || 0),
    0
  );
  const progressPercent =
    totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <div className="border-t border-border-muted pt-6 mt-6">
      {/* Header Section */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 select-none">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-[10px] font-mono uppercase tracking-widest text-brand-accent font-bold">
              REVIVAL ROADMAP
            </span>
            {phases.length > 0 && (
              <span className="px-2 py-0.5 text-[9px] font-mono font-bold border border-border-muted bg-surface-secondary/40 text-text-secondary">
                {phases.length} {phases.length === 1 ? "PHASE" : "PHASES"} &middot; {completedTasks}/{totalTasks} TASKS ({progressPercent}%)
              </span>
            )}
          </div>
          <p className="text-xs text-text-secondary font-sans mt-0.5">
            Structured milestone phases and actionable tasks for reviving this project
          </p>
        </div>

        {isTeamOwner && !isAddingPhase && (
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => {
              setActionError(null);
              setIsAddingPhase(true);
            }}
            aria-label="Add new roadmap phase"
            className="px-3 py-1.5 text-[9px] font-mono uppercase tracking-wider font-bold border border-brand-accent/40 bg-brand-accent/10 text-brand-accent hover:bg-brand-accent/20 transition-all cursor-pointer disabled:opacity-50"
          >
            + Add Phase
          </button>
        )}
      </div>

      {/* Action Error Banner */}
      {actionError && (
        <div className="border border-semantic-critical/30 bg-semantic-critical/10 p-3 mb-4 text-xs font-mono text-semantic-critical flex items-center justify-between">
          <span>{actionError}</span>
          <button
            type="button"
            onClick={() => setActionError(null)}
            className="text-xs font-bold hover:underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Create Phase Form (Owner only) */}
      {isTeamOwner && isAddingPhase && (
        <form
          onSubmit={handleCreatePhase}
          className="border border-border-strong p-4 bg-surface-secondary/25 mb-5 space-y-3 animate-fade-in"
        >
          <div className="flex items-center justify-between border-b border-border-muted pb-2 select-none">
            <span className="text-[10px] font-mono uppercase tracking-wider text-text-primary font-bold">
              New Roadmap Phase
            </span>
            <button
              type="button"
              onClick={() => {
                setIsAddingPhase(false);
                setActionError(null);
              }}
              disabled={actionLoading}
              className="text-[10px] font-mono uppercase text-text-muted hover:text-text-primary cursor-pointer"
            >
              Cancel
            </button>
          </div>

          <div>
            <label
              htmlFor="new-phase-title"
              className="text-[9px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
            >
              Phase Title *
            </label>
            <input
              id="new-phase-title"
              type="text"
              maxLength={200}
              required
              disabled={actionLoading}
              value={newPhaseTitle}
              onChange={(e) => setNewPhaseTitle(e.target.value)}
              placeholder="e.g. Phase 1: Stabilization & Deprecations"
              className="w-full bg-surface-base border border-border-strong px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-accent transition-colors font-sans"
            />
          </div>

          <div>
            <label
              htmlFor="new-phase-desc"
              className="text-[9px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
            >
              Description (Optional)
            </label>
            <textarea
              id="new-phase-desc"
              rows={2}
              disabled={actionLoading}
              value={newPhaseDescription}
              onChange={(e) => setNewPhaseDescription(e.target.value)}
              placeholder="Brief summary of what this phase accomplishes..."
              className="w-full bg-surface-base border border-border-strong px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-accent transition-colors font-sans resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 select-none">
            <button
              type="button"
              disabled={actionLoading}
              onClick={() => setIsAddingPhase(false)}
              className="px-3 py-1 text-[9px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary cursor-pointer transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="px-3 py-1 text-[9px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/15 text-brand-accent hover:bg-brand-accent/25 transition-all cursor-pointer disabled:opacity-50"
            >
              {actionLoading ? "Creating..." : "Create Phase"}
            </button>
          </div>
        </form>
      )}

      {/* Loading State */}
      {loading && (
        <div className="border border-border-muted p-8 text-center bg-surface-secondary/10 my-4 select-none">
          <div className="inline-block h-5 w-5 border-2 border-brand-accent border-t-transparent rounded-full animate-spin mb-2" />
          <p className="text-xs font-mono text-text-muted">Loading roadmap...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && phases.length === 0 && (
        <div className="border border-border-muted p-8 text-center bg-surface-secondary/10 my-4 select-none">
          <p className="text-xs font-mono text-text-muted mb-2">No roadmap phases defined yet.</p>
          {isTeamOwner ? (
            <p className="text-[11px] text-text-secondary">
              Create the first phase to begin mapping out the continuation plan for this project.
            </p>
          ) : (
            <p className="text-[11px] text-text-secondary">
              The team owner has not published any roadmap phases yet.
            </p>
          )}
        </div>
      )}

      {/* Phases List */}
      {!loading && phases.length > 0 && (
        <div className="space-y-6 my-4">
          {phases.map((phase) => {
            const isEditingThisPhase = editingPhaseId === phase.id;
            const isConfirmingDeletePhase = confirmDeletePhaseId === phase.id;
            const isAddingTaskToThis = addingTaskPhaseId === phase.id;
            const phaseTasks = phase.tasks || [];
            const phaseCompleted = phaseTasks.filter((t) => t.status === "completed").length;

            return (
              <div
                key={phase.id}
                className="border border-border-muted bg-surface-base/60 shadow-sm transition-all"
              >
                {/* Phase Header */}
                <div className="p-4 border-b border-border-muted/80 bg-surface-secondary/20">
                  {isEditingThisPhase ? (
                    <form onSubmit={handleUpdatePhase} className="space-y-3">
                      <div className="flex items-center justify-between border-b border-border-muted pb-1.5 select-none">
                        <span className="text-[9px] font-mono uppercase tracking-wider text-text-primary font-bold">
                          Edit Phase #{phase.id}
                        </span>
                        <button
                          type="button"
                          onClick={() => setEditingPhaseId(null)}
                          className="text-[9px] font-mono uppercase text-text-muted hover:text-text-primary cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <div className="md:col-span-3">
                          <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                            Title *
                          </label>
                          <input
                            type="text"
                            maxLength={200}
                            required
                            value={editPhaseTitle}
                            onChange={(e) => setEditPhaseTitle(e.target.value)}
                            className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans"
                          />
                        </div>
                        <div>
                          <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                            Position
                          </label>
                          <input
                            type="number"
                            value={editPhasePosition}
                            onChange={(e) => setEditPhasePosition(Number(e.target.value))}
                            className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-mono"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                          Description
                        </label>
                        <textarea
                          rows={2}
                          value={editPhaseDescription}
                          onChange={(e) => setEditPhaseDescription(e.target.value)}
                          className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans resize-none"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-2 pt-1">
                        <button
                          type="button"
                          disabled={actionLoading}
                          onClick={() => setEditingPhaseId(null)}
                          className="px-2.5 py-1 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={actionLoading}
                          className="px-2.5 py-1 text-[8px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/15 text-brand-accent hover:bg-brand-accent/25"
                        >
                          Save Changes
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-1.5 py-0.5 text-[8px] font-mono font-bold border border-border-muted bg-surface-base text-text-muted">
                            POS {phase.position}
                          </span>
                          <h4 className="text-sm font-outfit font-bold text-text-primary tracking-wide">
                            {phase.title}
                          </h4>
                          <span className="text-[9px] font-mono text-text-muted">
                            ({phaseCompleted}/{phaseTasks.length} done)
                          </span>
                        </div>
                        {phase.description && (
                          <p className="text-xs text-text-secondary font-sans leading-relaxed max-w-2xl">
                            {phase.description}
                          </p>
                        )}
                      </div>

                      {/* Phase Action Controls (Owner Only) */}
                      {isTeamOwner && (
                        <div className="flex items-center gap-2 select-none">
                          {isConfirmingDeletePhase ? (
                            <div className="flex items-center gap-1.5">
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={() => handleDeletePhase(phase.id)}
                                className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-critical/40 bg-semantic-critical/10 text-semantic-critical hover:bg-semantic-critical/20 cursor-pointer"
                              >
                                Confirm Delete
                              </button>
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={() => setConfirmDeletePhaseId(null)}
                                className="px-2 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <>
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={() => {
                                  setActionError(null);
                                  setEditingPhaseId(phase.id);
                                  setEditPhaseTitle(phase.title);
                                  setEditPhaseDescription(phase.description || "");
                                  setEditPhasePosition(phase.position);
                                }}
                                className="px-2 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary cursor-pointer"
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={() => {
                                  setActionError(null);
                                  setConfirmDeletePhaseId(phase.id);
                                }}
                                className="px-2 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-semantic-critical cursor-pointer"
                              >
                                Delete
                              </button>
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={() => {
                                  setActionError(null);
                                  setAddingTaskPhaseId(phase.id);
                                }}
                                className="px-2.5 py-0.5 text-[8px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/10 text-brand-accent hover:bg-brand-accent/20 cursor-pointer"
                              >
                                + Task
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Create Task Inline Form inside Phase */}
                {isTeamOwner && isAddingTaskToThis && (
                  <form
                    onSubmit={(e) => handleCreateTask(e, phase.id)}
                    className="border-b border-border-muted p-4 bg-surface-secondary/30 space-y-3 animate-fade-in"
                  >
                    <div className="flex items-center justify-between border-b border-border-muted pb-1 select-none">
                      <span className="text-[9px] font-mono uppercase tracking-wider text-text-primary font-bold">
                        New Task for &ldquo;{phase.title}&rdquo;
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setAddingTaskPhaseId(null);
                          setActionError(null);
                        }}
                        className="text-[9px] font-mono uppercase text-text-muted hover:text-text-primary cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>

                    <div>
                      <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                        Task Title *
                      </label>
                      <input
                        type="text"
                        maxLength={200}
                        required
                        value={newTaskTitle}
                        onChange={(e) => setNewTaskTitle(e.target.value)}
                        placeholder="e.g. Audit package vulnerabilities and update lockfile"
                        className="w-full bg-surface-base border border-border-strong px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans"
                      />
                    </div>

                    <div>
                      <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                        Description (Optional)
                      </label>
                      <textarea
                        rows={2}
                        value={newTaskDescription}
                        onChange={(e) => setNewTaskDescription(e.target.value)}
                        placeholder="Actionable instructions, acceptance criteria, or context..."
                        className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans resize-none"
                      />
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-1 select-none">
                      <button
                        type="button"
                        onClick={() => setAddingTaskPhaseId(null)}
                        className="px-2.5 py-1 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={actionLoading}
                        className="px-2.5 py-1 text-[8px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/15 text-brand-accent hover:bg-brand-accent/25"
                      >
                        Add Task
                      </button>
                    </div>
                  </form>
                )}

                {/* Tasks List within Phase */}
                <div className="divide-y divide-border-muted/60">
                  {phaseTasks.length === 0 ? (
                    <div className="p-4 text-center text-xs font-mono text-text-muted select-none">
                      No tasks in this phase yet.
                    </div>
                  ) : (
                    phaseTasks.map((task) => {
                      const isEditingThisTask = editingTaskId === task.id;
                      const isConfirmingDeleteTask = confirmDeleteTaskId === task.id;
                      const statusInfo = STATUS_CONFIG[task.status] || STATUS_CONFIG.todo;

                      if (isEditingThisTask && isTeamOwner) {
                        return (
                          <form
                            key={task.id}
                            onSubmit={handleUpdateTask}
                            className="p-4 bg-surface-secondary/25 space-y-3"
                          >
                            <div className="flex items-center justify-between border-b border-border-muted pb-1 select-none">
                              <span className="text-[9px] font-mono uppercase tracking-wider text-text-primary font-bold">
                                Edit Task #{task.id}
                              </span>
                              <button
                                type="button"
                                onClick={() => {
                                  setEditingTaskId(null);
                                  setEditingTaskPhaseId(null);
                                }}
                                className="text-[9px] font-mono uppercase text-text-muted hover:text-text-primary cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                              <div className="md:col-span-2">
                                <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                                  Title *
                                </label>
                                <input
                                  type="text"
                                  maxLength={200}
                                  required
                                  value={editTaskTitle}
                                  onChange={(e) => setEditTaskTitle(e.target.value)}
                                  className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans"
                                />
                              </div>
                              <div>
                                <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                                  Position
                                </label>
                                <input
                                  type="number"
                                  value={editTaskPosition}
                                  onChange={(e) => setEditTaskPosition(Number(e.target.value))}
                                  className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-mono"
                                />
                              </div>
                              <div>
                                <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                                  Status
                                </label>
                                <select
                                  value={editTaskStatus}
                                  onChange={(e) => setEditTaskStatus(e.target.value)}
                                  className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans cursor-pointer"
                                >
                                  <option value="todo">To Do</option>
                                  <option value="in_progress">In Progress</option>
                                  <option value="completed">Completed</option>
                                </select>
                              </div>
                            </div>

                            <div>
                              <label className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1">
                                Description
                              </label>
                              <textarea
                                rows={2}
                                value={editTaskDescription}
                                onChange={(e) => setEditTaskDescription(e.target.value)}
                                className="w-full bg-surface-base border border-border-strong px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:border-brand-accent font-sans resize-none"
                              />
                            </div>

                            <div className="flex items-center justify-end gap-2 pt-1 select-none">
                              <button
                                type="button"
                                onClick={() => {
                                  setEditingTaskId(null);
                                  setEditingTaskPhaseId(null);
                                }}
                                className="px-2.5 py-1 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary"
                              >
                                Cancel
                              </button>
                              <button
                                type="submit"
                                disabled={actionLoading}
                                className="px-2.5 py-1 text-[8px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/15 text-brand-accent hover:bg-brand-accent/25"
                              >
                                Save Task
                              </button>
                            </div>
                          </form>
                        );
                      }

                      return (
                        <div
                          key={task.id}
                          className="p-3.5 flex flex-wrap items-center justify-between gap-3 hover:bg-surface-secondary/15 transition-colors"
                        >
                          <div className="flex-1 min-w-[200px]">
                            <div className="flex items-center gap-2">
                              <span className="text-[8px] font-mono text-text-muted select-none">
                                #{task.position}
                              </span>
                              <span
                                className={`text-xs font-semibold ${
                                  task.status === "completed"
                                    ? "line-through text-text-muted"
                                    : "text-text-primary"
                                }`}
                              >
                                {task.title}
                              </span>
                            </div>
                            {task.description && (
                              <p className="text-[11px] text-text-secondary mt-0.5 ml-4 leading-relaxed">
                                {task.description}
                              </p>
                            )}
                          </div>

                          {/* Status and Action Controls */}
                          <div className="flex items-center gap-2 select-none">
                            {/* Status Selector (Owner & Active Members can update) */}
                            {canInteract ? (
                              <select
                                value={task.status}
                                disabled={actionLoading}
                                onChange={(e) =>
                                  handleStatusChange(phase.id, task.id, e.target.value)
                                }
                                aria-label={`Update status for ${task.title}`}
                                className={`text-[9px] font-mono uppercase font-bold px-2 py-0.5 border cursor-pointer focus:outline-none transition-all ${statusInfo.badgeClass}`}
                              >
                                <option value="todo">To Do</option>
                                <option value="in_progress">In Progress</option>
                                <option value="completed">Completed</option>
                              </select>
                            ) : (
                              <span
                                className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold border ${statusInfo.badgeClass}`}
                              >
                                <span className={`h-1.5 w-1.5 rounded-full ${statusInfo.dotClass}`} />
                                {statusInfo.label}
                              </span>
                            )}

                            {/* Owner Mutation Controls */}
                            {isTeamOwner && (
                              <>
                                {isConfirmingDeleteTask ? (
                                  <div className="flex items-center gap-1">
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() => handleDeleteTask(phase.id, task.id)}
                                      className="px-1.5 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-critical/40 bg-semantic-critical/10 text-semantic-critical hover:bg-semantic-critical/20 cursor-pointer"
                                    >
                                      Confirm
                                    </button>
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() => setConfirmDeleteTaskId(null)}
                                      className="px-1.5 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary cursor-pointer"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() => {
                                        setActionError(null);
                                        setEditingTaskId(task.id);
                                        setEditingTaskPhaseId(phase.id);
                                        setEditTaskTitle(task.title);
                                        setEditTaskDescription(task.description || "");
                                        setEditTaskPosition(task.position);
                                        setEditTaskStatus(task.status);
                                      }}
                                      className="px-1.5 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary cursor-pointer"
                                    >
                                      Edit
                                    </button>
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() => {
                                        setActionError(null);
                                        setConfirmDeleteTaskId(task.id);
                                      }}
                                      className="px-1.5 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-semantic-critical cursor-pointer"
                                    >
                                      Delete
                                    </button>
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
