"use client";

import { useState, useEffect, useCallback } from "react";
import {
  api,
  RevivalTeamResponse,
  RevivalWorkItemResponse,
  UserSummary,
} from "@/lib/api";

interface RevivalTeamProps {
  team: RevivalTeamResponse | null;
  loading: boolean;
  error: string | null;
  isOwner?: boolean;
  currentUser?: UserSummary | null;
  repositoryId?: number;
  onRetry?: () => void;
  onTeamUpdate?: () => void | Promise<void>;
}

export default function RevivalTeam({
  team,
  loading,
  error,
  isOwner = false,
  currentUser = null,
  repositoryId,
  onRetry,
  onTeamUpdate,
}: RevivalTeamProps) {
  const [confirmRemoveId, setConfirmRemoveId] = useState<number | null>(null);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Work items state
  const [workItems, setWorkItems] = useState<RevivalWorkItemResponse[]>([]);
  const [workItemsLoading, setWorkItemsLoading] = useState(false);

  // Create work item state (Owner only)
  const [isAddingItem, setIsAddingItem] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newAssigneeId, setNewAssigneeId] = useState<string>("");

  // Edit work item state (Owner only)
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editAssigneeId, setEditAssigneeId] = useState<string>("");
  const [editStatus, setEditStatus] = useState<string>("todo");

  // Delete confirmation state (Owner only)
  const [confirmDeleteItemId, setConfirmDeleteItemId] = useState<number | null>(null);

  const totalCount = team ? 1 + (team.members?.length || 0) : 0;
  const owner = team?.owner;
  const ownerName = owner ? owner.name || owner.username : "Owner";
  const ownerUsername = owner?.username || "";
  const ownerAvatar =
    owner?.avatar_url ||
    `https://api.dicebear.com/7.x/initials/svg?seed=${ownerName}`;

  const currentUserId = currentUser?.id;
  const isTeamOwner = Boolean(
    currentUserId && team?.owner?.id && currentUserId === team.owner.id
  );
  const isTeamMember = Boolean(
    currentUserId &&
      team?.members?.some((m) => m.user_id === currentUserId) &&
      !isTeamOwner
  );

  const targetRepoId = repositoryId || team?.repository_id;

  const eligibleAssignees = [
    ...(team?.owner
      ? [
          {
            id: team.owner.id,
            name: `${team.owner.name || team.owner.username} (Owner)`,
          },
        ]
      : []),
    ...(team?.members || []).map((m) => {
      const u = m.user;
      const memberName =
        m.name || u?.name || m.username || u?.username || `Member #${m.user_id}`;
      return {
        id: m.user_id,
        name: memberName,
      };
    }),
  ];

  const fetchWorkItems = useCallback(async () => {
    if (!targetRepoId || (!isTeamOwner && !isTeamMember)) {
      setWorkItems([]);
      return;
    }
    setWorkItemsLoading(true);
    try {
      const items = await api.getRevivalWorkItems(targetRepoId);
      setWorkItems(items);
    } catch (err: any) {
      if (
        err.message === "Revival team not found" ||
        err.message === "Repository not found"
      ) {
        setWorkItems([]);
        if (onTeamUpdate) {
          try {
            await onTeamUpdate();
          } catch {}
        }
      }
    } finally {
      setWorkItemsLoading(false);
    }
  }, [targetRepoId, isTeamOwner, isTeamMember, onTeamUpdate]);

  useEffect(() => {
    fetchWorkItems();
  }, [fetchWorkItems]);

  const handleCreateWorkItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetRepoId || actionLoading || !isTeamOwner) return;

    const trimmedTitle = newTitle.trim();
    if (!trimmedTitle) {
      setActionError("Title cannot be empty.");
      return;
    }
    if (trimmedTitle.length > 200) {
      setActionError("Title cannot exceed 200 characters.");
      return;
    }

    setActionLoading(true);
    setActiveActionId("create-work-item");
    setActionError(null);

    try {
      await api.createRevivalWorkItem(targetRepoId, {
        title: trimmedTitle,
        description: newDescription.trim() || undefined,
        assignee_id: newAssigneeId ? Number(newAssigneeId) : undefined,
      });
      setNewTitle("");
      setNewDescription("");
      setNewAssigneeId("");
      setIsAddingItem(false);
      await fetchWorkItems();
    } catch (err: any) {
      const isStale =
        err.message === "Revival team not found" ||
        err.message === "Repository not found";
      const msg =
        err.message === "UNAUTHORIZED"
          ? "Authentication required. Please log in again."
          : isStale
          ? "The revival team is no longer available."
          : err.message || "Failed to create work item.";
      setActionError(msg);
      if (isStale && onTeamUpdate) {
        try {
          await onTeamUpdate();
        } catch {}
      }
    } finally {
      setActionLoading(false);
      setActiveActionId(null);
    }
  };

  const handleStartEdit = (item: RevivalWorkItemResponse) => {
    setActionError(null);
    setConfirmDeleteItemId(null);
    setEditingItemId(item.id);
    setEditTitle(item.title);
    setEditDescription(item.description || "");
    setEditAssigneeId(item.assignee ? String(item.assignee.id) : "");
    setEditStatus(item.status);
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setActionError(null);
  };

  const handleSaveEdit = async (workItemId: number) => {
    if (!targetRepoId || actionLoading || !isTeamOwner) return;

    const trimmedTitle = editTitle.trim();
    if (!trimmedTitle) {
      setActionError("Title cannot be empty.");
      return;
    }
    if (trimmedTitle.length > 200) {
      setActionError("Title cannot exceed 200 characters.");
      return;
    }

    setActionLoading(true);
    setActiveActionId(`edit-${workItemId}`);
    setActionError(null);

    try {
      await api.updateRevivalWorkItem(targetRepoId, workItemId, {
        title: trimmedTitle,
        description: editDescription.trim() ? editDescription.trim() : null,
        assignee_id: editAssigneeId ? Number(editAssigneeId) : null,
        status: editStatus,
      });
      setEditingItemId(null);
      await fetchWorkItems();
    } catch (err: any) {
      const isStale =
        err.message === "Work item not found" ||
        err.message === "Revival team not found" ||
        err.message === "Repository not found";
      const msg =
        err.message === "UNAUTHORIZED"
          ? "Authentication required. Please log in again."
          : isStale
          ? "This work item is no longer available."
          : err.message || "Failed to update work item.";
      setActionError(msg);
      if (isStale) {
        setEditingItemId(null);
        await fetchWorkItems();
        if (onTeamUpdate) {
          try {
            await onTeamUpdate();
          } catch {}
        }
      }
    } finally {
      setActionLoading(false);
      setActiveActionId(null);
    }
  };

  const handleMemberStatusChange = async (
    workItemId: number,
    newStatus: string
  ) => {
    if (!targetRepoId || actionLoading || !isTeamMember) return;

    setActionLoading(true);
    setActiveActionId(`status-${workItemId}`);
    setActionError(null);

    try {
      await api.updateRevivalWorkItem(targetRepoId, workItemId, {
        status: newStatus,
      });
      await fetchWorkItems();
    } catch (err: any) {
      const isStale =
        err.message === "Work item not found" ||
        err.message === "Revival team not found" ||
        err.message === "Repository not found";
      const msg =
        err.message === "UNAUTHORIZED"
          ? "Authentication required. Please log in again."
          : isStale
          ? "This work item is no longer available."
          : err.message || "Failed to update status.";
      setActionError(msg);
      if (isStale) {
        await fetchWorkItems();
        if (onTeamUpdate) {
          try {
            await onTeamUpdate();
          } catch {}
        }
      }
    } finally {
      setActionLoading(false);
      setActiveActionId(null);
    }
  };

  const handleDeleteWorkItem = async (workItemId: number) => {
    if (!targetRepoId || actionLoading || !isTeamOwner) return;

    setActionLoading(true);
    setActiveActionId(`delete-${workItemId}`);
    setActionError(null);

    try {
      await api.deleteRevivalWorkItem(targetRepoId, workItemId);
      setConfirmDeleteItemId(null);
      await fetchWorkItems();
    } catch (err: any) {
      const isStale =
        err.message === "Work item not found" ||
        err.message === "Revival team not found" ||
        err.message === "Repository not found";
      const msg =
        err.message === "UNAUTHORIZED"
          ? "Authentication required. Please log in again."
          : isStale
          ? "This work item is no longer available."
          : err.message || "Failed to delete work item.";
      setActionError(msg);
      setConfirmDeleteItemId(null);
      await fetchWorkItems();
      if (isStale && onTeamUpdate) {
        try {
          await onTeamUpdate();
        } catch {}
      }
    } finally {
      setActionLoading(false);
      setActiveActionId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-healthy/30 bg-semantic-healthy/10 text-semantic-healthy">
            Completed
          </span>
        );
      case "in_progress":
        return (
          <span className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-brand-accent/30 bg-brand-accent/10 text-brand-accent">
            In Progress
          </span>
        );
      case "todo":
      default:
        return (
          <span className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-border-strong bg-surface-secondary/40 text-text-secondary">
            To Do
          </span>
        );
    }
  };


  const handleRemoveMember = async (userId: number) => {
    const targetRepoId = repositoryId || team?.repository_id;
    if (!targetRepoId || actionLoading) return;

    setActionLoading(true);
    setActiveActionId(`remove-${userId}`);
    setActionError(null);

    try {
      await api.removeRevivalTeamMember(targetRepoId, userId);
      setConfirmRemoveId(null);
      if (onTeamUpdate) {
        await onTeamUpdate();
      }
    } catch (err: any) {
      const isStale =
        err.message === "Team member not found" ||
        err.message === "Repository not found";
      const msg =
        err.message === "UNAUTHORIZED"
          ? "Authentication required. Please log in again."
          : isStale
          ? "This member is no longer in the revival team."
          : err.message || "Failed to remove member. Please try again.";
      setActionError(msg);
      if (isStale) {
        setConfirmRemoveId(null);
        if (onTeamUpdate) {
          try {
            await onTeamUpdate();
          } catch {}
        }
      }
    } finally {
      setActionLoading(false);
      setActiveActionId(null);
    }
  };

  const handleLeaveTeam = async () => {
    const targetRepoId = repositoryId || team?.repository_id;
    if (!targetRepoId || actionLoading) return;

    setActionLoading(true);
    setActiveActionId("leave");
    setActionError(null);

    try {
      await api.leaveRevivalTeam(targetRepoId);
      setConfirmLeave(false);
      if (onTeamUpdate) {
        await onTeamUpdate();
      }
    } catch (err: any) {
      const isStale =
        err.message === "Team member not found" ||
        err.message === "Repository not found";
      const msg =
        err.message === "UNAUTHORIZED"
          ? "Authentication required. Please log in again."
          : isStale
          ? "You are no longer a member of this revival team."
          : err.message || "Failed to leave team. Please try again.";
      setActionError(msg);
      if (isStale) {
        setConfirmLeave(false);
        if (onTeamUpdate) {
          try {
            await onTeamUpdate();
          } catch {}
        }
      }
    } finally {
      setActionLoading(false);
      setActiveActionId(null);
    }
  };

  return (
    <div className="border border-border-muted bg-surface-base p-8 mb-10 shadow-sm mt-10">
      {/* Header */}
      <div className="border-b border-border-muted pb-4 mb-6 select-none flex flex-wrap justify-between items-baseline gap-4">
        <div>
          <span className="text-[10px] font-mono tracking-widest uppercase text-brand-accent font-bold block mb-1">
            REVIVAL TEAM
          </span>
          <p className="text-xs text-text-secondary font-sans leading-relaxed">
            Developers collaborating on reviving this project
          </p>
        </div>

        <div className="flex items-center gap-3">
          {!loading && !error && team && (
            <span className="rounded-none border border-brand-accent/30 bg-brand-accent/10 text-brand-accent px-2 py-0.5 text-[9px] font-mono uppercase font-bold">
              {totalCount} {totalCount === 1 ? "MEMBER" : "MEMBERS"}
            </span>
          )}

          {/* Leave Team Button for Active Non-Owner Members */}
          {!loading && !error && team && isTeamMember && (
            <div>
              {confirmLeave ? (
                <div className="flex items-center gap-2 select-none">
                  <span className="text-[10px] text-semantic-critical font-mono">
                    Leave team?
                  </span>
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={handleLeaveTeam}
                    aria-label="Confirm leaving revival team"
                    className="px-2.5 py-1 text-[9px] font-mono uppercase font-bold border border-semantic-critical/40 bg-semantic-critical/10 text-semantic-critical hover:bg-semantic-critical/20 disabled:opacity-50 cursor-pointer transition-all"
                  >
                    {actionLoading && activeActionId === "leave"
                      ? "Leaving..."
                      : "Confirm Leave"}
                  </button>
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={() => setConfirmLeave(false)}
                    aria-label="Cancel leaving team"
                    className="px-2.5 py-1 text-[9px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary disabled:opacity-50 cursor-pointer transition-all"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => {
                    setActionError(null);
                    setConfirmLeave(true);
                  }}
                  aria-label="Leave revival team"
                  className="px-3 py-1 text-[9px] font-mono uppercase tracking-wider font-bold border border-border-strong bg-surface-base text-text-secondary hover:text-semantic-critical hover:border-semantic-critical/40 hover:bg-semantic-critical/5 transition-all cursor-pointer disabled:opacity-50"
                >
                  Leave Team
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Error Alert */}
      {actionError && (
        <div className="mb-6 p-3.5 border border-semantic-critical/20 bg-semantic-critical/5 flex items-center justify-between text-xs text-semantic-critical font-sans">
          <span>{actionError}</span>
          <button
            type="button"
            onClick={() => setActionError(null)}
            className="text-[10px] font-mono uppercase underline ml-4 hover:text-text-primary cursor-pointer select-none"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-10 gap-3 select-none">
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse" />
            <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.2s]" />
            <div className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse [animation-delay:0.4s]" />
          </div>
          <span className="text-[10px] font-mono uppercase text-text-muted">
            Loading team...
          </span>
        </div>
      ) : error ? (
        /* Error State */
        <div className="border border-semantic-critical/20 bg-semantic-critical/5 p-6 text-center select-none">
          <span className="text-[10px] font-mono uppercase text-semantic-critical font-bold">
            Unable to load revival team
          </span>
          <p className="text-xs text-text-secondary mt-1.5 font-sans leading-relaxed">
            {error}
          </p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 px-3 py-1 text-[9px] font-mono uppercase tracking-wider border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary transition-all cursor-pointer"
            >
              Retry
            </button>
          )}
        </div>
      ) : !team ? (
        /* Empty State */
        <div className="border border-dashed border-border-strong py-10 px-6 text-center select-none bg-surface-secondary/20">
          <h4 className="text-xs font-mono uppercase tracking-widest text-text-muted font-bold">
            NO REVIVAL TEAM FORMED YET
          </h4>
          <p className="text-[11px] text-text-secondary font-sans mt-2 max-w-md mx-auto leading-relaxed">
            Once the first Revival Request is approved, the team will appear here.
          </p>
        </div>
      ) : (
        /* Team Display */
        <div className="space-y-6">
          {/* Owner Card */}
          <div>
            <span className="text-[9px] font-mono uppercase tracking-widest text-text-muted font-bold block mb-3 select-none">
              TEAM OWNER
            </span>
            <div className="border border-border-muted p-4 bg-surface-secondary/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <img
                  src={ownerAvatar}
                  alt={ownerName}
                  className="h-9 w-9 rounded-full border border-border-muted object-cover select-none"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${ownerName}`;
                  }}
                />
                <div>
                  <div className="flex items-center gap-2">
                    <strong className="text-xs font-outfit text-text-primary font-bold">
                      {ownerName}
                    </strong>
                    {isTeamOwner && (
                      <span className="text-[9px] font-mono uppercase text-brand-accent font-bold select-none">
                        (You)
                      </span>
                    )}
                  </div>
                  {ownerUsername && (
                    <span className="text-[10px] font-mono text-text-muted block">
                      @{ownerUsername.toLowerCase()}
                    </span>
                  )}
                </div>
              </div>
              <span className="px-2 py-0.5 text-[9px] font-mono uppercase font-bold border border-brand-accent/30 bg-brand-accent/10 text-brand-accent select-none">
                OWNER
              </span>
            </div>
          </div>

          {/* Members List */}
          <div>
            <span className="text-[9px] font-mono uppercase tracking-widest text-text-muted font-bold block mb-3 select-none">
              REVIVAL MEMBERS {team.members?.length ? `(${team.members.length})` : ""}
            </span>
            {!team.members || team.members.length === 0 ? (
              <p className="text-xs text-text-muted italic py-2 font-sans select-none">
                No developers have joined the revival team yet.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {team.members.map((member) => {
                  const memberUser = member.user;
                  const name =
                    member.name ||
                    memberUser?.name ||
                    member.username ||
                    memberUser?.username ||
                    "Developer";
                  const username =
                    member.username || memberUser?.username || "";
                  const avatar =
                    member.avatar_url ||
                    memberUser?.avatar_url ||
                    `https://api.dicebear.com/7.x/initials/svg?seed=${name}`;
                  const joinedDate = new Date(
                    member.joined_at
                  ).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  });

                  const isMemberSelf = Boolean(
                    currentUserId && member.user_id === currentUserId
                  );
                  const isConfirmingRemove = confirmRemoveId === member.user_id;
                  const isRemovingThis =
                    actionLoading && activeActionId === `remove-${member.user_id}`;

                  return (
                    <div
                      key={member.id}
                      className="border border-border-muted p-3.5 bg-surface-secondary/15 flex items-center justify-between animate-fade-in"
                    >
                      <div className="flex items-center gap-3">
                        <img
                          src={avatar}
                          alt={name}
                          className="h-8 w-8 rounded-full border border-border-muted object-cover select-none"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${name}`;
                          }}
                        />
                        <div>
                          <div className="flex items-center gap-1.5">
                            <strong className="text-xs font-outfit text-text-primary block font-bold">
                              {name}
                            </strong>
                            {isMemberSelf && (
                              <span className="text-[9px] font-mono uppercase text-brand-accent font-bold select-none">
                                (You)
                              </span>
                            )}
                          </div>
                          {username && (
                            <span className="text-[10px] font-mono text-text-muted block">
                              @{username.toLowerCase()}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-right flex flex-col items-end gap-1 select-none">
                        <span className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-healthy/20 bg-semantic-healthy/5 text-semantic-healthy">
                          MEMBER
                        </span>
                        <span className="block text-[9px] font-mono text-text-muted">
                          Joined {joinedDate}
                        </span>

                        {/* Owner Remove Action */}
                        {isTeamOwner && (
                          <div className="mt-1">
                            {isConfirmingRemove ? (
                              <div className="flex items-center gap-1.5">
                                <button
                                  type="button"
                                  disabled={actionLoading}
                                  onClick={() => handleRemoveMember(member.user_id)}
                                  aria-label={`Confirm removing ${name} from revival team`}
                                  className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-critical/40 bg-semantic-critical/10 text-semantic-critical hover:bg-semantic-critical/20 disabled:opacity-50 cursor-pointer transition-all"
                                >
                                  {isRemovingThis ? "Removing..." : "Confirm"}
                                </button>
                                <button
                                  type="button"
                                  disabled={actionLoading}
                                  onClick={() => setConfirmRemoveId(null)}
                                  aria-label="Cancel removal"
                                  className="px-2 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary disabled:opacity-50 cursor-pointer transition-all"
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={() => {
                                  setActionError(null);
                                  setConfirmRemoveId(member.user_id);
                                }}
                                aria-label={`Remove ${name} from revival team`}
                                className="px-2 py-0.5 text-[8px] font-mono uppercase tracking-wider font-bold border border-border-strong bg-surface-base text-text-secondary hover:text-semantic-critical hover:border-semantic-critical/40 hover:bg-semantic-critical/5 transition-all cursor-pointer disabled:opacity-50"
                              >
                                Remove
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Work Items Section */}
          {(isTeamOwner || isTeamMember) && (
            <div className="border-t border-border-muted pt-6 mt-6">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4 select-none">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono uppercase tracking-widest text-text-muted font-bold">
                      REVIVAL WORK ITEMS
                    </span>
                    {workItems.length > 0 && (
                      <span className="px-1.5 py-0.5 text-[8px] font-mono font-bold border border-border-muted bg-surface-secondary/40 text-text-secondary">
                        {workItems.length}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-text-secondary font-sans mt-0.5">
                    Tasks and milestones for project revival
                  </p>
                </div>

                {isTeamOwner && !isAddingItem && (
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={() => {
                      setActionError(null);
                      setIsAddingItem(true);
                    }}
                    aria-label="Add new work item"
                    className="px-2.5 py-1 text-[9px] font-mono uppercase tracking-wider font-bold border border-brand-accent/40 bg-brand-accent/10 text-brand-accent hover:bg-brand-accent/20 transition-all cursor-pointer disabled:opacity-50"
                  >
                    + Add Work Item
                  </button>
                )}
              </div>

              {/* Create Work Item Inline Form (Owner only) */}
              {isTeamOwner && isAddingItem && (
                <form
                  onSubmit={handleCreateWorkItem}
                  className="border border-border-strong p-4 bg-surface-secondary/25 mb-4 space-y-3 animate-fade-in"
                >
                  <div className="flex items-center justify-between border-b border-border-muted pb-2 select-none">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-text-primary font-bold">
                      New Work Item
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setIsAddingItem(false);
                        setActionError(null);
                      }}
                      disabled={actionLoading}
                      aria-label="Cancel adding work item"
                      className="text-[10px] font-mono uppercase text-text-muted hover:text-text-primary cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>

                  <div>
                    <label
                      htmlFor="new-item-title"
                      className="text-[9px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                    >
                      Title *
                    </label>
                    <input
                      id="new-item-title"
                      type="text"
                      maxLength={200}
                      required
                      disabled={actionLoading}
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="e.g. Update deprecated dependencies"
                      className="w-full bg-surface-base border border-border-strong px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-accent transition-colors font-sans"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="new-item-desc"
                      className="text-[9px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                    >
                      Description (Optional)
                    </label>
                    <textarea
                      id="new-item-desc"
                      rows={2}
                      disabled={actionLoading}
                      value={newDescription}
                      onChange={(e) => setNewDescription(e.target.value)}
                      placeholder="Additional context or requirements..."
                      className="w-full bg-surface-base border border-border-strong px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-accent transition-colors font-sans resize-none"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="new-item-assignee"
                      className="text-[9px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                    >
                      Assignee
                    </label>
                    <select
                      id="new-item-assignee"
                      disabled={actionLoading}
                      value={newAssigneeId}
                      onChange={(e) => setNewAssigneeId(e.target.value)}
                      className="w-full bg-surface-base border border-border-strong px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-brand-accent transition-colors font-sans cursor-pointer"
                    >
                      <option value="">Unassigned</option>
                      {eligibleAssignees.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 select-none">
                    <button
                      type="button"
                      disabled={actionLoading}
                      onClick={() => {
                        setIsAddingItem(false);
                        setActionError(null);
                      }}
                      aria-label="Cancel new work item"
                      className="px-3 py-1 text-[9px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary disabled:opacity-50 cursor-pointer transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={actionLoading || !newTitle.trim()}
                      aria-label="Create work item"
                      className="px-3 py-1 text-[9px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/10 text-brand-accent hover:bg-brand-accent/20 disabled:opacity-50 cursor-pointer transition-all"
                    >
                      {actionLoading && activeActionId === "create-work-item"
                        ? "Creating..."
                        : "Create Item"}
                    </button>
                  </div>
                </form>
              )}

              {/* Work Items List / Empty State */}
              {workItemsLoading && workItems.length === 0 ? (
                <div className="flex items-center justify-center py-6 gap-2 text-text-muted font-mono text-[10px] select-none">
                  <span>Loading work items...</span>
                </div>
              ) : workItems.length === 0 ? (
                <div className="border border-dashed border-border-muted p-6 text-center bg-surface-secondary/10 select-none">
                  <p className="text-xs font-mono uppercase text-text-muted tracking-wider">
                    No work items yet
                  </p>
                  <p className="text-[11px] text-text-secondary font-sans mt-1">
                    {isTeamOwner
                      ? "Create the first work item to plan revival tasks."
                      : "The team owner hasn't created any tasks yet."}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {workItems.map((item) => {
                    const isEditingThis = editingItemId === item.id;
                    const isConfirmingDelete = confirmDeleteItemId === item.id;
                    const isMutatingThis =
                      actionLoading &&
                      (activeActionId === `edit-${item.id}` ||
                        activeActionId === `delete-${item.id}` ||
                        activeActionId === `status-${item.id}`);

                    const assigneeName = item.assignee
                      ? item.assignee.name || item.assignee.username
                      : "Unassigned";
                    const assigneeAvatar = item.assignee?.avatar_url;

                    return (
                      <div
                        key={item.id}
                        className="border border-border-muted p-4 bg-surface-secondary/15 transition-all"
                      >
                        {/* Owner Edit Form */}
                        {isEditingThis ? (
                          <div className="space-y-3 animate-fade-in">
                            <div className="flex items-center justify-between border-b border-border-muted pb-1.5 select-none">
                              <span className="text-[9px] font-mono uppercase font-bold text-brand-accent tracking-wider">
                                Edit Work Item #{item.id}
                              </span>
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={handleCancelEdit}
                                aria-label="Cancel editing"
                                className="text-[9px] font-mono uppercase text-text-muted hover:text-text-primary cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>

                            <div>
                              <label
                                htmlFor={`edit-title-${item.id}`}
                                className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                              >
                                Title *
                              </label>
                              <input
                                id={`edit-title-${item.id}`}
                                type="text"
                                maxLength={200}
                                required
                                disabled={actionLoading}
                                value={editTitle}
                                onChange={(e) => setEditTitle(e.target.value)}
                                className="w-full bg-surface-base border border-border-strong px-3 py-1 text-xs text-text-primary font-sans focus:outline-none focus:border-brand-accent"
                              />
                            </div>

                            <div>
                              <label
                                htmlFor={`edit-desc-${item.id}`}
                                className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                              >
                                Description
                              </label>
                              <textarea
                                id={`edit-desc-${item.id}`}
                                rows={2}
                                disabled={actionLoading}
                                value={editDescription}
                                onChange={(e) =>
                                  setEditDescription(e.target.value)
                                }
                                placeholder="No description provided"
                                className="w-full bg-surface-base border border-border-strong px-3 py-1 text-xs text-text-primary font-sans focus:outline-none focus:border-brand-accent resize-none"
                              />
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label
                                  htmlFor={`edit-assignee-${item.id}`}
                                  className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                                >
                                  Assignee
                                </label>
                                <select
                                  id={`edit-assignee-${item.id}`}
                                  disabled={actionLoading}
                                  value={editAssigneeId}
                                  onChange={(e) =>
                                    setEditAssigneeId(e.target.value)
                                  }
                                  className="w-full bg-surface-base border border-border-strong px-2 py-1 text-xs text-text-primary font-sans focus:outline-none focus:border-brand-accent cursor-pointer"
                                >
                                  <option value="">Unassigned</option>
                                  {eligibleAssignees.map((a) => (
                                    <option key={a.id} value={a.id}>
                                      {a.name}
                                    </option>
                                  ))}
                                </select>
                              </div>

                              <div>
                                <label
                                  htmlFor={`edit-status-${item.id}`}
                                  className="text-[8px] font-mono uppercase text-text-muted font-bold block mb-1 select-none"
                                >
                                  Status
                                </label>
                                <select
                                  id={`edit-status-${item.id}`}
                                  disabled={actionLoading}
                                  value={editStatus}
                                  onChange={(e) =>
                                    setEditStatus(e.target.value)
                                  }
                                  className="w-full bg-surface-base border border-border-strong px-2 py-1 text-xs text-text-primary font-sans focus:outline-none focus:border-brand-accent cursor-pointer"
                                >
                                  <option value="todo">To Do</option>
                                  <option value="in_progress">
                                    In Progress
                                  </option>
                                  <option value="completed">Completed</option>
                                </select>
                              </div>
                            </div>

                            <div className="flex items-center justify-end gap-2 pt-2 select-none">
                              <button
                                type="button"
                                disabled={actionLoading}
                                onClick={handleCancelEdit}
                                aria-label="Cancel edit"
                                className="px-2.5 py-1 text-[9px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary disabled:opacity-50 cursor-pointer"
                              >
                                Cancel
                              </button>
                              <button
                                type="button"
                                disabled={actionLoading || !editTitle.trim()}
                                onClick={() => handleSaveEdit(item.id)}
                                aria-label={`Save changes to ${item.title}`}
                                className="px-2.5 py-1 text-[9px] font-mono uppercase font-bold border border-brand-accent/40 bg-brand-accent/10 text-brand-accent hover:bg-brand-accent/20 disabled:opacity-50 cursor-pointer"
                              >
                                {isMutatingThis ? "Saving..." : "Save Changes"}
                              </button>
                            </div>
                          </div>
                        ) : (
                          /* Normal Work Item Card View */
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div className="space-y-1.5 flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <strong className="text-xs font-outfit text-text-primary font-bold break-words">
                                  {item.title}
                                </strong>
                                {/* Status display or member status control */}
                                {isTeamMember ? (
                                  <div className="inline-flex items-center gap-1.5 ml-1">
                                    <select
                                      aria-label={`Update status for ${item.title}`}
                                      disabled={actionLoading}
                                      value={item.status}
                                      onChange={(e) =>
                                        handleMemberStatusChange(
                                          item.id,
                                          e.target.value
                                        )
                                      }
                                      className="text-[9px] font-mono uppercase font-bold px-2 py-0.5 border border-border-strong bg-surface-base text-text-primary focus:outline-none focus:border-brand-accent cursor-pointer disabled:opacity-50"
                                    >
                                      <option value="todo">To Do</option>
                                      <option value="in_progress">
                                        In Progress
                                      </option>
                                      <option value="completed">
                                        Completed
                                      </option>
                                    </select>
                                    {isMutatingThis && (
                                      <span className="text-[8px] font-mono text-brand-accent animate-pulse">
                                        Updating...
                                      </span>
                                    )}
                                  </div>
                                ) : (
                                  getStatusBadge(item.status)
                                )}
                              </div>

                              {item.description && (
                                <p className="text-[11px] text-text-secondary font-sans leading-relaxed whitespace-pre-wrap">
                                  {item.description}
                                </p>
                              )}

                              <div className="flex items-center gap-3 text-[9px] font-mono text-text-muted select-none flex-wrap">
                                {/* Assignee display */}
                                <div className="flex items-center gap-1.5">
                                  <span>Assignee:</span>
                                  {item.assignee ? (
                                    <div className="flex items-center gap-1 text-text-secondary">
                                      {assigneeAvatar && (
                                        <img
                                          src={assigneeAvatar}
                                          alt={assigneeName}
                                          className="h-3.5 w-3.5 rounded-full object-cover border border-border-muted"
                                          onError={(e) => {
                                            (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${assigneeName}`;
                                          }}
                                        />
                                      )}
                                      <span className="font-bold">
                                        {assigneeName}
                                      </span>
                                    </div>
                                  ) : (
                                    <span className="italic text-text-muted">
                                      Unassigned
                                    </span>
                                  )}
                                </div>

                                <span>•</span>
                                <span>
                                  Created{" "}
                                  {new Date(
                                    item.created_at
                                  ).toLocaleDateString(undefined, {
                                    month: "short",
                                    day: "numeric",
                                  })}
                                </span>
                              </div>
                            </div>

                            {/* Owner Controls (Edit & Delete) */}
                            {isTeamOwner && (
                              <div className="flex items-center gap-2 self-end sm:self-center select-none shrink-0">
                                {isConfirmingDelete ? (
                                  <div className="flex items-center gap-1.5">
                                    <span className="text-[9px] text-semantic-critical font-mono">
                                      Delete?
                                    </span>
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() =>
                                        handleDeleteWorkItem(item.id)
                                      }
                                      aria-label={`Confirm deleting ${item.title}`}
                                      className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-critical/40 bg-semantic-critical/10 text-semantic-critical hover:bg-semantic-critical/20 disabled:opacity-50 cursor-pointer transition-all"
                                    >
                                      {isMutatingThis
                                        ? "Deleting..."
                                        : "Confirm"}
                                    </button>
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() =>
                                        setConfirmDeleteItemId(null)
                                      }
                                      aria-label="Cancel deletion"
                                      className="px-2 py-0.5 text-[8px] font-mono uppercase border border-border-strong bg-surface-base text-text-secondary hover:text-text-primary disabled:opacity-50 cursor-pointer transition-all"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <>
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() => handleStartEdit(item)}
                                      aria-label={`Edit ${item.title}`}
                                      className="px-2 py-0.5 text-[8px] font-mono uppercase tracking-wider font-bold border border-border-strong bg-surface-base text-text-secondary hover:text-brand-accent hover:border-brand-accent/40 transition-all cursor-pointer disabled:opacity-50"
                                    >
                                      Edit
                                    </button>
                                    <button
                                      type="button"
                                      disabled={actionLoading}
                                      onClick={() => {
                                        setActionError(null);
                                        setEditingItemId(null);
                                        setConfirmDeleteItemId(item.id);
                                      }}
                                      aria-label={`Delete ${item.title}`}
                                      className="px-2 py-0.5 text-[8px] font-mono uppercase tracking-wider font-bold border border-border-strong bg-surface-base text-text-secondary hover:text-semantic-critical hover:border-semantic-critical/40 hover:bg-semantic-critical/5 transition-all cursor-pointer disabled:opacity-50"
                                    >
                                      Delete
                                    </button>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
