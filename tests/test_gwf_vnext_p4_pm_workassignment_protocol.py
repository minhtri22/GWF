from __future__ import annotations

import pytest

from gwr.errors import AuthorityDenied, InvalidTransition, ValidationError
from gwr.g2e_bridge_vnext import G2EGWFBridgeVNext
from gwr.pm_workassignment_vnext import PMWorkAssignmentProtocolVNext


def _exact(name: str, rev: str = "r1", ch: str | None = None):
    return {"object_id": name, "revision_id": rev, "content_hash": ch or ("a" * 64)}


def _authority(rt, project_id):
    return rt.vnext_governance.create_authority_envelope(
        project_id,
        {"prim_authority_ref": "base"},
        {"role": "pm-materializer"},
        [{"project_id": project_id}],
        ["READ", "PROPOSE", "EXECUTE"],
        [],
    )


def _budget(rt, project_id):
    return rt.vnext_governance.create_budget_envelope(
        project_id,
        [{"dimension": "attempts", "unit": "count", "ceiling": 2, "enforcement": "HARD"}],
    )


def _snapshot(svc, project_id, auth_id, budget_id, *, revision="s1", allowed=("repo.read",), protected=(), resolved_har=()):
    return svc.create_governed_state_snapshot(
        project_id,
        revision,
        governance_profile_ref={"domain_id": "zero", "profile_id": "development", "profile_version": "1", "profile_hash": "b" * 64},
        authority_envelope_ref={"authority_envelope_id": auth_id},
        budget_envelope_ref={"budget_envelope_id": budget_id},
        g2e_goal_refs=[_exact("goal-1")],
        g2e_claim_refs=[_exact("claim-1")],
        g2e_proof_obligation_refs=[_exact("proof-1")],
        g2e_execution_attempt_refs=[_exact("attempt-1")],
        active_work_assignment_refs=[],
        human_action_request_refs=[],
        resolved_human_action_refs=list(resolved_har),
        protected_resource_metadata=list(protected),
        allowed_capabilities=list(allowed),
        policy_digest="c" * 64,
    )


def _role(svc, project_id, auth_id, budget_id, *, role="WORKER", caps=("repo.read",), independence=None):
    return svc.create_role_request(
        project_id,
        role,
        source_obligation_ref=_exact("proof-1"),
        required_capabilities=list(caps),
        authority_ceiling_ref={"authority_envelope_id": auth_id},
        budget_ceiling_ref={"budget_envelope_id": budget_id},
        execution_environment_class_request="provider-neutral-zero",
        expected_outputs=[{"kind": "candidate-output"}],
        independence_requirements=independence,
    )


def _proposal(
    svc,
    project_id,
    snapshot_id,
    role_id,
    auth_id,
    budget_id,
    *,
    proposal_id=None,
    revision_id="r1",
    caps=("repo.read",),
    protected=(),
    required_har=(),
):
    return svc.create_work_assignment_proposal(
        project_id,
        snapshot_id,
        role_id,
        proposal_id=proposal_id,
        revision_id=revision_id,
        source_goal_ref=_exact("goal-1"),
        source_claim_ref=_exact("claim-1"),
        source_proof_obligation_ref=_exact("proof-1"),
        source_execution_attempt_ref=_exact("attempt-1"),
        objective={"kind": "zero-provider-p4"},
        requested_execution_environment_class="provider-neutral-zero",
        requested_capabilities=list(caps),
        requested_authority_scope={
            "allow_actions": ["READ"],
            "resource_selectors": [{"project_id": project_id}],
        },
        requested_budget=[{"dimension": "attempts", "amount": 1}],
        authority_envelope_ref={"authority_envelope_id": auth_id},
        budget_envelope_ref={"budget_envelope_id": budget_id},
        protected_resource_constraints=list(protected),
        required_human_action_refs=list(required_har),
        expected_outputs=[{"kind": "candidate-output"}],
        handoff_contract={"required": ["candidate-output"], "operational_only": True},
    )


