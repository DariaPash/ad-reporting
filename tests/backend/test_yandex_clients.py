"""Тесты парсинга реальных форматов ответов Direct/Metrika.

Фикстуры – реальные ответы API. Metrika возвращает измерение даты как
{"name": "2026-09-14"}, а не {"value": ...}.
"""

from __future__ import annotations

import datetime

import pytest

from app.clients.yandex_direct_client import YandexDirectClient
from app.clients.yandex_metrika_client import YandexMetrikaClient


class FakeResponse:
    def __init__(
        self, *, json_data=None, text="", status_code=200, headers=None
    ):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, response: FakeResponse):
        self._response = response
        self.calls: list[dict] = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self._response

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self._response


# --------------------------------------------------------------------- #
# Direct – TSV с реальными данными
# --------------------------------------------------------------------- #

REAL_DIRECT_TSV = (
    "Date\tCampaignId\tCampaignName\tImpressions\tClicks\tCost\n"
    "2026-09-01\t52556566\tМетконцепт ПОИСК\t132\t6\t415.09\n"
    "2026-09-01\t117788678\tyd_mk_armatur_karkasy\t2640\t1\t31.66\n"
)


def test_direct_client_parses_real_tsv_with_extra_columns():
    session = FakeSession(FakeResponse(text=REAL_DIRECT_TSV, status_code=200))
    client = YandexDirectClient(token="t", session=session)

    rows = client.get_daily_statistics(
        datetime.date(2026, 9, 1), datetime.date(2026, 9, 1)
    )

    assert len(rows) == 2
    assert rows[0].campaign_id == 52556566
    assert rows[0].impressions == 132
    assert rows[0].clicks == 6
    assert rows[0].cost == pytest.approx(415.09)


def test_direct_client_report_queued_then_ready(monkeypatch):
    """201/202 – отчёт в очереди; клиент должен повторить запрос без sleep в
    тесте."""
    responses = iter(
        [
            FakeResponse(status_code=201, headers={"retryIn": "1"}),
            FakeResponse(text=REAL_DIRECT_TSV, status_code=200),
        ]
    )

    class SequencedSession(FakeSession):
        def post(self, url, **kwargs):
            self.calls.append({"url": url, **kwargs})
            return next(responses)

    monkeypatch.setattr(
        "app.clients.yandex_direct_client.time.sleep", lambda _seconds: None
    )
    client = YandexDirectClient(token="t", session=SequencedSession(None))

    rows = client.get_daily_statistics(
        datetime.date(2026, 9, 1), datetime.date(2026, 9, 1)
    )

    assert len(rows) == 2


# --------------------------------------------------------------------- #
# Metrika – JSON с реальной формой измерений
# --------------------------------------------------------------------- #

REAL_METRIKA_PAYLOAD = {
    "sampled": False,
    "data": [
        {
            "dimensions": [
                {"name": "2026-09-07"},
                {"id": None, "owner": None, "name": None, "direct_id": None},
            ],
            "metrics": [16.0, 2.0],
        },
        {
            "dimensions": [
                {"name": "2026-09-04"},
                {
                    "id": "33222679",
                    "owner": "1",
                    "name": "Метконцепт ПОИСК",
                    "direct_id": "N-52556566",
                },
            ],
            "metrics": [8.0, 0.0],
        },
    ],
}


def test_metrika_client_parses_real_dimension_shape():
    session = FakeSession(
        FakeResponse(json_data=REAL_METRIKA_PAYLOAD, status_code=200)
    )
    client = YandexMetrikaClient(token="t", session=session)

    rows = client.get_daily_statistics(
        counter_id="55327960",
        goal_ids=[329796778],
        date_from=datetime.date(2026, 9, 4),
        date_to=datetime.date(2026, 9, 7),
    )

    assert len(rows) == 2
    unset_row = next(
        r for r in rows if r.stat_date == datetime.date(2026, 9, 7)
    )
    assert (
        unset_row.campaign_id is None
    )  # "(not set)" – не привязано к кампании Директа
    assert unset_row.visits == 16
    assert unset_row.goal_reaches[329796778] == 2

    known_row = next(
        r for r in rows if r.stat_date == datetime.date(2026, 9, 4)
    )
    assert known_row.campaign_id == 52556566  # "N-" снят
    assert known_row.visits == 8


# --------------------------------------------------------------------- #
# Секреты никогда не попадают в текст исключения: это сообщение уходит
# в HTTP-ответ клиенту.
# --------------------------------------------------------------------- #

FAKE_TOKEN = "y0__xSecretDirectTokenValueThatMustNeverLeak"


def test_direct_client_error_message_never_contains_response_body_or_token():
    error_body = {
        "error": {"error_string": "плохой токен", "error_detail": FAKE_TOKEN}
    }
    session = FakeSession(FakeResponse(json_data=error_body, status_code=200))
    client = YandexDirectClient(token=FAKE_TOKEN, session=session)

    with pytest.raises(Exception) as exc_info:
        client.get_campaigns()

    assert FAKE_TOKEN not in str(exc_info.value)


def test_direct_client_http_error_message_never_contains_response_body():
    session = FakeSession(
        FakeResponse(json_data={"secret_leak": FAKE_TOKEN}, status_code=400)
    )
    client = YandexDirectClient(token=FAKE_TOKEN, session=session)

    with pytest.raises(Exception) as exc_info:
        client.get_campaigns()

    assert FAKE_TOKEN not in str(exc_info.value)


def test_metrika_client_error_message_never_contains_response_body_or_token():
    session = FakeSession(
        FakeResponse(json_data={"secret_leak": FAKE_TOKEN}, status_code=403)
    )
    client = YandexMetrikaClient(token=FAKE_TOKEN, session=session)

    with pytest.raises(Exception) as exc_info:
        client.get_goals("55327960")

    assert FAKE_TOKEN not in str(exc_info.value)


def test_direct_client_never_sends_token_anywhere_but_authorization_header():
    """Токен должен попадать ровно в один заголовок и никуда больше (не в
    тело запроса, не в query, не задваиваться в других заголовках)."""
    session = FakeSession(
        FakeResponse(json_data={"result": {"Campaigns": []}}, status_code=200)
    )
    client = YandexDirectClient(token=FAKE_TOKEN, session=session)

    client.get_campaigns()

    call = session.calls[0]
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert FAKE_TOKEN not in str(call.get("json", {}))
