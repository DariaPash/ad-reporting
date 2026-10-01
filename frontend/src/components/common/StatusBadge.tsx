import type { ReactNode } from "react";

export type BadgeTone = "ok" | "bad" | "neutral";

const ICON: Record<BadgeTone, string> = {
  ok: "✓",
  bad: "!",
  neutral: "",
};

/** Статус никогда не кодируется только цветом — всегда иконка + текст. */
export function StatusBadge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  const icon = ICON[tone];
  return (
    <span className={`badge${tone !== "neutral" ? ` ${tone}` : ""}`}>
      {icon ? `${icon} ` : ""}
      {children}
    </span>
  );
}
