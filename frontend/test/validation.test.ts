import { describe, expect, it } from "vitest";
import { validateReportForm, firstErrorField } from "../src/utils/validation";

describe("validateReportForm", () => {
  it("requires a start date", () => {
    const errors = validateReportForm({ dateFrom: "", dateTo: "2026-08-31", campaignIds: [1] });
    expect(errors.dateFrom).toBe("Укажите начальную дату.");
  });

  it("requires an end date", () => {
    const errors = validateReportForm({ dateFrom: "2026-08-01", dateTo: "", campaignIds: [1] });
    expect(errors.dateTo).toBe("Укажите конечную дату.");
  });

  it("rejects a start date after the end date", () => {
    const errors = validateReportForm({ dateFrom: "2026-09-01", dateTo: "2026-08-01", campaignIds: [1] });
    expect(errors.dateFrom).toBe("Начальная дата не может быть позже конечной.");
  });

  it("allows a single-day period (start === end)", () => {
    const errors = validateReportForm({ dateFrom: "2026-08-01", dateTo: "2026-08-01", campaignIds: [1] });
    expect(errors.dateFrom).toBeUndefined();
  });

  it("requires at least one campaign", () => {
    const errors = validateReportForm({ dateFrom: "2026-08-01", dateTo: "2026-08-31", campaignIds: [] });
    expect(errors.campaigns).toBe("Выберите хотя бы одну рекламную кампанию.");
  });

  it("passes with valid values", () => {
    const errors = validateReportForm({ dateFrom: "2026-08-01", dateTo: "2026-08-31", campaignIds: [1, 2] });
    expect(errors).toEqual({});
  });
});

describe("firstErrorField", () => {
  it("prioritizes dateFrom, then dateTo, then campaigns", () => {
    expect(firstErrorField({ dateFrom: "x", dateTo: "y", campaigns: "z" })).toBe("dateFrom");
    expect(firstErrorField({ dateTo: "y", campaigns: "z" })).toBe("dateTo");
    expect(firstErrorField({ campaigns: "z" })).toBe("campaigns");
    expect(firstErrorField({})).toBeNull();
  });
});
