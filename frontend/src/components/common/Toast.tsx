export function Toast({ message, tone = "info" }: { message: string; tone?: "info" | "error" }) {
  return (
    <div className={`toast${tone === "error" ? " error" : ""}`} role="status" aria-live="polite">
      {message}
    </div>
  );
}
