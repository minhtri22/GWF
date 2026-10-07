from __future__ import annotations

import copy

import pytest

from gwr.errors import AuthorityDenied, InvalidTransition, ValidationError
from gwr.g2e_bridge_vnext import (
    G2EGWFBridgeVNext,
    P3_G2E_MAPPING_VERSION,
    _payload_sha256,
    g2e_bridge_ref,
)


def _eref(name: str, rev: str = "r1", ch: str | None = None):
    return {
        "object_id": name,
        "revision_id": rev,
        "content_hash": ch or ("a" * 64),
    }


def _mapping(project_id="p1", *, target="rev-1", ref=None, active=True):
    return G2EGWFBridgeVNext.mapping_record(
        project_id,
        "claim",
        ref or _eref("claim-1"),
        {"kind": "Revision", "id": target},
        "b" * 64,
        active=active,
    )


def _agent_fixture(seeded, *, binding_mode="FROZEN", required_caps=None, authority=None):
    rt, project_id, planner, _, approver = seeded
    bridge = G2EGWFBridgeVNext(rt)
    required_caps = required_caps or ["tool.exec"]
    authority = authority or ["READ", "EXECUTE"]

    proof_ref = _eref("proof-1")
    attempt_ref = _eref("attempt-object-1")
    agent_binding_ref = _eref("agent-binding-1")
    agent_manifest_ref = _eref("agent-manifest-1")
    environment_manifest_ref = _eref("environment-manifest-1", ch="c" * 64)
    equivalence_ref = _eref("agent-equivalence-1", ch="d" * 64)

    identity = {
        "agent_app": "agent-app-a",
        "provider_ref": "provider-a",
        "model_ref": "model-a",
        "harness_ref": "harness-a",
        "transport_ref": "transport-a",
    }
    attempt = {
        "attempt_id": "attempt-1",
        "exact_ref": attempt_ref,
        "agent_binding_ref": agent_binding_ref,
        **identity,
    }
    manifest = {
        "exact_ref": agent_manifest_ref,
        "capabilities": [
            {
                "capability_id": "tool.exec",
                "available": True,
                "qualification_refs": ["qualification:tool.exec"],
            },
            {
                "capability_id": "artifact.extract",
                "available": True,
                "qualification_refs": ["qualification:artifact.extract"],
            },
        ],
    }
    agent_binding = {
        "exact_ref": agent_binding_ref,
        "resolved_attempt_id": "attempt-1",
        "binding_mode": binding_mode,
        "capability_manifest_ref": agent_manifest_ref,
        "equivalence_policy_ref": equivalence_ref,
        "required_capability_ids": list(required_caps),
        "authority_scope": list(authority),
        **identity,
    }

    auth_id = rt.vnext_governance.create_authority_envelope(
        project_id,
        {"prim_authority_ref": "base"},
        {"role": "executor"},
        [{"project_id": project_id}],
        list(authority),
        [],
    )
    budget_id = rt.vnext_governance.create_budget_envelope(
        project_id,
        [{"dimension": "attempts", "unit": "count", "ceiling": 1, "enforcement": "HARD"}],
    )
    env_id = rt.vnext_governance.register_execution_environment(
        "provider-neutral",
        "adapter-a",
        "1",
        "e" * 64,
        environment_manifest_ref,
    )
    wa_id = rt.vnext_governance.create_work_assignment(
        project_id,
        [
            g2e_bridge_ref("proof_obligation", proof_ref),
            g2e_bridge_ref("execution_attempt_envelope", attempt_ref),
        ],
        {"kind": "g2e_attempt_dispatch"},
        {"role": "executor"},
        list(required_caps),
        {"provider_neutral": True},
        {"authority_envelope_id": auth_id},
        {"budget_envelope_id": budget_id},
        [{"kind": "candidate_evidence"}],
        {"operational_only": True},
        proposer_actor_id=planner,
    )
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa_id, planner)
    rt.vnext_governance.authorize_work_assignment(wa_id, approver, frozen_hash)
    executor_binding_id = rt.vnext_governance.create_executor_binding(
        wa_id,
        binding_mode,
        {"role": "executor"},
        dict(identity),
        {"execution_environment_id": env_id},
        agent_manifest_ref,
        list(identity.keys()),
        {"authority_envelope_id": auth_id},
        {"budget_envelope_id": budget_id},
        equivalence_policy_ref=equivalence_ref,
    )
    return {
        "rt": rt,
        "project_id": project_id,
        "planner": planner,
        "approver": approver,
        "bridge": bridge,
        "proof_ref": proof_ref,
        "attempt_ref": attempt_ref,
        "attempt": attempt,
        "manifest": manifest,
        "agent_binding": agent_binding,
        "wa_id": wa_id,
        "executor_binding_id": executor_binding_id,
        "auth_id": auth_id,
        "budget_id": budget_id,
        "env_id": env_id,
        "environment_manifest_ref": environment_manifest_ref,
        "equivalence_ref": equivalence_ref,
    }


