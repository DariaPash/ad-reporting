import { act, renderHook } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useReportSubmit } from "../src/hooks/useReportSubmit";
import * as reportsApi from "../src/api/reports";

vi.mock("../src/api/reports", () => ({ createReport: vi.fn() }));

const navigateMock = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigateMock };
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const VALID_PAYLOAD = { dateFrom: "2026-08-01", dateTo: "2026-08-31", campaignIds: [1], goalIds: [] };

beforeEach(() => {
  vi.useFakeTimers();
  navigateMock.mockClear();
  vi.mocked(reportsApi.createReport).mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useReportSubmit", () => {
  it("sets validation_error and never calls the API for invalid input", async () => {
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    await act(async () => {
      await result.current.submit({ dateFrom: "", dateTo: "2026-08-31", campaignIds: [], goalIds: [] });
    });

    expect(result.current.phase.kind).toBe("validation_error");
    expect(reportsApi.createReport).not.toHaveBeenCalled();
  });

  it("cycles through cosmetic stages on schedule while the request is pending", async () => {
    const { promise } = deferred<{ id: number }>();
    vi.mocked(reportsApi.createReport).mockReturnValue(promise as never);
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    act(() => {
      void result.current.submit(VALID_PAYLOAD);
    });
    expect(result.current.phase.kind).toBe("checking");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(result.current.phase.kind).toBe("fetching");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(800); // -> 1400ms total
    });
    expect(result.current.phase.kind).toBe("calculating");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1200); // -> 2600ms total
    });
    expect(result.current.phase.kind).toBe("saving");

    // Дальнейшее ожидание не должно откатывать стадию назад.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(result.current.phase.kind).toBe("saving");
  });

  it("navigates to the new report on success, regardless of which stage was showing", async () => {
    const { promise, resolve } = deferred<{ id: number }>();
    vi.mocked(reportsApi.createReport).mockReturnValue(promise as never);
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    act(() => {
      void result.current.submit(VALID_PAYLOAD);
    });

    await act(async () => {
      resolve({ id: 42 });
      await promise;
    });

    expect(result.current.phase).toEqual({ kind: "report", reportId: 42 });
    expect(navigateMock).toHaveBeenCalledWith("/reports/42", { replace: true });
  });

  it("classifies a network failure as api_error with the exact spec-mandated message", async () => {
    vi.mocked(reportsApi.createReport).mockRejectedValue({ kind: "network", httpStatus: null, code: null, message: "boom" });
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    await act(async () => {
      await result.current.submit(VALID_PAYLOAD);
    });

    expect(result.current.phase).toEqual({
      kind: "api_error",
      message: "Не удалось получить недостающую статистику. Ранее сохраненные данные не изменены.",
    });
  });

  it("classifies external_api_error (502) as api_error, independent of the currently displayed stage", async () => {
    vi.mocked(reportsApi.createReport).mockRejectedValue({
      kind: "domain",
      httpStatus: 502,
      code: "external_api_error",
      message: "backend text should not matter",
    });
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    await act(async () => {
      await result.current.submit(VALID_PAYLOAD);
    });

    expect(result.current.phase.kind).toBe("api_error");
  });

  it("classifies any other error (e.g. unexpected 500) as a generic save_error", async () => {
    vi.mocked(reportsApi.createReport).mockRejectedValue({
      kind: "domain",
      httpStatus: 500,
      code: "internal_error",
      message: "should not be shown",
    });
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    await act(async () => {
      await result.current.submit(VALID_PAYLOAD);
    });

    expect(result.current.phase).toEqual({ kind: "save_error", message: "Не удалось сформировать отчет. Попробуйте еще раз." });
  });

  it("ignores a second submit while the first is still in flight (no duplicate API call)", async () => {
    const { promise } = deferred<{ id: number }>();
    vi.mocked(reportsApi.createReport).mockReturnValue(promise as never);
    const { result } = renderHook(() => useReportSubmit(), { wrapper: MemoryRouter });

    act(() => {
      void result.current.submit(VALID_PAYLOAD);
      void result.current.submit(VALID_PAYLOAD);
    });

    expect(reportsApi.createReport).toHaveBeenCalledTimes(1);
  });
});
