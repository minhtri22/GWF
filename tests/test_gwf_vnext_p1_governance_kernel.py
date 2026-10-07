import pytest

from gwr.errors import ApprovalMismatch, AuthorityDenied, InvalidTransition, NotFound, ValidationError
from gwr.governance_vnext import GovernanceProfileRef


def _profile(rt, domain_id, profile_id, version="1", *, policy=None, edges=None):
    return rt.vnext_governance.register_profile_definition(
        domain_id,
        profile_id,
        version,
        policy or {
            "autonomy_policy": {},
            "mutation_policy": {},
            "protected_resource_policy": {},
            "lineage_policy": {},
            "approval_policy": {},
            "retry_recovery_policy": {},
            "claim_permission_policy": {},
        },
        edges or [],
    )


def _root_authority(rt, project_id):
    return rt.vnext_governance.create_authority_envelope(
        project_id,
        {"prim_authority_ref": "base"},
        {"role": "operator"},
        [{"project_id": project_id}, {"scope": "workspace"}],
        ["READ", "EXECUTE", "PROPOSE"],
        ["DELETE"],
    )


def _root_budget(rt, project_id):
    return rt.vnext_governance.create_budget_envelope(
        project_id,
        [
            {"dimension": "attempts", "unit": "count", "ceiling": 4, "enforcement": "HARD"},
            {"dimension": "wall_time", "unit": "seconds", "ceiling": 300, "enforcement": "ADVISORY"},
        ],
    )


def _environment(rt):
    return rt.vnext_governance.register_execution_environment(
        "zero-provider-fixture",
        "zero.adapter",
        "1",
        "a" * 64,
        {"manifest_id": "cap-zero", "hash": "b" * 64},
        transport_class="none",
        locality_class="local-test",
        secret_connection_ref="opaque:test-connection",
    )


def _assignment(rt, project_id, planner, auth_id, budget_id, *, objective=None):
    return rt.vnext_governance.create_work_assignment(
        project_id,
        [{"kind": "fixture", "id": "origin-1"}],
        objective or {"task": "zero-provider"},
        {"role": "operator"},
        ["repository_read"],
        {"allowed_environment_types": ["zero-provider-fixture"]},
        {"authority_envelope_id": auth_id},
        {"budget_envelope_id": budget_id},
        [{"kind": "fixture-result"}],
        {"required": ["fixture-result"]},
        proposer_actor_id=planner,
    )


def _binding(rt, assignment_id, auth_id, budget_id, env_id, *, mode="DYNAMIC"):
    return rt.vnext_governance.create_executor_binding(
        assignment_id,
        mode,
        {"role": "operator"},
        {"agent_app": "zero-fixture", "model": "zero-model"},
        {"execution_environment_id": env_id},
        {"manifest_id": "cap-zero", "hash": "b" * 64},
        ["agent_app", "model", "execution_environment"],
        {"authority_envelope_id": auth_id},
        {"budget_envelope_id": budget_id},
        equivalence_policy_ref={"policy": "exact-zero-fixture"} if mode == "DYNAMIC" else None,
    )


def test_p1_positive_zero_provider_contract_roundtrip(seeded):
    rt, p, planner, operator, approver = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    env = _environment(rt)
    wa = _assignment(rt, p, planner, auth, budget)
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, planner)
    binding = _binding(rt, wa, auth, budget, env)
    rt.vnext_governance.authorize_work_assignment(wa, approver, frozen_hash)
    rt.vnext_governance.dispatch_work_assignment(wa, binding, approver)
    rt.vnext_governance.mark_assignment_running(wa, operator)
    rt.vnext_governance.mark_assignment_completed(wa, operator)
    row = rt.db.one("SELECT state FROM work_assignments WHERE work_assignment_id=?", (wa,))
    assert row["state"] == "COMPLETED"
    assert rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"] == 0


