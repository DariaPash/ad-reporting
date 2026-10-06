import { useCallback, useState } from "react";
import { useAsyncList } from "../../hooks/useAsyncList";
import { listUsers } from "../../api/users";
import { ListState } from "../common/ListState";
import { UsersTable } from "./UsersTable";
import { CreateUserForm } from "./CreateUserForm";
import { GeneratedPasswordBanner } from "./GeneratedPasswordBanner";
import type { UserCreatedOut } from "../../types/api";

export function UsersPage() {
  const fetcher = useCallback(() => listUsers(), []);
  const { state, reload } = useAsyncList(fetcher);
  const [justCreated, setJustCreated] = useState<UserCreatedOut | null>(null);

  return (
    <>
      <h1>Пользователи</h1>
      <p className="lead">Создание учётных записей для входа в систему по никнейму и паролю.</p>

      {justCreated && <GeneratedPasswordBanner user={justCreated} onDismiss={() => setJustCreated(null)} />}

      <CreateUserForm
        onCreated={(user) => {
          setJustCreated(user);
          reload();
        }}
      />

      <ListState state={state} onRetry={reload} emptyTitle="Пользователей пока нет">
        {(users) => <UsersTable users={users} />}
      </ListState>
    </>
  );
}
