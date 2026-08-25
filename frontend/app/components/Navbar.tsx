"use client";

import { UserSummary } from "@/lib/api";

interface NavbarProps {
  user: UserSummary;
  activeTab: "dashboard" | "analytics";
  setActiveTab: (tab: "dashboard" | "analytics") => void;
  onLogout: () => void;
}

export default function Navbar({
  user,
  activeTab,
  setActiveTab,
  onLogout,
}: NavbarProps) {
  // Use a fallback avatar url if none is provided
  const avatarUrl = user.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${user.username}`;

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border-muted bg-background/85 backdrop-blur-md transition-colors select-none">
      <div className="mx-auto max-w-5xl px-6">
        <div className="flex h-14 items-center justify-between">
          <div className="flex h-full items-center">
            {/* Logo */}
            <div className="flex items-center gap-2 cursor-pointer select-none" onClick={() => setActiveTab("dashboard")}>
              <span className="font-outfit text-base font-extrabold tracking-wider text-text-primary uppercase">
                SecondCommit
              </span>
            </div>

            {/* Navigation Tabs */}
            <div className="flex h-full items-center gap-6 ml-8">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`flex items-center h-full text-[10px] font-mono uppercase tracking-widest transition-all border-b-2 pt-0.5 cursor-pointer outline-none ${
                  activeTab === "dashboard"
                    ? "border-brand-accent text-brand-accent font-bold"
                    : "border-transparent text-text-secondary hover:text-brand-accent"
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab("analytics")}
                className={`flex items-center h-full text-[10px] font-mono uppercase tracking-widest transition-all border-b-2 pt-0.5 cursor-pointer outline-none ${
                  activeTab === "analytics"
                    ? "border-brand-accent text-brand-accent font-bold"
                    : "border-transparent text-text-secondary hover:text-brand-accent"
                }`}
              >
                Analytics
              </button>
            </div>
          </div>

          {/* Right Hand Profile Actions */}
          <div className="flex items-center gap-5">
            {/* User Profile Summary */}
            <div className="flex items-center gap-2">
              <img
                src={avatarUrl}
                alt={user.name || user.username}
                className="h-5 w-5 rounded-full border border-border-strong bg-surface-secondary object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${user.name || user.username}`;
                }}
              />
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-[11px] font-bold text-text-primary leading-none">
                  {user.name || user.username}
                </span>
                <span className="text-[9px] text-text-muted leading-none mt-1 font-mono">
                  @{user.username.toLowerCase()}
                </span>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="rounded-none border border-border-muted bg-surface-base px-3 py-1 text-[9px] font-mono uppercase tracking-wider text-text-secondary hover:text-brand-accent hover:border-brand-accent transition-all duration-150 cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-brand-accent"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
