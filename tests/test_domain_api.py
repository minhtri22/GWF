from pathlib import Path
import yaml, pytest
from fastapi.testclient import TestClient
from gwr.domain import validate_domain
from gwr.errors import ValidationError
from gwr.api import create_app

def test_domain_validation_rejects_bad_primitive():
    bad={"domain_id":"x","version":"1","artifact_types":[{"id":"a","maps_to":"BAD","normative":False}],"trace_types":[],"workunit_templates":[],"gate_types":[],"failure_types":[],"recovery_policies":[],"roles":[],"authority_policies":[],"approval_policies":[]}
    with pytest.raises(ValidationError): validate_domain(bad)

def test_health_api(runtime):
    c=TestClient(create_app(runtime)); r=c.get('/health'); assert r.status_code==200 and r.json()["ok"] is True
