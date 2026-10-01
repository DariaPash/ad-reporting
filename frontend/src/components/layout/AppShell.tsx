import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

/** Сайдбар 224px + независимо прокручиваемая основная область. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "224px 1fr", minHeight: "100vh" }}>
      <Sidebar />
      <main style={{ minWidth: 0, padding: "25px 30px", overflow: "auto" }}>{children}</main>
    </div>
  );
}
