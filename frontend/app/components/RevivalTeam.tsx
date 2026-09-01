"use client";

import { RevivalTeamResponse } from "@/lib/api";

interface RevivalTeamProps {
  team: RevivalTeamResponse | null;
  loading: boolean;
  error: string | null;
  isOwner: boolean;
  onRetry?: () => void;
}

export default function RevivalTeam({
  team,
  loading,
  error,
  isOwner,
  onRetry,
}: RevivalTeamProps) {
  const totalCount = team ? 1 + (team.members?.length || 0) : 0;
  const owner = team?.owner;
  const ownerName = owner ? owner.name || owner.username : "Owner";
  const ownerUsername = owner?.username || "";
  const ownerAvatar =
    owner?.avatar_url ||
    `https://api.dicebear.com/7.x/initials/svg?seed=${ownerName}`;

  return (
    <div className="border border-border-muted bg-surface-base p-8 mb-10 shadow-sm mt-10">
      {/* Header */}
      <div className="border-b border-border-muted pb-4 mb-6 select-none flex justify-between items-baseline">
        <div>
          <span className="text-[10px] font-mono tracking-widest uppercase text-brand-accent font-bold block mb-1">
            REVIVAL TEAM
          </span>
          <p className="text-xs text-text-secondary font-sans leading-relaxed">
            Developers collaborating on reviving this project
          </p>
        </div>
        {!loading && !error && team && (
          <span className="rounded-none border border-brand-accent/30 bg-brand-accent/10 text-brand-accent px-2 py-0.5 text-[9px] font-mono uppercase font-bold">
            {totalCount} {totalCount === 1 ? "MEMBER" : "MEMBERS"}
          </span>
        )}
      </div>

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
                    {isOwner && (
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
                          <strong className="text-xs font-outfit text-text-primary block font-bold">
                            {name}
                          </strong>
                          {username && (
                            <span className="text-[10px] font-mono text-text-muted block">
                              @{username.toLowerCase()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right select-none">
                        <span className="px-2 py-0.5 text-[8px] font-mono uppercase font-bold border border-semantic-healthy/20 bg-semantic-healthy/5 text-semantic-healthy">
                          MEMBER
                        </span>
                        <span className="block text-[9px] font-mono text-text-muted mt-1">
                          Joined {joinedDate}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
