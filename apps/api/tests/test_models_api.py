from app.core.config import settings
from app.services import model_registry
from tests.conftest import train


def test_model_endpoints_require_login(client):
    assert client.get("/api/v1/models").status_code == 401
    assert client.post("/api/v1/models/train", json={}).status_code == 401


def test_analyst_cannot_train(client, analyst):
    assert train(client, analyst).status_code == 403


def test_active_model_is_404_before_any_training(client, analyst):
    assert client.get("/api/v1/models/active", headers=analyst).status_code == 404


def test_first_trained_model_is_promoted_and_saved(client, admin, analyst):
    response = train(client, admin, seed=3)

    assert response.status_code == 201
    body = response.json()
    assert body["promoted"] is True
    assert body["champion_pr_auc"] is None
    assert body["version"]["is_active"] is True
    assert body["version"]["dataset"]["seed"] == 3
    assert (settings.MODEL_DIR / f"risk_model_v{body['version']['id']}.joblib").exists()

    active = client.get("/api/v1/models/active", headers=analyst).json()
    assert active["id"] == body["version"]["id"]


def test_champion_is_scored_on_the_challengers_test_set(client, admin):
    train(client, admin, seed=3)
    # Same seed means same data and an identical model, so the scores must match exactly.
    challenger = train(client, admin, seed=3).json()

    assert challenger["champion_pr_auc"] == challenger["version"]["metrics"]["pr_auc"]
    assert challenger["promoted"] is True


def test_weaker_challenger_is_not_promoted_but_can_be_activated(client, admin, monkeypatch):
    champion_id = train(client, admin, seed=3).json()["version"]["id"]
    monkeypatch.setattr(model_registry, "_champion_pr_auc", lambda champion, result: 1.0)

    challenger = train(client, admin, seed=4).json()
    assert challenger["promoted"] is False
    assert client.get("/api/v1/models/active", headers=admin).json()["id"] == champion_id

    challenger_id = challenger["version"]["id"]
    activated = client.post(f"/api/v1/models/{challenger_id}/activate", headers=admin)
    assert activated.status_code == 200

    versions = {v["id"]: v["is_active"] for v in client.get("/api/v1/models", headers=admin).json()}
    assert versions == {challenger_id: True, champion_id: False}


def test_train_rejects_tiny_datasets(client, admin):
    assert train(client, admin, n_samples=500).status_code == 422