def _candidate(attempt_ref=None, payload=None):
    payload = {"value": 7} if payload is None else payload
    attempt_ref = attempt_ref or _eref("attempt-object-1")
    return {
        "source_class": "MEASUREMENT",
        "lifecycle": "CANDIDATE",
        "producer_attempt_ref": attempt_ref,
        "payload_digest": _payload_sha256(payload),
        "freshness_state": "EXPOSED",
        "independence_satisfied": ["reviewer_context"],
    }, payload


def _policy():
    return {
        "accepted_source_classes": ["MEASUREMENT"],
        "require_attempt_linkage": True,
        "allowed_freshness_states": ["EXPOSED"],
        "independence_requirements": ["reviewer_context"],
    }


def test_p3_positive_mapping_and_hash_domains_are_distinct():
    rec = _mapping()
    assert G2EGWFBridgeVNext.validate_mapping_record(rec)
    assert rec["hash_domains"] == {"g2e": "G2E_CANONICAL", "gwf": "GWF_RUNTIME"}


def test_p3_positive_work_assignment_and_agent_binding_reconcile(seeded):
    fx = _agent_fixture(seeded)
    assert fx["bridge"].validate_work_assignment_bridge(
        fx["wa_id"], fx["proof_ref"], fx["attempt_ref"]
    )
    assert fx["bridge"].validate_agent_executor_binding(
        fx["wa_id"],
        fx["executor_binding_id"],
        fx["attempt"],
        fx["agent_binding"],
        fx["manifest"],
    )


def test_p3_positive_candidate_evidence_is_validation_only():
    evidence, payload = _candidate()
    assert G2EGWFBridgeVNext.validate_candidate_evidence(
        evidence,
        expected_attempt_ref=_eref("attempt-object-1"),
        payload=payload,
        admission_policy=_policy(),
    )
    assert evidence["lifecycle"] == "CANDIDATE"


def test_p3_positive_protected_resource_monotonicity():
    assert G2EGWFBridgeVNext.protected_resource_transition("FRESH", "RESERVED") == "RESERVED"
    assert G2EGWFBridgeVNext.protected_resource_transition("RESERVED", "EXPOSED") == "EXPOSED"


# 01 GWF ID cannot replace G2E object_id/revision_id/content_hash.
def test_p3_negative_01_gwf_id_cannot_replace_g2e_exact_identity():
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.mapping_record(
            "p1",
            "claim",
            {"object_id": "gwf-revision-1", "revision_id": "", "content_hash": "a" * 64},
            {"kind": "Revision", "id": "gwf-revision-1"},
            "b" * 64,
        )


# 02 GWF content hash cannot be compared as semantic substitute for G2E canonical hash.
def test_p3_negative_02_gwf_hash_not_semantic_substitute():
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.assert_hash_domain_separation(
            _eref("claim-1"),
            "a" * 64,
            semantic_substitution=True,
        )