def _submitted(seeded, *, caps=("repo.read",), allowed=("repo.read",), protected=(), required_har=(), resolved_har=(), role="WORKER", independence=None):
    rt, project_id, planner, _, approver = seeded
    svc = PMWorkAssignmentProtocolVNext(rt.db, rt.vnext_governance)
    auth_id = _authority(rt, project_id)
    budget_id = _budget(rt, project_id)
    snapshot_id = _snapshot(
        svc,
        project_id,
        auth_id,
        budget_id,
        allowed=allowed,
        resolved_har=resolved_har,
    )
    role_id = _role(
        svc,
        project_id,
        auth_id,
        budget_id,
        role=role,
        caps=caps,
        independence=independence,
    )
    proposal_id, proposal_hash = _proposal(
        svc,
        project_id,
        snapshot_id,
        role_id,
        auth_id,
        budget_id,
        caps=caps,
        protected=protected,
        required_har=required_har,
    )
    frozen = svc.freeze_proposal(proposal_id, "r1")
    assert frozen == proposal_hash
    svc.submit_proposal(proposal_id, "r1", frozen)
    return {
        "rt": rt,
        "project_id": project_id,
        "planner": planner,
        "approver": approver,
        "svc": svc,
        "auth_id": auth_id,
        "budget_id": budget_id,
        "snapshot_id": snapshot_id,
        "role_id": role_id,
        "proposal_id": proposal_id,
        "proposal_hash": proposal_hash,
    }


def _authorized_assignment(fx, *, current_revision="s1", protected_access_authorized=False):
    svc = fx["svc"]
    rt = fx["rt"]
    payload = svc.materialization_payload(
        fx["proposal_id"],
        "r1",
        current_state_revision=current_revision,
        protected_access_authorized=protected_access_authorized,
    )
    wa = rt.vnext_governance.create_work_assignment(
        payload["project_id"],
        payload["origin_refs"],
        payload["objective"],
        payload["agent_role_ref"],
        payload["required_capabilities"],
        payload["execution_environment_constraints"],
        payload["authority_envelope_ref"],
        payload["budget_envelope_ref"],
        payload["expected_outputs"],
        payload["completion_contract"],
        protected_resource_constraints=payload["protected_resource_constraints"],
        independence_requirements=payload["independence_requirements"],
        proposer_actor_id=fx["planner"],
    )
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, fx["planner"])
    rt.vnext_governance.authorize_work_assignment(wa, fx["approver"], frozen_hash)
    return wa


def test_p4_positive_proposal_materialization_roundtrip(seeded):
    fx = _submitted(seeded)
    wa = _authorized_assignment(fx)
    fx["svc"].record_materialization(
        fx["proposal_id"], "r1", wa, current_state_revision="s1"
    )
    row = fx["rt"].db.one(
        "SELECT state,materialized_work_assignment_id FROM pm_work_assignment_proposals "
        "WHERE proposal_id=? AND revision_id='r1'",
        (fx["proposal_id"],),
    )
    assert row["state"] == "AUTHORIZED_MATERIALIZED"
    assert row["materialized_work_assignment_id"] == wa


def test_p4_positive_plan_and_handoff_are_content_bound(seeded):
    fx = _submitted(seeded)
    plan_hash = fx["svc"].create_plan_revision(
        "plan-1",
        "r1",
        fx["snapshot_id"],
        objective_summary={"objective": "bounded"},
        dependency_refs=[_exact("proof-1")],
        proposal_refs=[{"proposal_id": fx["proposal_id"], "revision_id": "r1", "content_hash": fx["proposal_hash"]}],
        created_by_pm_identity_ref={"role": "PM", "identity": "provider-neutral"},
    )
    assert len(plan_hash) == 64
    hid, hh = fx["svc"].create_handoff_record(
        fx["project_id"],
        "r1",
        fx["snapshot_id"],
        current_state_revision="s1",
        pm_plan_ref={"plan_id": "plan-1", "revision_id": "r1", "content_hash": plan_hash},
        proposal_refs=[{"proposal_id": fx["proposal_id"], "revision_id": "r1", "content_hash": fx["proposal_hash"]}],
        unresolved_human_action_refs=[],
        active_work_assignment_refs=[],
        next_allowed_action="WAIT_FOR_GWF_AUTHORIZATION",
    )
    assert hid.startswith("pmhandoff_")
    assert len(hh) == 64


