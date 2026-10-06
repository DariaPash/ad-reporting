import { useState } from "react";
import type { UserCreatedOut, UserRole } from "../../types/api";
import { createUser } from "../../api/users";
import { isAppError } from "../../types/errors";

interface Props {
  onCreated: (user: UserCreatedOut) => void;
}

export function CreateUserForm({ onCreated }: Props) {
  const [username, setUsername] = useState("");
  const [role, setRole] = useState<UserRole>("specialist");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (username.trim().length < 3) {
      setError("Никнейм должен содержать не менее 3 символов.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const created = await createUser({ username: username.trim(), role });
      setUsername("");
      setRole("specialist");
      onCreated(created);
    } catch (err) {
      setError(isAppError(err) ? err.message : "Не удалось создать пользователя.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel" noValidate onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
      <h2>Новый пользователь</h2>
      <div className="grid2">
        <div>
          <label className="title" htmlFor="new-user-username">
            Никнейм
          </label>
          <input
            id="new-user-username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={submitting}
            aria-invalid={error ? true : undefined}
          />
        </div>
        <div>
          <label className="title" htmlFor="new-user-role">
            Роль
          </label>
          <select
            id="new-user-role"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            disabled={submitting}
            style={{ width: "100%", padding: "9px 10px", fontSize: 16, border: "1px solid #98a2b3", borderRadius: 5 }}
          >
            <option value="specialist">Специалист по рекламе</option>
            <option value="admin">Администратор</option>
          </select>
        </div>
      </div>
      <div className="field-error" role="alert">
        {error}
      </div>
      <div className="actions">
        <button type="submit" className="btn primary" disabled={submitting} aria-busy={submitting}>
          {submitting ? "Создание…" : "Создать пользователя"}
        </button>
      </div>
    </form>
  );
}
