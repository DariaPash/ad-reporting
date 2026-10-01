import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ReportForm } from "./components/report-form/ReportForm";
import { ReportView } from "./components/report-view/ReportView";
import { ReportHistory } from "./components/report-history/ReportHistory";
import { OperationsLog } from "./components/operations-log/OperationsLog";
import { HelpPage } from "./components/help/HelpPage";
import { UsersPage } from "./components/users/UsersPage";
import { MonitoringPage } from "./components/monitoring/MonitoringPage";
import { isAdmin, useCurrentUser } from "./hooks/useCurrentUser";

/** Клиентский гейт админ-маршрутов — только UX, настоящая проверка роли на бэкенде.
 * Пока роль загружается, ничего не рендерим, чтобы не мелькала админ-страница. */
function AdminOnly({ children }: { children: ReactNode }) {
  const currentUser = useCurrentUser();
  if (currentUser.status === "loading") return null;
  if (!isAdmin(currentUser)) return <Navigate to="/report/new" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/report/new" replace />} />
        <Route path="/report/new" element={<ReportForm />} />
        <Route path="/reports" element={<ReportHistory />} />
        <Route path="/reports/:id" element={<ReportView />} />
        <Route
          path="/operations"
          element={
            <AdminOnly>
              <OperationsLog />
            </AdminOnly>
          }
        />
        <Route path="/help" element={<HelpPage />} />
        <Route
          path="/users"
          element={
            <AdminOnly>
              <UsersPage />
            </AdminOnly>
          }
        />
        <Route
          path="/monitoring"
          element={
            <AdminOnly>
              <MonitoringPage />
            </AdminOnly>
          }
        />
        <Route path="*" element={<Navigate to="/report/new" replace />} />
      </Routes>
    </AppShell>
  );
}
