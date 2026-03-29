"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function ShellFrame({
  children,
  promotionsEnabled,
}: {
  children: React.ReactNode;
  promotionsEnabled: boolean;
}) {
  const pathname = usePathname();

  if (pathname === "/login") {
    return <main className="main auth-main">{children}</main>;
  }

  return (
    <div className="shell">
      <Sidebar promotionsEnabled={promotionsEnabled} />
      <div className="workspace">
        <Topbar />
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