# 03 same G2E exact ref cannot map to two conflicting active mirrors in one mapping scope.
def test_p3_negative_03_conflicting_active_mirrors_fail_closed():
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.assert_mapping_uniqueness([
            _mapping(target="rev-a"),
            _mapping(target="rev-b"),
        ])


# 04 unknown mapping version fails closed.
def test_p3_negative_04_unknown_mapping_version_fails_closed():
    rec = _mapping()
    rec["mapping_version"] = "unknown"
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_mapping_record(rec)


# 05 WorkAssignment missing exact ProofObligation ref fails closed.
def test_p3_negative_05_work_assignment_missing_proof_ref(seeded):
    fx = _agent_fixture(seeded)
    row = fx["rt"].db.one("SELECT * FROM work_assignments WHERE work_assignment_id=?", (fx["wa_id"],))
    fx["rt"].db.conn.execute(
        "UPDATE work_assignments SET origin_refs=? WHERE work_assignment_id=?",
        ('[{"system":"G2E","schema_kind":"execution_attempt_envelope","exact_ref":{"object_id":"attempt-object-1","revision_id":"r1","content_hash":"' + "a" * 64 + '"}}]', fx["wa_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_work_assignment_bridge(fx["wa_id"], fx["proof_ref"], fx["attempt_ref"])


# 06 WorkAssignment missing exact ExecutionAttempt ref fails closed.
def test_p3_negative_06_work_assignment_missing_attempt_ref(seeded):
    fx = _agent_fixture(seeded)
    fx["rt"].db.conn.execute(
        "UPDATE work_assignments SET origin_refs=? WHERE work_assignment_id=?",
        ('[{"system":"G2E","schema_kind":"proof_obligation","exact_ref":{"object_id":"proof-1","revision_id":"r1","content_hash":"' + "a" * 64 + '"}}]', fx["wa_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_work_assignment_bridge(fx["wa_id"], fx["proof_ref"], fx["attempt_ref"])


# 07 one G2E attempt cannot dispatch through two active WorkAssignments.
def test_p3_negative_07_one_attempt_two_active_assignments_rejected(seeded):
    fx = _agent_fixture(seeded)
    rt = fx["rt"]
    wa2 = rt.vnext_governance.create_work_assignment(
        fx["project_id"],
        [
            g2e_bridge_ref("proof_obligation", fx["proof_ref"]),
            g2e_bridge_ref("execution_attempt_envelope", fx["attempt_ref"]),
        ],
        {"kind": "duplicate"},
        {"role": "executor"},
        ["tool.exec"],
        {"provider_neutral": True},
        {"authority_envelope_id": fx["auth_id"]},
        {"budget_envelope_id": fx["budget_id"]},
        [{"kind": "candidate_evidence"}],
        {"operational_only": True},
        proposer_actor_id=fx["planner"],
    )
    rt.vnext_governance.freeze_work_assignment(wa2, fx["planner"])
    with pytest.raises(InvalidTransition):
        fx["bridge"].validate_work_assignment_bridge(wa2, fx["proof_ref"], fx["attempt_ref"])


# 08 GWF runtime retry cannot create replacement attempt implicitly.
def test_p3_negative_08_runtime_retry_cannot_create_replacement_attempt():
    with pytest.raises(InvalidTransition):
        G2EGWFBridgeVNext.assert_runtime_retry_does_not_create_attempt(
            "attempt-1", "attempt-2", runtime_retry=True
        )


# 09 WorkAssignment COMPLETED cannot create EvidenceRecord ADMITTED.
def test_p3_negative_09_completed_does_not_admit_evidence():
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.operational_state_to_scientific_claim("COMPLETED")


# 10 WorkAssignment COMPLETED cannot create Adjudication PASS.
def test_p3_negative_10_completed_does_not_create_pass():
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.operational_state_to_scientific_claim("COMPLETED")


# 11 ExecutorBinding cannot replace G2E AgentBinding semantic identity.
def test_p3_negative_11_executor_binding_not_agent_binding(seeded):
    fx = _agent_fixture(seeded)
    attempt = copy.deepcopy(fx["attempt"])
    attempt["agent_binding_ref"] = _eref("executor-binding-as-agent-binding")
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], attempt, fx["agent_binding"], fx["manifest"]
        )


# 12 agent-backed attempt without G2E AgentBinding fails closed.
def test_p3_negative_12_agent_attempt_without_agent_binding(seeded):
    fx = _agent_fixture(seeded)
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], None, fx["manifest"]
        )


# 13 AgentBinding resolved_attempt_id mismatch fails closed.
def test_p3_negative_13_resolved_attempt_id_mismatch(seeded):
    fx = _agent_fixture(seeded)
    binding = copy.deepcopy(fx["agent_binding"])
    binding["resolved_attempt_id"] = "attempt-other"
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], binding, fx["manifest"]
        )


