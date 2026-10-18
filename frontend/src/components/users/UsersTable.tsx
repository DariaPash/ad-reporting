import type { UserOut } from "../../types/api";
import { StatusBadge } from "../common/StatusBadge";
import { formatDateTime } from "../../utils/format";

export function UsersTable({ users }: { users: UserOut[] }) {
  return (
    <div className="panel">
      <div className="table-scroll">
        <table className="cards">
          <thead>
            <tr>
              <th>Никнейм</th>
              <th style={{ width: 140 }}>Роль</th>
              <th style={{ width: 180 }}>Создан</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="cell-title">{u.username}</td>
                <td data-label="Роль">
                  {u.role === "admin" ? (
                    <StatusBadge tone="neutral">администратор</StatusBadge>
                  ) : (
                    <StatusBadge tone="neutral">специалист</StatusBadge>
                  )}
                </td>
                <td data-label="Создан">{formatDateTime(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
