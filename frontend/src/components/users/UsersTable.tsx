import type { UserOut } from "../../types/api";
import { StatusBadge } from "../common/StatusBadge";
import { formatDateTime } from "../../utils/format";

export function UsersTable({ users }: { users: UserOut[] }) {
  return (
    <div className="panel">
      <div className="table-scroll">
        <table>
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
                <td>{u.username}</td>
                <td>
                  {u.role === "admin" ? (
                    <StatusBadge tone="neutral">администратор</StatusBadge>
                  ) : (
                    <StatusBadge tone="neutral">специалист</StatusBadge>
                  )}
                </td>
                <td>{formatDateTime(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
