import { useState } from "react";
import type { UserCreatedOut } from "../../types/api";

interface Props {
  user: UserCreatedOut;
  onDismiss: () => void;
}

/** Пароль показывается один раз — сервер его больше не отдаёт. Баннер закрывается
 * только вручную, чтобы администратор не потерял пароль случайно. */
export function GeneratedPasswordBanner({ user, onDismiss }: Props) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(user.password);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="panel" role="status" style={{ marginBottom: 16, borderColor: "var(--accent)" }}>
      <p style={{ margin: 0, fontWeight: 700 }}>
        Пользователь «{user.username}» создан. Пароль показан один раз — сохраните его.
      </p>
      <p className="formula" style={{ margin: "10px 0", wordBreak: "break-all" }}>
        {user.password}
      </p>
      <div className="actions" style={{ justifyContent: "flex-start" }}>
        <button type="button" className="btn" onClick={handleCopy}>
          {copied ? "Скопировано" : "Скопировать"}
        </button>
        <button type="button" className="btn" onClick={onDismiss}>
          Закрыть
        </button>
      </div>
    </div>
  );
}