# 1. child AuthorityEnvelope cannot add an action absent from parent.
def test_p1_negative_01_authority_child_cannot_add_action(seeded):
    rt, p, *_ = seeded
    parent = _root_authority(rt, p)
    with pytest.raises(AuthorityDenied):
        rt.vnext_governance.create_authority_envelope(
            p,
            {"authority_envelope_id": parent},
            {"role": "operator"},
            [{"project_id": p}],
            ["READ", "APPROVE"],
            [],
        )


# 2. child resource scope cannot widen parent scope.
def test_p1_negative_02_authority_child_cannot_widen_resource_scope(seeded):
    rt, p, *_ = seeded
    parent = _root_authority(rt, p)
    with pytest.raises(AuthorityDenied):
        rt.vnext_governance.create_authority_envelope(
            p,
            {"authority_envelope_id": parent},
            {"role": "operator"},
            [{"project_id": p}, {"scope": "outside-parent"}],
            ["READ"],
            [],
        )


# 3. DENY overrides ALLOW.
def test_p1_negative_03_authority_deny_wins(seeded):
    rt, p, *_ = seeded
    root = rt.vnext_governance.create_authority_envelope(
        p,
        {"prim_authority_ref": "base"},
        {"role": "operator"},
        [{"project_id": p}],
        ["READ", "EXECUTE"],
        ["EXECUTE"],
    )
    effective = rt.vnext_governance.effective_authority(root)
    assert "EXECUTE" not in effective["allow_actions"]
    assert "EXECUTE" in effective["deny_actions"]


# 4. child budget cannot increase inherited ceiling silently.
def test_p1_negative_04_budget_child_cannot_expand_ceiling(seeded):
    rt, p, *_ = seeded
    parent = _root_budget(rt, p)
    with pytest.raises(AuthorityDenied):
        rt.vnext_governance.create_budget_envelope(
            p,
            [{"dimension": "attempts", "unit": "count", "ceiling": 5, "enforcement": "HARD"}],
            parent_budget_ref={"budget_envelope_id": parent},
        )


# 5. WorkAssignment PROPOSED cannot dispatch.
def test_p1_negative_05_proposed_assignment_cannot_dispatch(seeded):
    rt, p, planner, *_ = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    wa = _assignment(rt, p, planner, auth, budget)
    with pytest.raises(InvalidTransition):
        rt.vnext_governance.dispatch_work_assignment(wa, "not-a-binding", planner)


# 6. changed frozen assignment payload invalidates prior authorization.
def test_p1_negative_06_changed_frozen_assignment_invalidates_authorization(seeded):
    rt, p, planner, _, approver = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    wa = _assignment(rt, p, planner, auth, budget)
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, planner)
    rt.db.conn.execute(
        "UPDATE work_assignments SET objective=? WHERE work_assignment_id=?",
        ('{"task":"tampered"}', wa),
    )
    rt.db.conn.commit()
    with pytest.raises(ApprovalMismatch):
        rt.vnext_governance.authorize_work_assignment(wa, approver, frozen_hash)


# 7. changed HumanActionRequest payload invalidates prior approval/request.
def test_p1_negative_07_human_action_payload_change_invalidates_resolution(seeded):
    rt, p, planner, _, approver = seeded
    frozen = {"action": "expand-budget", "delta": 1}
    proposal = rt.governance.prepare_proposal(
        p,
        planner,
        "CREATE_REVISION",
        [],
        frozen,
        "normative_change",
    )
    prop = rt.db.one("SELECT * FROM proposals WHERE proposal_id=?", (proposal,))
    approval = rt.governance.approve_proposal(proposal, approver, prop["payload_hash"])
    request = rt.vnext_governance.create_human_action_request(
        p,
        "BUDGET_EXPANSION",
        {"kind": "budget", "id": "b1"},
        frozen,
        "APPROVE",
        {"actor_type": "HUMAN"},
        ["EXPANSION"],
    )
    row = rt.db.one("SELECT * FROM human_action_requests WHERE human_action_request_id=?", (request,))
    rt.db.conn.execute(
        "UPDATE human_action_requests SET frozen_payload=? WHERE human_action_request_id=?",
        ('{"action":"expand-budget","delta":2}', request),
    )
    rt.db.conn.commit()
    with pytest.raises(ApprovalMismatch):
        rt.vnext_governance.resolve_human_action_request(request, approval, row["frozen_payload_hash"])


