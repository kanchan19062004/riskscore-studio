from app.ml.train import HIGH_RISK_THRESHOLD, REVIEW_THRESHOLD

RiskLevel = str


def risk_level(probability: float) -> RiskLevel:
    if probability >= HIGH_RISK_THRESHOLD:
        return "HIGH"
    if probability >= REVIEW_THRESHOLD:
        return "MEDIUM"
    return "LOW"
