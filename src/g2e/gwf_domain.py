from __future__ import annotations

from copy import deepcopy

from gwr.domain import DomainPackage, validate_domain


G2E_GWF_DOMAIN_ID = "g2e.runtime"
G2E_GWF_DOMAIN_VERSION = "0.1.0"


# Static reviewed P4 contract. Dynamic ProofObligations are executed through one
# generic workunit; the adapter never generates trusted domain definitions at runtime.
G2E_GWF_DOMAIN_DATA = {
    "domain_id": G2E_GWF_DOMAIN_ID,
    "version": G2E_GWF_DOMAIN_VERSION,
    "compatible_runtime_versions": ["0.8.x"],
    "description": (
        "Base G2E runtime-mapping domain. GWF owns execution/governance/persistence "
        "only; canonical G2E semantics and verdicts remain G2E-owned."
    ),
    "product": {"display_name": "G2E Base Adapter", "category": "runtime"},
    "artifact_types": [
        {
            "id": "g2e_canonical_object",
            "maps_to": "PRIM-ARTIFACT",
            "revision_model": "PRIM-REVISION",
            "normative": False,
            "hard_dependencies": [],
            "required_fields": [
                "mapping_version",
                "schema_kind",
                "g2e_exact_ref",
                "canonical_object",
            ],
        }
    ],
    "trace_types": [
        {
            "id": "g2e_maps_to",
            "maps_to": "PRIM-TRACE",
            "strength": "INFORMATIONAL",
            "invalidates_on_upstream_supersede": False,
            "propagation_rule": "NONE",
        }
    ],
    "workunit_templates": [
        {
            "id": "g2e_execute_proof",
            "maps_to": "PRIM-WORKUNIT",
            "inputs": [{"artifact_type": "g2e_canonical_object"}],
            "outputs": [],
            "no_gate": True,
            "required_gate_types": [],
            "required_authorities": ["EXECUTE"],
            "execution_policy": {
                "semantic_authority": "G2E",
                "runtime_success_is_scientific_pass": False,
            },
            "evidence_required": ["g2e_candidate_evidence"],
            "success_conditions": ["runtime_terminal_state_recorded"],
            "known_failure_modes": ["g2e_executor_failure"],
            # One GWF run == one G2E ExecutionAttempt. Scientific replacement
            # attempts remain owned by the frozen G2E ProofRetryPolicy.
            "retry_policy": {"max_attempts": 1},
            "recovery_policy": {"mode": "G2E_FAIL_CLOSED"},
            "idempotency_semantics": "EXACT_PAYLOAD",
            "resource_conflict_keys": [],
        }
    ],
    "evidence_types": [
        {
            "id": "g2e_candidate_evidence",
            "maps_to": "PRIM-EVIDENCE",
            "trust_class": "AUTHORITATIVE",
        }
    ],
    "gate_types": [],
    "failure_types": [
        {
            "id": "g2e_executor_failure",
            "maps_to": "PRIM-FAILURE",
            "default_decision": "STOP",
            "retryable": False,
            "retry_budget": 0,
        }
    ],
    "recovery_policies": [
        {
            "failure_type": "g2e_executor_failure",
            "maps_to": "PRIM-RECOVERY",
            "invalidation_mode": "NONE",
        }
    ],
    "roles": [
        {"id": "system", "maps_to": "PRIM-ACTOR"},
        {"id": "g2e_operator", "maps_to": "PRIM-ACTOR"},
        {"id": "g2e_approver", "maps_to": "PRIM-ACTOR"},
    ],
    "authority_policies": [
        {
            "id": "g2e-system",
            "role": "system",
            "maps_to": "PRIM-AUTHORITY",
            "allow": ["CREATE_REVISION", "EXECUTE", "CANCEL", "PROPOSE", "APPROVE"],
        },
        {
            "id": "g2e-operator",
            "role": "g2e_operator",
            "maps_to": "PRIM-AUTHORITY",
            "allow": ["CREATE_REVISION", "EXECUTE", "CANCEL", "PROPOSE"],
        },
        {
            "id": "g2e-approver",
            "role": "g2e_approver",
            "maps_to": "PRIM-AUTHORITY",
            "allow": ["APPROVE", "PROPOSE", "CREATE_REVISION"],
        },
    ],
    "approval_policies": [],
    "loop_policy": {"maps_to": "PRIM-LOOPGUARD", "same_signature_limit": 1},
}


def g2e_gwf_domain() -> DomainPackage:
    """Return a fresh validated copy of the static P4 GWF domain contract."""
    data = deepcopy(G2E_GWF_DOMAIN_DATA)
    validate_domain(data)
    return DomainPackage(data)
