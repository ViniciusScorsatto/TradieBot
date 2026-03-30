import { ShellFrame } from "../../components/shell-frame";

export default function DashboardShellLayout({ children }: { children: React.ReactNode }) {
  const promotionsEnabled =
    (process.env.ENABLE_PROMOTIONS ?? "false").trim().toLowerCase() === "true" ||
    (process.env.ENABLE_PROMOTIONS ?? "").trim() === "1";

  return <ShellFrame promotionsEnabled={promotionsEnabled}>{children}</ShellFrame>;
}
