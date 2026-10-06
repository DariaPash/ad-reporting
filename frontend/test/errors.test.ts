import { afterEach, describe, expect, it, vi } from "vitest";
import { request } from "../src/api/client";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("request() error normalization", () => {
  it("classifies a thrown fetch (network failure) as kind:network", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(request("/campaigns")).rejects.toMatchObject({
      kind: "network",
      httpStatus: null,
    });
  });

  it("normalizes a domain error {code,message} from core/exceptions.py", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(502, { code: "external_api_error", message: "Не удалось получить статистику Директа." })),
    );

    await expect(request("/reports")).rejects.toMatchObject({
      kind: "domain",
      httpStatus: 502,
      code: "external_api_error",
    });
  });

  it("normalizes FastAPI's own {detail:[...]} validation shape without leaking detail contents", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(422, { detail: [{ loc: ["query", "status"], msg: "invalid", type: "value_error" }] })),
    );

    const error = (await request("/operations").catch((e: unknown) => e)) as { kind: string; message: string };
    expect(error.kind).toBe("validation");
    expect(error.message).not.toContain("value_error");
    expect(error.message).not.toContain("loc");
  });

  it("falls back to kind:unknown for a non-JSON error body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>502 Bad Gateway</html>", { status: 502 })));

    await expect(request("/health")).rejects.toMatchObject({ kind: "unknown", httpStatus: 502 });
  });

  it("returns the parsed body on success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { status: "ok", database: "ok" })));

    await expect(request("/health")).resolves.toEqual({ status: "ok", database: "ok" });
  });
});