# 8. dynamic ExecutorBinding cannot mutate after dispatch.
def test_p1_negative_08_dynamic_binding_immutable_after_dispatch(seeded):
    rt, p, planner, _, approver = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    env = _environment(rt)
    wa = _assignment(rt, p, planner, auth, budget)
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, planner)
    binding = _binding(rt, wa, auth, budget, env, mode="DYNAMIC")
    rt.vnext_governance.authorize_work_assignment(wa, approver, frozen_hash)
    rt.vnext_governance.dispatch_work_assignment(wa, binding, approver)
    with pytest.raises(InvalidTransition):
        rt.vnext_governance.substitute_executor_binding(binding, {"agent_app": "replacement"})


# 9. frozen ExecutorBinding substitution is rejected.
def test_p1_negative_09_frozen_binding_substitution_rejected(seeded):
    rt, p, planner, *_ = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    env = _environment(rt)
    wa = _assignment(rt, p, planner, auth, budget)
    rt.vnext_governance.freeze_work_assignment(wa, planner)
    binding = _binding(rt, wa, auth, budget, env, mode="FROZEN")
    with pytest.raises(InvalidTransition):
        rt.vnext_governance.substitute_executor_binding(binding, {"agent_app": "replacement"})


# 10. WorkAssignment COMPLETED cannot directly set a G2E/scientific verdict.
def test_p1_negative_10_assignment_completion_does_not_create_domain_verdict(seeded):
    rt, p, planner, operator, approver = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    env = _environment(rt)
    wa = _assignment(rt, p, planner, auth, budget)
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, planner)
    binding = _binding(rt, wa, auth, budget, env)
    rt.vnext_governance.authorize_work_assignment(wa, approver, frozen_hash)
    rt.vnext_governance.dispatch_work_assignment(wa, binding, approver)
    rt.vnext_governance.mark_assignment_running(wa, operator)
    before = rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"]
    rt.vnext_governance.mark_assignment_completed(wa, operator)
    after = rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"]
    assert before == after
    assert rt.db.one("SELECT state FROM work_assignments WHERE work_assignment_id=?", (wa,))["state"] == "COMPLETED"


# 11. foreign runtime IDs cannot replace canonical assignment identity.
def test_p1_negative_11_foreign_runtime_id_cannot_replace_assignment_identity(seeded):
    rt, p, *_ = seeded
    env = _environment(rt)
    with pytest.raises(NotFound):
        rt.vnext_governance.create_executor_binding(
            "foreign-runtime-id",
            "DYNAMIC",
            {"role": "operator"},
            {"agent_app": "zero"},
            {"execution_environment_id": env},
            {"manifest_id": "cap-zero"},
            [],
            {"authority_envelope_id": "auth"},
            {"budget_envelope_id": "budget"},
        )


# 12. UI state cannot authorize execution.
def test_p1_negative_12_ui_state_cannot_authorize_execution(seeded):
    rt, p, planner, *_ = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    wa = _assignment(rt, p, planner, auth, budget)
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, planner)
    with pytest.raises((NotFound, AuthorityDenied)):
        rt.vnext_governance.authorize_work_assignment(wa, "browser-ui-state", frozen_hash)


# 13. unresolved profile hash cannot execute/resolve.
def test_p1_negative_13_unresolved_profile_hash_fails_closed(seeded):
    rt, *_ = seeded
    ref = _profile(rt, "zero.domain", "zero.profile")
    bad = ref.to_dict()
    bad["profile_hash"] = "0" * 64
    with pytest.raises(NotFound):
        rt.vnext_governance.resolve_profile_ref(bad)


