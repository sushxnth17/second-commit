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
    <nav className="sticky top-0 z-50 w-full border-b border-zinc-900 bg-zinc-950/80 backdrop-blur-md transition-colors">
      <div className="mx-auto max-w-5xl px-6">
        <div className="flex h-14 items-center justify-between">
          <div className="flex h-full items-center">
            {/* Logo */}
            <div className="flex items-center cursor-pointer select-none" onClick={() => setActiveTab("dashboard")}>
              <span className="font-serif italic text-base font-normal tracking-wide text-white">
                SecondCommit
              </span>
            </div>

            {/* Navigation Tabs */}
            <div className="flex h-full items-center gap-6 ml-8">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`flex items-center h-full text-[10px] font-mono uppercase tracking-widest transition-all border-b pt-0.5 cursor-pointer outline-none ${
                  activeTab === "dashboard"
                    ? "border-white text-white"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab("analytics")}
                className={`flex items-center h-full text-[10px] font-mono uppercase tracking-widest transition-all border-b pt-0.5 cursor-pointer outline-none ${
                  activeTab === "analytics"
                    ? "border-white text-white"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
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
                className="h-5 w-5 rounded-none border border-zinc-800 bg-zinc-900 object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${user.name || user.username}`;
                }}
              />
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-[11px] font-medium text-zinc-300 leading-none">
                  {user.name || user.username}
                </span>
                <span className="text-[9px] text-zinc-500 leading-none mt-1 font-mono">
                  @{user.username.toLowerCase()}
                </span>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="rounded-none border border-zinc-800 bg-zinc-950 px-3 py-1 text-[10px] font-mono uppercase tracking-wider text-zinc-400 hover:text-white hover:bg-zinc-900 hover:border-zinc-700 transition-all cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