def _forbidden(seeded, action):
    svc = PMWorkAssignmentProtocolVNext(seeded[0].db, seeded[0].vnext_governance)
    with pytest.raises(AuthorityDenied):
        svc.assert_pm_action_allowed(action)


def test_p4_negative_01_pm_cannot_create_authority(seeded):
    _forbidden(seeded, "CREATE_AUTHORITY")


def test_p4_negative_02_pm_cannot_expand_authority(seeded):
    _forbidden(seeded, "EXPAND_AUTHORITY")


def test_p4_negative_03_pm_cannot_expand_budget(seeded):
    _forbidden(seeded, "EXPAND_BUDGET")


def test_p4_negative_04_pm_cannot_expose_protected_resource_payload(seeded):
    rt, project_id, *_ = seeded
    svc = PMWorkAssignmentProtocolVNext(rt.db, rt.vnext_governance)
    auth_id = _authority(rt, project_id)
    budget_id = _budget(rt, project_id)
    with pytest.raises(ValidationError):
        _snapshot(
            svc,
            project_id,
            auth_id,
            budget_id,
            protected=[{"resource_id": "fresh-test", "payload": {"hidden": True}}],
        )


def test_p4_negative_05_pm_cannot_consume_protected_resource(seeded):
    _forbidden(seeded, "CONSUME_PROTECTED_RESOURCE")


def test_p4_negative_06_pm_cannot_direct_dispatch_executor(seeded):
    _forbidden(seeded, "DIRECT_DISPATCH_EXECUTOR")


def test_p4_negative_07_pm_cannot_create_scientific_verdict(seeded):
    _forbidden(seeded, "CREATE_SCIENTIFIC_VERDICT")


def test_p4_negative_08_pm_cannot_admit_evidence(seeded):
    _forbidden(seeded, "ADMIT_EVIDENCE")


def test_p4_negative_09_pm_cannot_create_release_acceptance(seeded):
    _forbidden(seeded, "CREATE_RELEASE_ACCEPTANCE")


def test_p4_negative_10_pm_cannot_override_g2e_agent_binding(seeded):
    _forbidden(seeded, "OVERRIDE_G2E_AGENT_BINDING")


def test_p4_negative_11_pm_cannot_override_gwf_executor_binding(seeded):
    _forbidden(seeded, "OVERRIDE_GWF_EXECUTOR_BINDING")


def test_p4_negative_12_pm_cannot_mutate_frozen_work_assignment(seeded):
    _forbidden(seeded, "MUTATE_FROZEN_WORK_ASSIGNMENT")


def test_p4_negative_13_pm_cannot_mutate_frozen_proof_obligation(seeded):
    _forbidden(seeded, "MUTATE_FROZEN_PROOF_OBLIGATION")


def test_p4_negative_14_pm_cannot_mutate_governance_profile(seeded):
    _forbidden(seeded, "MUTATE_FROZEN_GOVERNANCE_PROFILE")


def test_p4_negative_15_pm_cannot_downgrade_profile_to_escape(seeded):
    _forbidden(seeded, "DOWNGRADE_PROFILE_TO_ESCAPE")


def test_p4_negative_16_pm_cannot_reinterpret_terminal_lineage(seeded):
    _forbidden(seeded, "REINTERPRET_TERMINAL_LINEAGE")


def test_p4_negative_17_stale_proposal_rejected_after_material_state_revision(seeded):
    fx = _submitted(seeded)
    with pytest.raises(InvalidTransition):
        fx["svc"].materialization_payload(
            fx["proposal_id"], "r1", current_state_revision="s2"
        )


