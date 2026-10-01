const integerFormatter = new Intl.NumberFormat("ru-RU");
const percentFormatter = new Intl.NumberFormat("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const moneyFormatter = new Intl.NumberFormat("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const dateFormatter = new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
const dateTimeFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

/** null означает «не вычисляется» — всегда «—», никогда не 0. */
export function formatKpi(value: number | null, kind: "int" | "money" | "percent"): string {
  if (value === null) return "—";
  if (kind === "int") return integerFormatter.format(value);
  if (kind === "percent") return `${percentFormatter.format(value)}%`;
  return `${moneyFormatter.format(value)} ₽`;
}

export function formatInt(value: number): string {
  return integerFormatter.format(value);
}

export function formatDate(isoDate: string): string {
  // 'YYYY-MM-DD' -> локальная дата без сдвига часового пояса.
  const [year, month, day] = isoDate.split("-").map(Number);
  return dateFormatter.format(new Date(year!, (month ?? 1) - 1, day ?? 1));
}

export function formatDateTime(isoDateTime: string): string {
  return dateTimeFormatter.format(new Date(isoDateTime));
}
