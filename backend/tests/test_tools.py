import pytest
from src.tools.validators import validate_incident_description
from src.tools.analyzers import calculate_risk_score, estimate_sla


def test_validate_incident_sqli():
    log = "POST /api/auth/login username=admin' UNION SELECT 1,password FROM users--"
    res = validate_incident_description(log)
    assert res["is_security_event"] is True
    assert "SQL_INJECTION" in res["security_types"]
    assert res["extracted_fields"]["component"] == "auth"


def test_validate_incident_xss():
    log = "GET /search?q=<script>alert('pwned')</script>"
    res = validate_incident_description(log)
    assert res["is_security_event"] is True
    assert "CROSS_SITE_SCRIPTING" in res["security_types"]


def test_validate_incident_path_traversal():
    log = "GET /api/static/../../../../etc/passwd"
    res = validate_incident_description(log)
    assert res["is_security_event"] is True
    assert "PATH_TRAVERSAL" in res["security_types"]


def test_validate_legitimate_log():
    log = "SELECT query completed in 45ms for user dashboard."
    res = validate_incident_description(log)
    assert res["is_security_event"] is False


def test_validate_sqli_boolean_based():
    log = "GET /product?id=1 AND 1=1--"
    res = validate_incident_description(log)
    assert res["is_security_event"] is True


def test_validate_xss_event_handler():
    log = "GET /page?q=<img src=x onerror=alert(1)>"
    res = validate_incident_description(log)
    assert res["is_security_event"] is True
    assert "CROSS_SITE_SCRIPTING" in res["security_types"]


def test_validate_component_detection_database():
    log = "Connection refused to postgres on port 5432"
    res = validate_incident_description(log)
    assert res["extracted_fields"]["component"] == "database"


def test_validate_component_detection_network():
    log = "ECONNREFUSED gateway proxy DNS resolution failed"
    res = validate_incident_description(log)
    assert res["extracted_fields"]["component"] == "network"


def test_calculate_risk_security_override():
    res = calculate_risk_score(
        component="auth", severity="P3", is_operational=True,
        is_security_event=True, historical_mttd=10.0
    )
    assert res["risk_score"] == 10.0
    assert res["severity"] == "P1"
    assert res["escalation_team"] == "SOC"
    assert res["category"] == "CRITICAL_SECURITY"


def test_calculate_risk_infrastructure_down():
    res = calculate_risk_score(
        component="database", severity="P1", is_operational=False,
        is_security_event=False, historical_mttd=4.0
    )
    assert res["risk_score"] >= 8.0
    assert res["escalation_team"] == "On-call SRE"


def test_calculate_risk_low_severity_operational():
    res = calculate_risk_score(
        component="frontend", severity="P3", is_operational=True,
        is_security_event=False, historical_mttd=30.0
    )
    assert res["risk_score"] < 5.0
    assert res["escalation_team"] == "Platform Team"


def test_estimate_sla_targets():
    sla_p1 = estimate_sla("P1")
    assert sla_p1["sla_response_minutes"] == 15
    assert sla_p1["sla_resolution_minutes"] == 60

    sla_p2 = estimate_sla("P2")
    assert sla_p2["sla_response_minutes"] == 30
    assert sla_p2["sla_resolution_minutes"] == 240


def test_estimate_sla_with_historical_mttr():
    sla = estimate_sla("P1", historical_mttr=45.0)
    assert sla["estimated_mttr_minutes"] == 45.0
    assert sla["sla_risk"] == "NORMAL"
