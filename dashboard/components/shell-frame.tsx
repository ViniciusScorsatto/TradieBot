"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function ShellFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === "/login") {
    return <main className="main auth-main">{children}</main>;
  }

  return (
    <div className="shell">
      <Sidebar />
      <div className="workspace">
        <Topbar />
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
