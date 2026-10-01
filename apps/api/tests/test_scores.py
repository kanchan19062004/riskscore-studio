from tests.conftest import train

GROCERY = {
    "amount": 42.5,
    "merchant_category": "grocery",
    "channel": "pos",
    "hour": 14,
    "account_age_days": 900,
    "avg_amount_30d": 48.0,
    "txn_count_24h": 2,
    "failed_attempts_24h": 0,
    "is_new_device": False,
    "country_mismatch": False,
}

RISKY = {
    "amount": 9200.0,
    "merchant_category": "crypto",
    "channel": "online",
    "hour": 3,
    "account_age_days": 8,
    "avg_amount_30d": 180.0,
    "txn_count_24h": 11,
    "failed_attempts_24h": 4,
    "is_new_device": True,
    "country_mismatch": True,
}


def score(client, headers, payload):
    return client.post("/api/v1/scores", json=payload, headers=headers)


def test_scoring_requires_login(client):
    assert client.post("/api/v1/scores", json=GROCERY).status_code == 401
    assert client.get("/api/v1/scores").status_code == 401


def test_scoring_404_without_a_model(client, analyst):
    assert score(client, analyst, GROCERY).status_code == 404


def test_invalid_hour_is_rejected(client, analyst):
    assert score(client, analyst, {**GROCERY, "hour": 25}).status_code == 422


def test_unknown_merchant_category_is_rejected(client, analyst):
    assert score(client, analyst, {**GROCERY, "merchant_category": "not-a-real-mcc"}).status_code == 422


def test_score_returns_risk_and_second_call_is_cached(client, admin, analyst):
    train(client, admin, seed=3)

    first = score(client, analyst, GROCERY)
    assert first.status_code == 201
    body = first.json()
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0 <= body["probability"] <= 1
    assert body["cache_hit"] is False
    assert body["model_version_id"] >= 1

    second = score(client, analyst, GROCERY).json()
    assert second["cache_hit"] is True
    assert second["probability"] == body["probability"]
    assert second["risk_level"] == body["risk_level"]
    assert second["id"] != body["id"]  # audit row is new even on a cache hit


def test_different_payload_misses_the_cache(client, admin, analyst):
    train(client, admin, seed=3)
    score(client, analyst, GROCERY)
    other = score(client, analyst, {**GROCERY, "amount": 43.0}).json()
    assert other["cache_hit"] is False


def test_risky_transaction_scores_higher_than_grocery(client, admin, analyst):
    train(client, admin, seed=3)
    grocery = score(client, analyst, GROCERY).json()["probability"]
    risky = score(client, analyst, RISKY).json()
    assert risky["probability"] > grocery
    assert risky["risk_level"] in {"MEDIUM", "HIGH"}


def test_history_is_private_to_the_scorer(client, admin, analyst):
    train(client, admin, seed=3)
    score(client, analyst, GROCERY)
    score(client, admin, RISKY)

    analyst_rows = client.get("/api/v1/scores", headers=analyst).json()["items"]
    admin_rows = client.get("/api/v1/scores", headers=admin).json()["items"]
    assert all(row["payload"]["merchant_category"] == "grocery" for row in analyst_rows)
    assert all(row["payload"]["merchant_category"] == "crypto" for row in admin_rows)


def test_admin_can_list_everyone_and_analyst_cannot(client, admin, analyst):
    train(client, admin, seed=3)
    score(client, analyst, GROCERY)
    score(client, admin, RISKY)

    everyone = client.get("/api/v1/scores?scope=all", headers=admin).json()
    assert everyone["total"] == 2
    assert client.get("/api/v1/scores?scope=all", headers=analyst).status_code == 403


def test_history_filters_and_pagination(client, admin, analyst):
    train(client, admin, seed=3)
    score(client, analyst, GROCERY)
    score(client, analyst, GROCERY)  # cache hit
    score(client, analyst, RISKY)

    grocery = client.get("/api/v1/scores?merchant_category=grocery", headers=analyst).json()
    assert grocery["total"] == 2
    assert all(row["payload"]["merchant_category"] == "grocery" for row in grocery["items"])

    hits = client.get("/api/v1/scores?cache_hit=true", headers=analyst).json()
    assert hits["total"] == 1
    assert hits["items"][0]["cache_hit"] is True

    page = client.get("/api/v1/scores?page=2&page_size=2", headers=analyst).json()
    assert page["page"] == 2
    assert page["page_size"] == 2
    assert page["total"] == 3
    assert len(page["items"]) == 1


def test_detail_hides_other_users_rows(client, admin, analyst):
    train(client, admin, seed=3)
    other_id = score(client, admin, RISKY).json()["id"]
    mine_id = score(client, analyst, GROCERY).json()["id"]

    assert client.get(f"/api/v1/scores/{other_id}", headers=analyst).status_code == 404
    mine = client.get(f"/api/v1/scores/{mine_id}", headers=analyst)
    assert mine.status_code == 200
    assert mine.json()["id"] == mine_id
    # Admins can open anyone's score for audit.
    assert client.get(f"/api/v1/scores/{mine_id}", headers=admin).status_code == 200


def test_csv_export_respects_filters(client, admin, analyst):
    train(client, admin, seed=3)
    score(client, analyst, GROCERY)
    score(client, analyst, RISKY)

    csv_body = client.get("/api/v1/scores/export?merchant_category=crypto", headers=analyst)
    assert csv_body.status_code == 200
    assert "text/csv" in csv_body.headers["content-type"]
    lines = csv_body.text.strip().splitlines()
    assert lines[0].startswith("created_at")
    assert len(lines) == 2
    assert "crypto" in lines[1]


def test_options_lists_categories(client, analyst):
    body = client.get("/api/v1/scores/options", headers=analyst).json()
    assert "crypto" in body["merchant_categories"]
    assert "online" in body["channels"]
