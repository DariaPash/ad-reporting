import { NavLink } from "react-router-dom";
import { isAdmin, useCurrentUser } from "../../hooks/useCurrentUser";

/** Боковая навигация. Раздел «Администрирование» виден только администратору —
 * это только UX, реальная проверка роли на бэкенде. */
export function Sidebar() {
  const currentUser = useCurrentUser();
  const admin = isAdmin(currentUser);

  return (
    <aside style={{ padding: "22px 16px", color: "#e4e7ec", background: "var(--sidebar-bg)" }}>
      <NavLink to="/report/new" style={{ display: "block", margin: "0 8px 28px", fontSize: 17, fontWeight: 700, color: "#fff", textDecoration: "none" }}>
        Ad Reporting
      </NavLink>
      <nav>
        <SidebarLink to="/report/new">Формирование отчета</SidebarLink>
        {/* end — иначе страница /reports/:id тоже подсвечивала бы «История отчетов» */}
        <SidebarLink to="/reports" end>
          История отчетов
        </SidebarLink>
        <SidebarLink to="/help">Справка</SidebarLink>
        {/* Раздел «Администрирование» — только для роли admin. */}
        {admin && (
          <>
            <hr style={{ margin: "16px 10px", border: 0, borderTop: "1px solid #475467" }} />
            <small style={{ display: "block", margin: "0 12px 7px", color: "#98a2b3", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Администрирование
            </small>
            <SidebarLink to="/operations">Журнал операций</SidebarLink>
            <SidebarLink to="/users">Пользователи</SidebarLink>
            <SidebarLink to="/monitoring">Мониторинг</SidebarLink>
          </>
        )}
      </nav>
    </aside>
  );
}

function SidebarLink({ to, children, end }: { to: string; children: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      style={({ isActive }) => ({
        display: "block",
        margin: "4px 0",
        padding: "11px 12px",
        textAlign: "left",
        color: isActive ? "#fff" : "var(--sidebar-text)",
        background: isActive ? "var(--sidebar-current)" : "transparent",
        borderRadius: 6,
        textDecoration: "none",
      })}
    >
      {children}
    </NavLink>
  );
}
