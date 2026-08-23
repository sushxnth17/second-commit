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
          <div className="flex items-center gap-6">
            {/* Logo */}
            <div className="flex items-center cursor-pointer" onClick={() => setActiveTab("dashboard")}>
              <div className="flex h-7 w-7 items-center justify-center rounded border border-zinc-800 bg-zinc-900 text-indigo-400">
                <span className="font-sans text-xs font-black tracking-wider">2C</span>
              </div>
              <span className="text-sm font-bold tracking-tight text-white ml-2.5">
                SecondCommit
              </span>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                  activeTab === "dashboard"
                    ? "bg-zinc-900 text-white border border-zinc-800"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab("analytics")}
                className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                  activeTab === "analytics"
                    ? "bg-zinc-900 text-white border border-zinc-800"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Analytics
              </button>
            </div>
          </div>

          {/* Right Hand Profile Actions */}
          <div className="flex items-center gap-4">
            {/* User Profile Summary */}
            <div className="flex items-center gap-2">
              <img
                src={avatarUrl}
                alt={user.name || user.username}
                className="h-6 w-6 rounded border border-zinc-800 bg-zinc-900 object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${user.name || user.username}`;
                }}
              />
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-medium text-zinc-300 leading-none">
                  {user.name || user.username}
                </span>
                <span className="text-[9px] text-zinc-550 leading-none mt-0.5 font-mono">
                  @{user.username.toLowerCase()}
                </span>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="rounded border border-zinc-800 bg-zinc-900/30 px-2.5 py-1 text-[10px] font-semibold text-zinc-400 hover:text-white hover:bg-zinc-900 hover:border-zinc-700 transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
