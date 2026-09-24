from app.models.campaign import Campaign

# ID заведомо вне диапазона реальных кампаний: тесты делят БД с
# синхронизированными данными, поэтому не полагаются на пустую таблицу.
FAKE_DIRECT_CAMPAIGN_ID = 900_000_001


def test_list_campaigns_empty_for_unknown_search(client):
    response = client.get(
        "/campaigns", params={"search": "zzz_несуществующая_кампания_zzz"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_campaigns_returns_seeded_row(client, db_session):
    db_session.add(
        Campaign(
            direct_campaign_id=FAKE_DIRECT_CAMPAIGN_ID,
            name="Поиск — бренд",
            state="ON",
            status="ACCEPTED",
        )
    )
    db_session.flush()

    response = client.get("/campaigns", params={"search": "Поиск — бренд"})

    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert names == ["Поиск — бренд"]