# 14. unknown profile transition edge fails closed.
def test_p1_negative_14_unknown_transition_edge_fails_closed(seeded):
    rt, p, planner, *_ = seeded
    source = _profile(rt, "zero.domain", "source")
    target = _profile(rt, "zero.domain", "target")
    transition = rt.vnext_governance.propose_transition(
        p,
        {"kind": "project", "id": p},
        source,
        target,
        planner,
        ["TEST"],
    )
    with pytest.raises(InvalidTransition):
        rt.vnext_governance.evaluate_transition(transition)


# 15. provider credentials cannot serialize into P1 contract records.
def test_p1_negative_15_raw_secret_serialization_rejected(seeded):
    rt, p, planner, *_ = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    with pytest.raises(ValidationError):
        _assignment(rt, p, planner, auth, budget, objective={"task": "x", "api_key": "secret"})


# 16. operational failure does not create domain PASS/FAIL by itself.
def test_p1_negative_16_operational_failure_does_not_create_domain_verdict(seeded):
    rt, p, planner, _, approver = seeded
    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    env = _environment(rt)
    wa = _assignment(rt, p, planner, auth, budget)
    frozen_hash = rt.vnext_governance.freeze_work_assignment(wa, planner)
    binding = _binding(rt, wa, auth, budget, env)
    rt.vnext_governance.authorize_work_assignment(wa, approver, frozen_hash)
    rt.vnext_governance.dispatch_work_assignment(wa, binding, approver)
    before_gates = rt.db.one("SELECT COUNT(*) AS n FROM gates")["n"]
    before_decisions = rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"]
    rt.vnext_governance.mark_assignment_operational_failure(wa, "SYSTEM", "NETWORK_TIMEOUT")
    assert rt.db.one("SELECT state FROM work_assignments WHERE work_assignment_id=?", (wa,))["state"] == "BLOCKED"
    assert rt.db.one("SELECT COUNT(*) AS n FROM gates")["n"] == before_gates
    assert rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"] == before_decisions


def test_p1_profile_transition_exact_edge_and_effective_policy(seeded):
    rt, p, planner, *_ = seeded
    target = _profile(rt, "zero.domain", "target")
    edge = {
        "target_profile_ref": target.to_dict(),
        "condition_codes": ["ZERO_FIXTURE"],
        "disposition": "AUTO_ALLOWED",
        "required_human_action_kind": None,
    }
    source = _profile(rt, "zero.domain", "source-with-edge", edges=[edge])
    transition = rt.vnext_governance.propose_transition(
        p,
        {"kind": "project", "id": p},
        source,
        target,
        planner,
        ["ZERO_FIXTURE"],
    )
    assert rt.vnext_governance.evaluate_transition(transition) == "AUTO_ALLOWED"

    auth = _root_authority(rt, p)
    budget = _root_budget(rt, p)
    compiled = rt.vnext_governance.compile_effective_policy(
        p,
        {"source": "zero-base"},
        source,
        {"fixture": True},
        auth,
        budget,
        [],
    )
    assert len(compiled["compiled_hash"]) == 64
    assert compiled["provenance"]["profile_ref"] == source.to_dict()


def test_p1_budget_usage_is_separate_from_frozen_definition(seeded):
    rt, p, *_ = seeded
    budget = _root_budget(rt, p)
    before = rt.db.one("SELECT payload_hash FROM budget_envelopes WHERE budget_envelope_id=?", (budget,))["payload_hash"]
    assert rt.vnext_governance.record_budget_usage(budget, "attempts", 1) == 1
    after = rt.db.one("SELECT payload_hash FROM budget_envelopes WHERE budget_envelope_id=?", (budget,))["payload_hash"]
    assert before == after
    with pytest.raises(AuthorityDenied):
        rt.vnext_governance.record_budget_usage(budget, "attempts", 4)
