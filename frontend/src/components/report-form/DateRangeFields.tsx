import type { Ref } from "react";

interface Props {
  dateFrom: string;
  dateTo: string;
  onChangeFrom: (value: string) => void;
  onChangeTo: (value: string) => void;
  errorFrom?: string;
  errorTo?: string;
  disabled: boolean;
  dateFromRef: Ref<HTMLInputElement>;
  dateToRef: Ref<HTMLInputElement>;
}

export function DateRangeFields({ dateFrom, dateTo, onChangeFrom, onChangeTo, errorFrom, errorTo, disabled, dateFromRef, dateToRef }: Props) {
  return (
    <>
      <h2>Период</h2>
      <div className="grid2">
        <div>
          <label className="title" htmlFor="date-from">
            Начальная дата *
          </label>
          <input
            id="date-from"
            ref={dateFromRef}
            type="date"
            value={dateFrom}
            disabled={disabled}
            className={errorFrom ? "invalid" : undefined}
            aria-invalid={Boolean(errorFrom)}
            aria-describedby="date-from-error"
            onChange={(e) => onChangeFrom(e.target.value)}
          />
          <div id="date-from-error" className="field-error">
            {errorFrom}
          </div>
        </div>
        <div>
          <label className="title" htmlFor="date-to">
            Конечная дата *
          </label>
          <input
            id="date-to"
            ref={dateToRef}
            type="date"
            value={dateTo}
            disabled={disabled}
            className={errorTo ? "invalid" : undefined}
            aria-invalid={Boolean(errorTo)}
            aria-describedby="date-to-error"
            onChange={(e) => onChangeTo(e.target.value)}
          />
          <div id="date-to-error" className="field-error">
            {errorTo}
          </div>
        </div>
      </div>
    </>
  );
}