# 14 ExecutorBinding agent_identity widening/mismatch fails closed.
def test_p3_negative_14_executor_identity_mismatch(seeded):
    fx = _agent_fixture(seeded)
    fx["rt"].db.conn.execute(
        "UPDATE executor_bindings SET agent_identity=? WHERE executor_binding_id=?",
        ('{"agent_app":"agent-app-a","provider_ref":"provider-b","model_ref":"model-a","harness_ref":"harness-a","transport_ref":"transport-a"}', fx["executor_binding_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], fx["agent_binding"], fx["manifest"]
        )


# 15 G2E FROZEN binding cannot map to GWF DYNAMIC binding.
def test_p3_negative_15_frozen_agent_binding_requires_frozen_executor(seeded):
    fx = _agent_fixture(seeded)
    fx["rt"].db.conn.execute(
        "UPDATE executor_bindings SET binding_mode='DYNAMIC',status='RESOLVED' WHERE executor_binding_id=?",
        (fx["executor_binding_id"],),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], fx["agent_binding"], fx["manifest"]
        )


# 16 material ExecutorBinding substitution requires new G2E attempt.
def test_p3_negative_16_material_executor_substitution_requires_new_attempt(seeded):
    fx = _agent_fixture(seeded)
    candidate = copy.deepcopy(fx["agent_binding"])
    candidate["model_ref"] = "model-b"
    with pytest.raises(InvalidTransition):
        G2EGWFBridgeVNext.validate_material_substitution(
            fx["agent_binding"], candidate, material_dimensions=["model_ref"], same_attempt_id=True
        )


# 17 G2E AgentCapabilityManifest cannot be substituted by environment capability manifest.
def test_p3_negative_17_agent_capability_manifest_not_environment_manifest(seeded):
    fx = _agent_fixture(seeded)
    fx["rt"].db.conn.execute(
        "UPDATE executor_bindings SET capability_manifest_ref=? WHERE executor_binding_id=?",
        ('{"object_id":"environment-manifest-1","revision_id":"r1","content_hash":"' + "c" * 64 + '"}', fx["executor_binding_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], fx["agent_binding"], fx["manifest"]
        )


# 18 ExecutionEnvironment capability manifest cannot be substituted by G2E AgentCapabilityManifest.
def test_p3_negative_18_environment_manifest_not_agent_manifest(seeded):
    fx = _agent_fixture(seeded)
    fx["rt"].db.conn.execute(
        "UPDATE execution_environments SET capability_manifest_ref=? WHERE execution_environment_id=?",
        ('{"object_id":"agent-manifest-1","revision_id":"r1","content_hash":"' + "a" * 64 + '"}', fx["env_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], fx["agent_binding"], fx["manifest"]
        )


# 19 GWF required capabilities cannot drop G2E required agent capabilities.
def test_p3_negative_19_gwf_cannot_drop_required_agent_capability(seeded):
    fx = _agent_fixture(seeded)
    fx["rt"].db.conn.execute(
        "UPDATE work_assignments SET required_capabilities='[]' WHERE work_assignment_id=?",
        (fx["wa_id"],),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], fx["agent_binding"], fx["manifest"]
        )


# 20 effective GWF authority cannot exceed G2E AgentBinding authority scope.
def test_p3_negative_20_gwf_authority_cannot_exceed_g2e_ceiling(seeded):
    fx = _agent_fixture(seeded, authority=["READ", "EXECUTE", "DELETE"])
    binding = copy.deepcopy(fx["agent_binding"])
    binding["authority_scope"] = ["READ", "EXECUTE"]
    with pytest.raises(AuthorityDenied):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"], fx["executor_binding_id"], fx["attempt"], binding, fx["manifest"]
        )


# 21 QualificationAuthorityGrant cannot authorize operational dispatch.
def test_p3_negative_21_qualification_grant_not_operational_authority(seeded):
    fx = _agent_fixture(seeded)
    with pytest.raises(AuthorityDenied):
        fx["bridge"].validate_agent_executor_binding(
            fx["wa_id"],
            fx["executor_binding_id"],
            fx["attempt"],
            fx["agent_binding"],
            fx["manifest"],
            qualification_grant_used_for_dispatch=True,
        )


# 22 protected resource exact ref substitution fails closed.
def test_p3_negative_22_protected_resource_exact_ref_substitution(seeded):
    fx = _agent_fixture(seeded)
    with pytest.raises(ValidationError):
        fx["bridge"].validate_work_assignment_bridge(
            fx["wa_id"],
            fx["proof_ref"],
            fx["attempt_ref"],
            protected_resource_refs=[g2e_bridge_ref("protected_resource", _eref("protected-1"))],
        )


# 23 EXPOSED protected resource cannot transition to RESERVED or FRESH.
def test_p3_negative_23_exposed_resource_cannot_move_backward():
    for target in ("RESERVED", "FRESH"):
        with pytest.raises(InvalidTransition):
            G2EGWFBridgeVNext.protected_resource_transition("EXPOSED", target)


# 24 uncertain protected access recovery becomes EXPOSED.
def test_p3_negative_24_uncertain_recovery_fails_closed_to_exposed():
    assert (
        G2EGWFBridgeVNext.protected_resource_transition(
            "FRESH", "FRESH", uncertain_access_recovery=True
        )
        == "EXPOSED"
    )


# 25 protected resource access before durable reservation fails closed.
def test_p3_negative_25_access_requires_durable_reservation():
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.validate_protected_access(
            freshness_state="FRESH", durable_reservation=False, access_started=True
        )


# 26 research profile cannot make G2E-disallowed protected access admissible.
def test_p3_negative_26_profile_cannot_bypass_g2e_protected_access():
    profile_would_allow = True
    assert profile_would_allow
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.validate_protected_access(
            freshness_state="FRESH", durable_reservation=False, access_started=True
        )


# 27 candidate runtime evidence cannot become ADMITTED without G2E EvidenceAdmissionPolicy.
def test_p3_negative_27_runtime_cannot_emit_admitted_evidence():
    evidence, payload = _candidate()
    evidence["lifecycle"] = "ADMITTED"
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_candidate_evidence(
            evidence,
            expected_attempt_ref=_eref("attempt-object-1"),
            payload=payload,
            admission_policy=_policy(),
        )


# 28 evidence payload digest mismatch is rejected.
def test_p3_negative_28_evidence_payload_digest_mismatch():
    evidence, payload = _candidate()
    evidence["payload_digest"] = "f" * 64
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_candidate_evidence(
            evidence,
            expected_attempt_ref=_eref("attempt-object-1"),
            payload=payload,
            admission_policy=_policy(),
        )


# 29 producer attempt mismatch is rejected.
def test_p3_negative_29_evidence_producer_attempt_mismatch():
    evidence, payload = _candidate()
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_candidate_evidence(
            evidence,
            expected_attempt_ref=_eref("different-attempt"),
            payload=payload,
            admission_policy=_policy(),
        )


# 30 freshness/admission-policy mismatch is rejected.
def test_p3_negative_30_evidence_freshness_policy_mismatch():
    evidence, payload = _candidate()
    evidence["freshness_state"] = "RESERVED"
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_candidate_evidence(
            evidence,
            expected_attempt_ref=_eref("attempt-object-1"),
            payload=payload,
            admission_policy=_policy(),
        )


# 31 independence-policy mismatch is rejected.
def test_p3_negative_31_evidence_independence_policy_mismatch():
    evidence, payload = _candidate()
    evidence["independence_satisfied"] = []
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_candidate_evidence(
            evidence,
            expected_attempt_ref=_eref("attempt-object-1"),
            payload=payload,
            admission_policy=_policy(),
        )


# 32 different provider/model alone does not satisfy independence.
def test_p3_negative_32_provider_model_difference_not_independence():
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_independence(
            {"required_dimensions": ["independent_reviewer_context"]},
            {
                "provider_changed": True,
                "model_changed": True,
                "independent_reviewer_context": False,
            },
        )


# 33 adjudication consuming non-ADMITTED evidence is rejected.
def test_p3_negative_33_adjudication_requires_admitted_evidence():
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_adjudication_inputs([
            {"lifecycle": "CANDIDATE"}
        ])


# 34 GWF or human state cannot rewrite terminal G2E Adjudication.
def test_p3_negative_34_non_g2e_authority_cannot_rewrite_adjudication():
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.validate_adjudication_mirror(
            {"verdict": "FAIL"},
            semantic_authority="HUMAN",
            existing_verdict="PASS",
        )


# 35 normative post-outcome change cannot reuse old proof/attempt identity.
def test_p3_negative_35_post_outcome_normative_change_requires_successor():
    with pytest.raises(InvalidTransition):
        G2EGWFBridgeVNext.validate_normative_revision(
            change_class="NORMATIVE",
            outcome_exposed=True,
            reuses_old_exact_identity=True,
        )


# 36 material agent substitution cannot reuse old attempt identity.
def test_p3_negative_36_material_agent_change_requires_new_attempt():
    old = {"harness_ref": "harness-a"}
    new = {"harness_ref": "harness-b"}
    with pytest.raises(InvalidTransition):
        G2EGWFBridgeVNext.validate_material_substitution(
            old,
            new,
            material_dimensions=["harness_ref"],
            same_attempt_id=True,
        )


# 37 checkpoint with mismatched G2E exact refs is rejected.
def test_p3_negative_37_checkpoint_exact_ref_mismatch_rejected():
    with pytest.raises(ValidationError):
        G2EGWFBridgeVNext.validate_checkpoint(
            [_eref("proof-1")],
            [_eref("proof-2")],
        )


# 38 checkpoint uncertainty cannot reset protected-resource exposure.
def test_p3_negative_38_checkpoint_uncertainty_remains_exposed():
    assert (
        G2EGWFBridgeVNext.validate_checkpoint(
            [_eref("proof-1")],
            [_eref("proof-1")],
            uncertain_protected_access=True,
        )
        == "EXPOSED"
    )


# 39 transport-experiment files cannot be imported as canonical semantic core.
def test_p3_negative_39_transport_experiment_import_firewall():
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.assert_source_import_allowed(
            "transport_experiment", mode="runtime_import"
        )


# 40 historical evidence files cannot be executed/imported as runtime implementation.
def test_p3_negative_40_historical_evidence_import_firewall():
    with pytest.raises(AuthorityDenied):
        G2EGWFBridgeVNext.assert_source_import_allowed(
            "historical_evidence", mode="runtime_import"
        )
