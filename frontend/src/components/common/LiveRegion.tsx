import type { ReactNode } from "react";

/** Уведомления об асинхронном результате должны попадать в live region. */
export function LiveRegion({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={className} role="status" aria-live="polite">
      {children}
    </div>
  );
}