def test_p4_negative_18_pm_cannot_silently_substitute_worker_role(seeded):
    fx = _submitted(seeded)
    replacement = _role(
        fx["svc"], fx["project_id"], fx["auth_id"], fx["budget_id"], role="WORKER"
    )
    fx["rt"].db.conn.execute(
        "UPDATE pm_work_assignment_proposals SET role_request_id=? WHERE proposal_id=? AND revision_id='r1'",
        (replacement, fx["proposal_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["svc"].validate_proposal_integrity(fx["proposal_id"], "r1")


def test_p4_negative_19_pm_cannot_silently_substitute_qa_role(seeded):
    fx = _submitted(
        seeded,
        role="QA_REVIEWER",
        independence={"required_dimensions": ["separate_context"]},
    )
    replacement = _role(
        fx["svc"],
        fx["project_id"],
        fx["auth_id"],
        fx["budget_id"],
        role="QA_REVIEWER",
        independence={"required_dimensions": ["source_blind"]},
    )
    fx["rt"].db.conn.execute(
        "UPDATE pm_work_assignment_proposals SET role_request_id=? WHERE proposal_id=? AND revision_id='r1'",
        (replacement, fx["proposal_id"]),
    )
    fx["rt"].db.conn.commit()
    with pytest.raises(ValidationError):
        fx["svc"].validate_proposal_integrity(fx["proposal_id"], "r1")


def test_p4_negative_20_provider_difference_does_not_prove_independence(seeded):
    rt, project_id, *_ = seeded
    svc = PMWorkAssignmentProtocolVNext(rt.db, rt.vnext_governance)
    auth_id = _authority(rt, project_id)
    budget_id = _budget(rt, project_id)
    with pytest.raises(ValidationError):
        _role(
            svc,
            project_id,
            auth_id,
            budget_id,
            role="QA_REVIEWER",
            independence={"provider_difference": True, "model_difference": True},
        )


def test_p4_negative_21_operational_completion_not_scientific_evidence(seeded):
    _forbidden(seeded, "TREAT_OPERATIONAL_COMPLETION_AS_EVIDENCE")


def test_p4_negative_22_pm_cannot_bypass_human_action_request(seeded):
    _forbidden(seeded, "BYPASS_HUMAN_ACTION_REQUEST")


def test_p4_negative_23_pm_cannot_self_resolve_human_action_request(seeded):
    _forbidden(seeded, "SELF_RESOLVE_HUMAN_ACTION_REQUEST")


def test_p4_negative_24_proposal_cannot_materialize_without_gwf_authorization(seeded):
    fx = _submitted(seeded)
    payload = fx["svc"].materialization_payload(
        fx["proposal_id"], "r1", current_state_revision="s1"
    )
    wa = fx["rt"].vnext_governance.create_work_assignment(
        payload["project_id"],
        payload["origin_refs"],
        payload["objective"],
        payload["agent_role_ref"],
        payload["required_capabilities"],
        payload["execution_environment_constraints"],
        payload["authority_envelope_ref"],
        payload["budget_envelope_ref"],
        payload["expected_outputs"],
        payload["completion_contract"],
        protected_resource_constraints=payload["protected_resource_constraints"],
        independence_requirements=payload["independence_requirements"],
        proposer_actor_id=fx["planner"],
    )
    with pytest.raises(AuthorityDenied):
        fx["svc"].record_materialization(
            fx["proposal_id"], "r1", wa, current_state_revision="s1"
        )


def test_p4_negative_25_duplicate_active_work_assignment_for_same_attempt_rejected(seeded):
    fx = _submitted(seeded)
    rt = fx["rt"]
    payload = fx["svc"].materialization_payload(
        fx["proposal_id"], "r1", current_state_revision="s1"
    )
    wa1 = rt.vnext_governance.create_work_assignment(
        payload["project_id"], payload["origin_refs"], payload["objective"], payload["agent_role_ref"],
        payload["required_capabilities"], payload["execution_environment_constraints"],
        payload["authority_envelope_ref"], payload["budget_envelope_ref"],
        payload["expected_outputs"], payload["completion_contract"],
        proposer_actor_id=fx["planner"],
    )
    rt.vnext_governance.freeze_work_assignment(wa1, fx["planner"])
    wa2 = rt.vnext_governance.create_work_assignment(
        payload["project_id"], payload["origin_refs"], {"duplicate": True}, payload["agent_role_ref"],
        payload["required_capabilities"], payload["execution_environment_constraints"],
        payload["authority_envelope_ref"], payload["budget_envelope_ref"],
        payload["expected_outputs"], payload["completion_contract"],
        proposer_actor_id=fx["planner"],
    )
    rt.vnext_governance.freeze_work_assignment(wa2, fx["planner"])
    bridge = G2EGWFBridgeVNext(rt)
    with pytest.raises(InvalidTransition):
        bridge.validate_work_assignment_bridge(wa2, _exact("proof-1"), _exact("attempt-1"))


def test_p4_negative_26_handoff_cannot_change_proposal_identity_silently(seeded):
    fx = _submitted(seeded)
    with pytest.raises(ValidationError):
        fx["svc"].create_handoff_record(
            fx["project_id"],
            "r1",
            fx["snapshot_id"],
            current_state_revision="s1",
            pm_plan_ref={"plan_id": "p", "revision_id": "r1", "content_hash": "d" * 64},
            proposal_refs=[{"proposal_id": fx["proposal_id"], "revision_id": "r1", "content_hash": "0" * 64}],
            unresolved_human_action_refs=[],
            active_work_assignment_refs=[],
            next_allowed_action="WAIT",
        )


def test_p4_negative_27_recovery_must_bind_current_governed_state_revision(seeded):
    fx = _submitted(seeded)
    with pytest.raises(InvalidTransition):
        fx["svc"].create_handoff_record(
            fx["project_id"],
            "r1",
            fx["snapshot_id"],
            current_state_revision="s2",
            pm_plan_ref={"plan_id": "p", "revision_id": "r1", "content_hash": "d" * 64},
            proposal_refs=[{"proposal_id": fx["proposal_id"], "revision_id": "r1", "content_hash": fx["proposal_hash"]}],
            unresolved_human_action_refs=[],
            active_work_assignment_refs=[],
            next_allowed_action="WAIT",
        )


def test_p4_negative_28_pm_cannot_request_capability_beyond_active_profile(seeded):
    fx = _submitted(seeded, caps=("repo.read", "repo.write"), allowed=("repo.read",))
    with pytest.raises(AuthorityDenied):
        fx["svc"].materialization_payload(
            fx["proposal_id"], "r1", current_state_revision="s1"
        )


def test_p4_negative_29_pm_cannot_request_protected_access_before_authorization(seeded):
    fx = _submitted(
        seeded,
        protected=({"resource_id": "fresh-test", "mode": "READ"},),
    )
    with pytest.raises(AuthorityDenied):
        fx["svc"].materialization_payload(
            fx["proposal_id"], "r1", current_state_revision="s1"
        )


def test_p4_negative_30_pm_cannot_elevate_exploratory_finding_to_confirmatory_proof(seeded):
    _forbidden(seeded, "ELEVATE_EXPLORATORY_TO_CONFIRMATORY")


def test_p4_negative_31_pm_cannot_change_frozen_threshold_metric_seed(seeded):
    _forbidden(seeded, "CHANGE_FROZEN_THRESHOLD_METRIC_SEED")


def test_p4_negative_32_ui_browser_state_cannot_act_as_pm_authority(seeded):
    _forbidden(seeded, "USE_UI_STATE_AS_AUTHORITY")


def test_p4_negative_33_pm_cannot_redefine_work_assignment_ownership(seeded):
    _forbidden(seeded, "REDEFINE_WORK_ASSIGNMENT")


def test_p4_negative_34_pm_cannot_create_replacement_g2e_attempt(seeded):
    _forbidden(seeded, "CREATE_REPLACEMENT_G2E_ATTEMPT")


def test_p4_negative_35_pm_cannot_treat_model_strength_as_authority(seeded):
    _forbidden(seeded, "USE_MODEL_STRENGTH_AS_AUTHORITY")


def test_p4_negative_36_pm_cannot_bypass_p1_p2_p3_execution_locks(seeded):
    _forbidden(seeded, "BYPASS_P1_P2_P3_LOCKS")
