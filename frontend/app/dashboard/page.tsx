"use client";

import { useEffect } from "react";

export default function DashboardRedirect() {
  useEffect(() => {
    // Automatically close the OAuth popup window to return focus to the parent window
    try {
      window.close();
    } catch (e) {
      console.error("Failed to auto-close popup window:", e);
    }
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background text-text-primary font-sans">
      <div className="flex items-center gap-1.5 mb-3 select-none animate-pulse">
        <div className="h-1.5 w-1.5 rounded-full bg-border-strong" />
        <div className="h-1.5 w-1.5 rounded-full bg-border-strong" />
        <div className="h-1.5 w-1.5 rounded-full bg-border-strong" />
      </div>
      <span className="text-[10px] font-mono tracking-widest uppercase text-text-secondary select-none">
        Redirecting to workspace...
      </span>
    </div>
  );
}
