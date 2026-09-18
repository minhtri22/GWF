from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import re

import yaml

from .domain import DomainPackage, load_domain, validate_domain
from .errors import ValidationError
from .utils import content_hash


_DOMAIN_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


@dataclass(frozen=True)
class DomainValidationReport:
    ok: bool
    domain_id: str | None
    version: str | None
    fingerprint: str | None
    counts: dict[str, int]
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DomainSDK:
    """Developer-facing SDK for authoring and validating declarative GWR domains."""

    sections = (
        "artifact_types", "trace_types", "workunit_templates", "evidence_types",
        "gate_types", "failure_types", "recovery_policies", "roles",
        "authority_policies", "approval_policies", "skill_contracts",
    )

    @classmethod
    def _load_data(cls, source: str | Path | dict[str, Any]) -> dict[str, Any]:
        if isinstance(source, dict):
            return source
        path = Path(source)
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    @classmethod
    def validate(cls, source: str | Path | dict[str, Any]) -> DomainValidationReport:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        try:
            data = cls._load_data(source)
        except Exception as exc:
            return DomainValidationReport(False, None, None, None, {}, [{"code": "PARSE_ERROR", "message": str(exc)}], [])
        if not isinstance(data, dict):
            return DomainValidationReport(False, None, None, None, {}, [{"code": "ROOT_NOT_OBJECT", "message": "Domain YAML root must be an object"}], [])

        domain_id = data.get("domain_id")
        version = str(data.get("version")) if data.get("version") is not None else None
        if domain_id and not _DOMAIN_ID.match(str(domain_id)):
            errors.append({"code": "DOMAIN_ID_FORMAT", "message": "domain_id must be lowercase and URL/CLI safe"})
        try:
            validate_domain(data)
        except ValidationError as exc:
            errors.append({"code": exc.code, "message": exc.message, "details": exc.details})
        except Exception as exc:
            errors.append({"code": "VALIDATION_EXCEPTION", "message": str(exc)})

        counts = {section: len(data.get(section, []) or []) for section in cls.sections}
        if not data.get("description"):
            warnings.append({"code": "DESCRIPTION_MISSING", "message": "Add a domain description for operator-facing surfaces."})
        if not data.get("compatible_runtime_versions"):
            warnings.append({"code": "RUNTIME_COMPATIBILITY_MISSING", "message": "Declare compatible_runtime_versions before publishing the domain."})
        if not data.get("product"):
            warnings.append({"code": "PRODUCT_METADATA_MISSING", "message": "Optional product metadata can provide display_name and category in v0.8 UI."})
        fingerprint = content_hash(data)
        return DomainValidationReport(not errors, str(domain_id) if domain_id else None, version, fingerprint, counts, errors, warnings)

    @classmethod
    def inspect(cls, source: str | Path | dict[str, Any]) -> dict[str, Any]:
        data = cls._load_data(source)
        report = cls.validate(data)
        if not report.ok:
            raise ValidationError("Domain package is invalid", details=report.to_dict())
        pkg = DomainPackage(data)
        dependencies = []
        for artifact in data.get("artifact_types", []) or []:
            for dep in artifact.get("hard_dependencies", []) or []:
                dependencies.append({"from": artifact["id"], "to": dep, "kind": "HARD"})
        workunits = []
        for wu in pkg.workunits():
            workunits.append({
                "id": wu["id"],
                "executor_role": wu.get("executor_role"),
                "skill_ref": wu.get("skill_ref"),
                "agent_protocol": wu.get("agent_protocol", {}),
                "inputs": [x.get("artifact_type") if isinstance(x, dict) else x for x in wu.get("inputs", [])],
                "outputs": [x.get("artifact_type") if isinstance(x, dict) else x for x in wu.get("outputs", [])],
                "gates": list(wu.get("required_gate_types", []) or []),
                "known_failure_modes": list(wu.get("known_failure_modes", []) or []),
            })
        return {
            "domain_id": pkg.domain_id,
            "version": data.get("version"),
            "description": data.get("description"),
            "fingerprint": report.fingerprint,
            "counts": report.counts,
            "dependencies": dependencies,
            "workunits": workunits,
            "roles": [x.get("id") for x in data.get("roles", []) or []],
            "skill_contracts": list((data.get("skill_contracts", {}) or {}).keys()),
            "agent_protocol": data.get("agent_protocol", {}) or {},
            "warnings": report.warnings,
        }

    @classmethod
    def scaffold(cls, domain_id: str, *, display_name: str | None = None) -> str:
        if not _DOMAIN_ID.match(domain_id):
            raise ValidationError("Invalid domain_id for scaffold")
        display = display_name or domain_id.replace("-", " ").replace("_", " ").title()
        data = {
            "domain_id": domain_id,
            "version": "0.1.0",
            "compatible_runtime_versions": ["0.8.x"],
            "description": f"{display} workflow domain.",
            "product": {"display_name": display, "category": "custom"},
            "artifact_types": [
                {"id": "request", "maps_to": "PRIM-ARTIFACT", "revision_model": "PRIM-REVISION", "normative": True, "approval_policy": "normative_change"},
                {"id": "result", "maps_to": "PRIM-ARTIFACT", "revision_model": "PRIM-REVISION", "normative": False},
            ],
            "trace_types": [
                {"id": "derived_from", "maps_to": "PRIM-TRACE", "strength": "HARD", "invalidates_on_upstream_supersede": True, "propagation_rule": "MARK_STALE"},
            ],
            "workunit_templates": [
                {
                    "id": "execute", "maps_to": "PRIM-WORKUNIT",
                    "inputs": [{"artifact_type": "request"}], "outputs": [{"artifact_type": "result"}],
                    "executor_role": "operator", "required_gate_types": ["request_ready"],
                    "evidence_required": ["execution_result"], "success_conditions": ["result_verified"],
                    "known_failure_modes": ["tool_timeout"], "retry_policy": {"max_attempts": 2, "retryable_failure_codes": ["tool_timeout"]},
                    "recovery_policy": {"mode": "AFFECTED_SUBGRAPH"}, "idempotency_semantics": "EXACT_PAYLOAD",
                    "resource_conflict_keys": [],
                }
            ],
            "evidence_types": [{"id": "execution_result", "maps_to": "PRIM-EVIDENCE", "trust_class": "AUTHORITATIVE"}],
            "gate_types": [
                {"id": "request_ready", "maps_to": "PRIM-GATE", "required_validity": {"inputs": "VALID"}, "allowed_trust_classes": ["AUTHORITATIVE", "SUPPORTED"]},
            ],
            "failure_types": [{"id": "tool_timeout", "maps_to": "PRIM-FAILURE", "default_decision": "RETRY", "retryable": True, "retry_budget": 1}],
            "recovery_policies": [{"failure_type": "tool_timeout", "maps_to": "PRIM-RECOVERY", "invalidation_mode": "AFFECTED_SUBGRAPH"}],
            "roles": [{"id": "operator", "maps_to": "PRIM-ACTOR"}, {"id": "approver", "maps_to": "PRIM-ACTOR"}],
            "authority_policies": [
                {"id": "operator-policy", "role": "operator", "maps_to": "PRIM-AUTHORITY", "allow": ["EXECUTE", "PROPOSE", "CREATE_REVISION"]},
                {"id": "approver-policy", "role": "approver", "maps_to": "PRIM-AUTHORITY", "allow": ["APPROVE", "CONFIRM", "PROPOSE", "CREATE_REVISION"]},
            ],
            "approval_policies": [
                {"id": "normative_change", "maps_to": "PRIM-APPROVAL", "requires_actor_type": "HUMAN", "requires_role": "approver", "prohibit_self_approval": True},
            ],
            "validity_rules": [],
            "loop_policy": {"maps_to": "PRIM-LOOPGUARD", "same_signature_limit": 2},
        }
        # The scaffold itself must be valid: this turns the template into an executable contract.
        report = cls.validate(data)
        if not report.ok:
            raise ValidationError("Internal scaffold template is invalid", details=report.to_dict())
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

    @classmethod
    def load(cls, source: str | Path) -> DomainPackage:
        report = cls.validate(source)
        if not report.ok:
            raise ValidationError("Domain package is invalid", details=report.to_dict())
        return load_domain(source)
