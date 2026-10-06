import { describe, expect, it } from "vitest";
import { formatKpi, formatDate } from "../src/utils/format";

describe("formatKpi", () => {
  it("renders null as em dash, never as 0", () => {
    expect(formatKpi(null, "int")).toBe("—");
    expect(formatKpi(null, "money")).toBe("—");
    expect(formatKpi(null, "percent")).toBe("—");
  });

  it("formats integers with ru-RU thousands grouping", () => {
    expect(formatKpi(482910, "int")).toBe("482 910");
  });

  it("formats money with two decimals and the ruble sign", () => {
    expect(formatKpi(128540, "money")).toBe("128 540,00 ₽");
  });

  it("formats percent with two decimals and a percent sign", () => {
    expect(formatKpi(3.28, "percent")).toBe("3,28%");
  });

  it("treats 0 as a real computed value, not as null", () => {
    expect(formatKpi(0, "int")).toBe("0");
    expect(formatKpi(0, "percent")).toBe("0,00%");
  });
});

describe("formatDate", () => {
  it("formats an ISO date without a timezone shift", () => {
    expect(formatDate("2026-08-01")).toBe("01.08.2026");
    expect(formatDate("2026-12-31")).toBe("31.12.2026");
  });
});
