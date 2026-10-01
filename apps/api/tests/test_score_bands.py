from app.ml.score import risk_level
from app.ml.train import HIGH_RISK_THRESHOLD, REVIEW_THRESHOLD


def test_risk_bands():
    assert risk_level(0.0) == "LOW"
    assert risk_level(REVIEW_THRESHOLD - 1e-9) == "LOW"
    assert risk_level(REVIEW_THRESHOLD) == "MEDIUM"
    assert risk_level(HIGH_RISK_THRESHOLD - 1e-9) == "MEDIUM"
    assert risk_level(HIGH_RISK_THRESHOLD) == "HIGH"
    assert risk_level(1.0) == "HIGH"
