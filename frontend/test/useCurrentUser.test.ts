import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { isAdmin, useCurrentUser } from "../src/hooks/useCurrentUser";
import * as authApi from "../src/api/auth";
import type { UserOut } from "../src/types/api";

vi.mock("../src/api/auth", () => ({ getMe: vi.fn() }));

const ADMIN: UserOut = { id: 1, username: "admin", role: "admin", created_at: "2026-09-01T00:00:00Z" };
const SPECIALIST: UserOut = { id: 2, username: "bob", role: "specialist", created_at: "2026-09-01T00:00:00Z" };

describe("useCurrentUser", () => {
  it("reports isAdmin=true only once /auth/me resolves with role=admin", async () => {
    vi.mocked(authApi.getMe).mockResolvedValueOnce(ADMIN);
    const { result } = renderHook(() => useCurrentUser());

    expect(result.current.status).toBe("loading");
    expect(isAdmin(result.current)).toBe(false);

    await waitFor(() => expect(result.current.status).toBe("success"));
    expect(isAdmin(result.current)).toBe(true);
  });

  it("reports isAdmin=false for a specialist", async () => {
    vi.mocked(authApi.getMe).mockResolvedValueOnce(SPECIALIST);
    const { result } = renderHook(() => useCurrentUser());

    await waitFor(() => expect(result.current.status).toBe("success"));
    expect(isAdmin(result.current)).toBe(false);
  });

  it("falls back to isAdmin=false when /auth/me fails (e.g. not logged in)", async () => {
    vi.mocked(authApi.getMe).mockRejectedValueOnce({ kind: "network", httpStatus: null, code: null, message: "нет сети" });
    const { result } = renderHook(() => useCurrentUser());

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(isAdmin(result.current)).toBe(false);
  });
});
