export interface FieldErrors {
  dateFrom?: string;
  dateTo?: string;
  campaigns?: string;
}

export interface ReportFormValues {
  dateFrom: string;
  dateTo: string;
  campaignIds: number[];
}

/** Правила валидации формы отчёта. */
export function validateReportForm(values: ReportFormValues): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.dateFrom) {
    errors.dateFrom = "Укажите начальную дату.";
  }
  if (!values.dateTo) {
    errors.dateTo = "Укажите конечную дату.";
  }
  if (values.dateFrom && values.dateTo && values.dateFrom > values.dateTo) {
    errors.dateFrom = "Начальная дата не может быть позже конечной.";
  }
  if (values.campaignIds.length === 0) {
    errors.campaigns = "Выберите хотя бы одну рекламную кампанию.";
  }

  return errors;
}

export function firstErrorField(errors: FieldErrors): keyof FieldErrors | null {
  if (errors.dateFrom) return "dateFrom";
  if (errors.dateTo) return "dateTo";
  if (errors.campaigns) return "campaigns";
  return null;
}
