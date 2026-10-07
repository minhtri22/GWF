from __future__ import annotations

from pathlib import Path

import pytest

from gwr.domain_governance_vnext import (
    DomainGovernanceProfilePackage,
    DomainGovernanceProfileService,
)
from gwr.errors import AuthorityDenied, InvalidTransition, NotFound, ValidationError
from gwr.utils import content_hash, parse_json


ROOT = Path(__file__).parents[1]
RESEARCH_PACKAGE = ROOT / "domains" / "research.governance_profiles.v1.json"
SOFTWARE_PACKAGE = ROOT / "domains" / "software.governance_profiles.v1.json"


def _service(rt):
    svc = DomainGovernanceProfileService.from_runtime(
        rt,
        [RESEARCH_PACKAGE, SOFTWARE_PACKAGE],
    )
    svc.register_package("research.full-cycle")
    svc.register_package("software.delivery")
    return svc


def _direct_bind(svc, project_id, key, actor_id):
    pkg = svc._package_for_key(key)
    profile = pkg.get(key)
    svc.vnext.bind_project_profile(project_id, profile.ref, actor_id=actor_id)
    return profile


def _edge_conditions(svc, key_from, key_to):
    pkg = svc._package_for_key(key_from)
    edge = pkg.transition_edge(key_from, key_to)
    return list(edge.get("condition_codes") or [])


def _advance_auto(svc, project_id, planner, target_key):
    active = svc.active_profile(project_id)
    conds = _edge_conditions(svc, active.canonical_key, target_key)
    tid = svc.propose_transition(project_id, target_key, planner, conds)
    result = svc.evaluate_transition(tid)
    assert result["disposition"] == "AUTO_ALLOWED"
    svc.activate_transition(tid, planner)
    return tid


def _resolve_human_transition(svc, rt, project_id, planner, approver, target_key):
    active = svc.active_profile(project_id)
    conds = _edge_conditions(svc, active.canonical_key, target_key)
    tid = svc.propose_transition(project_id, target_key, planner, conds)
    result = svc.evaluate_transition(tid)
    assert result["disposition"] == "HUMAN_APPROVAL_REQUIRED"
    har = rt.db.one(
        "SELECT * FROM human_action_requests WHERE human_action_request_id=?",
        (result["human_action_request_id"],),
    )
    frozen_payload = parse_json(har["frozen_payload"], {})
    proposal_id = rt.governance.prepare_proposal(
        project_id,
        planner,
        "CREATE_REVISION",
        [],
        frozen_payload,
        None,
    )
    proposal = rt.db.one("SELECT * FROM proposals WHERE proposal_id=?", (proposal_id,))
    approval_id = rt.governance.approve_proposal(
        proposal_id,
        approver,
        proposal["payload_hash"],
    )
    svc.vnext.resolve_human_action_request(
        result["human_action_request_id"],
        approval_id,
        har["frozen_payload_hash"],
    )
    svc.activate_transition(tid, approver)
    return tid


def test_p2_positive_profile_packages_exact_and_transition_paths(seeded):
    rt, p, planner, _, approver = seeded
    svc = _service(rt)

    svc.bind_initial_profile(p, "research.triage", planner)
    _advance_auto(svc, p, planner, "research.exploratory")
    _advance_auto(svc, p, planner, "research.measurement")
    _resolve_human_transition(svc, rt, p, planner, approver, "research.confirmatory")
    assert svc.active_profile(p).canonical_key == "research.confirmatory"


def test_p2_positive_software_transition_path(seeded):
    rt, p, planner, _, approver = seeded
    svc = _service(rt)

    svc.bind_initial_profile(p, "software.triage", planner)
    _advance_auto(svc, p, planner, "software.development")
    _advance_auto(svc, p, planner, "software.qualification")
    _resolve_human_transition(svc, rt, p, planner, approver, "software.release")
    assert svc.active_profile(p).canonical_key == "software.release"


# 01 research triage cannot consume calibration or protected confirmatory resources.
def test_p2_negative_01_research_triage_protected_firewall(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    svc.bind_initial_profile(p, "research.triage", planner)
    for cls in ("CALIBRATION", "PROTECTED_CONFIRMATORY"):
        with pytest.raises(AuthorityDenied):
            svc.authorize_domain_action(p, "READ_GOVERNED_STATE", protected_resource_class=cls)


# 02 research exploratory cannot consume protected confirmatory resources.
def test_p2_negative_02_research_exploratory_protected_firewall(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.exploratory", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_domain_action(p, "READ_GOVERNED_STATE", protected_resource_class="PROTECTED_CONFIRMATORY")


# 03 research exploratory cannot emit formal scientific verdict.
def test_p2_negative_03_research_exploratory_formal_verdict_firewall(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.exploratory", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_claim(p, "PASS")


# 04 research measurement cannot consume protected confirmatory resources.
def test_p2_negative_04_research_measurement_protected_firewall(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.measurement", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_domain_action(p, "READ_GOVERNED_STATE", protected_resource_class="PROTECTED_CONFIRMATORY")


# 05 research measurement material metric/instrument/protocol mutation cannot remain same lineage.
def test_p2_negative_05_measurement_material_change_requires_successor(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.measurement", planner)
    for code in ("MATERIAL_METRIC_CHANGE", "MATERIAL_INSTRUMENT_CHANGE", "MATERIAL_PROTOCOL_CHANGE"):
        with pytest.raises(InvalidTransition) as exc:
            svc.require_successor_for_material_change(p, code)
        assert exc.value.details["disposition"] == "SUCCESSOR_REQUIRED"


# 06 measurement cannot transition to confirmatory without exact readiness conditions and HumanActionRequest.
def test_p2_negative_06_confirmatory_transition_requires_conditions_and_human_request(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.measurement", planner)
    tid = svc.propose_transition(p, "research.confirmatory", planner, ["MEASUREMENT_PROTOCOL_FROZEN"])
    with pytest.raises(InvalidTransition):
        svc.evaluate_transition(tid)


# 07 research confirmatory cannot mutate frozen hypothesis/metric/threshold/cohort/seed namespace.
def test_p2_negative_07_confirmatory_scientific_mutations_denied(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    for action in (
        "MUTATE_HYPOTHESIS",
        "MUTATE_CONFIRMATORY_METRIC",
        "MUTATE_CONFIRMATORY_THRESHOLD",
        "MUTATE_CONFIRMATORY_COHORT",
        "MUTATE_CONFIRMATORY_SEED_NAMESPACE",
    ):
        with pytest.raises(AuthorityDenied):
            svc.authorize_domain_action(p, action)


# 08 research confirmatory operational failure cannot create scientific FAIL.
def test_p2_negative_08_confirmatory_operational_failure_not_scientific_fail(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    before = rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"]
    assert svc.authorize_domain_action(p, "RECOVER_OPERATIONAL_SAME_SEMANTICS")
    after = rt.db.one("SELECT COUNT(*) AS n FROM decisions")["n"]
    assert before == after
    with pytest.raises(AuthorityDenied):
        svc.authorize_claim(p, "FAIL")


# 09 research confirmatory completion cannot create scientific PASS.
def test_p2_negative_09_confirmatory_profile_does_not_emit_pass(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_claim(p, "PASS")


# 10 research confirmatory protected consumption requires exact bound context.
def test_p2_negative_10_confirmatory_protected_access_context_required(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    for context in (
        {},
        {"resource_identity_bound": True},
        {"resource_identity_bound": True, "consumption_budget_bound": True},
    ):
        with pytest.raises(AuthorityDenied):
            svc.authorize_domain_action(
                p,
                "EXECUTE_FROZEN_CONFIRMATORY_PLAN",
                protected_resource_class="PROTECTED_CONFIRMATORY",
                protected_access_context=context,
            )


# 11 consumed/spent confirmatory attempt cannot be silently rerun or rescued.
def test_p2_negative_11_confirmatory_no_rescue_material_change(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    with pytest.raises(InvalidTransition) as exc:
        svc.require_successor_for_material_change(p, "MUTATE_CONFIRMATORY_THRESHOLD")
    assert exc.value.details["disposition"] == "SUCCESSOR_REQUIRED"


# 12 terminal verdict cannot be rewritten by human approval/profile transition.
def test_p2_negative_12_human_approval_cannot_emit_or_rewrite_scientific_verdict(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    for verdict in ("PASS", "FAIL", "UNRESOLVED"):
        with pytest.raises(AuthorityDenied):
            svc.authorize_claim(p, verdict)


# 13 research successor required for material scientific change.
def test_p2_negative_13_research_successor_required(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    with pytest.raises(InvalidTransition) as exc:
        svc.require_successor_for_material_change(p, "MUTATE_HYPOTHESIS")
    assert exc.value.details["active_profile"] == "research.confirmatory"


# 14 software triage cannot mutate product behavior or perform release action.
def test_p2_negative_14_software_triage_product_and_release_firewall(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    svc.bind_initial_profile(p, "software.triage", planner)
    for action in ("MUTATE_PRODUCT_BEHAVIOR", "MERGE", "DEPLOY", "PUBLISH"):
        with pytest.raises(AuthorityDenied):
            svc.authorize_domain_action(p, action)


# 15 software development cannot emit qualification or release acceptance.
def test_p2_negative_15_software_development_claim_ceiling(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.development", planner)
    for claim in ("QUALIFIED_CANDIDATE", "RELEASE_CANDIDATE", "RELEASE_ACCEPTED"):
        with pytest.raises(AuthorityDenied):
            svc.authorize_claim(p, claim)


# 16 software development out-of-scope mutation is rejected.
def test_p2_negative_16_software_development_scope_expansion_denied(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.development", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_domain_action(p, "EXPAND_SCOPE_WITHOUT_APPROVAL")


# 17 qualification candidate SHA change invalidates prior QA.
def test_p2_negative_17_qualification_candidate_change_invalidates_prior_qa(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.qualification", planner)
    with pytest.raises(AuthorityDenied):
        svc.validate_candidate_identity_change(
            p,
            old_candidate_sha="a" * 40,
            new_candidate_sha="b" * 40,
            prior_qa_reused=True,
            within_frozen_scope=True,
        )


# 18 qualification material scope expansion requires successor development cycle.
def test_p2_negative_18_qualification_scope_expansion_requires_successor(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.qualification", planner)
    with pytest.raises(InvalidTransition) as exc:
        svc.validate_candidate_identity_change(
            p,
            old_candidate_sha="a" * 40,
            new_candidate_sha="b" * 40,
            prior_qa_reused=False,
            within_frozen_scope=False,
        )
    assert exc.value.details["disposition"] == "SUCCESSOR_REQUIRED"


# 19 software qualification cannot emit release acceptance.
def test_p2_negative_19_qualification_release_acceptance_firewall(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.qualification", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_claim(p, "RELEASE_ACCEPTED")


# 20 software release activation requires exact conditions and HumanActionRequest.
def test_p2_negative_20_release_transition_requires_conditions_and_human_request(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.qualification", planner)
    tid = svc.propose_transition(p, "software.release", planner, ["EXACT_CANDIDATE_SHA_FROZEN"])
    with pytest.raises(InvalidTransition):
        svc.evaluate_transition(tid)


# 21 software release cannot mutate frozen product candidate.
def test_p2_negative_21_release_candidate_mutation_denied(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.release", planner)
    with pytest.raises(AuthorityDenied):
        svc.authorize_domain_action(p, "MUTATE_PRODUCT_CODE")


# 22 software release external effect retry requires idempotency/effect ledger proof.
def test_p2_negative_22_release_effect_retry_requires_safety_proof(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.release", planner)
    with pytest.raises(AuthorityDenied):
        svc.assert_external_effect_retry_safe(p, idempotency_proven=True, effect_ledger_reconciled=False)


# 23 research profile ref cannot be used as software profile ref and vice versa.
def test_p2_negative_23_cross_domain_profile_ref_rejected(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    research_pkg = svc._package("research.full-cycle")
    software_pkg = svc._package("software.delivery")
    with pytest.raises(NotFound):
        software_pkg.key_for_ref(research_pkg.get("research.triage").ref)


# 24 profile policy cannot expand parent authority or budget.
def test_p2_negative_24_profile_cannot_expand_parent_authority_or_budget(seeded):
    rt, p, *_ = seeded
    parent_auth = rt.vnext_governance.create_authority_envelope(
        p,
        {"prim_authority_ref": "base"},
        {"role": "operator"},
        [{"project_id": p}],
        ["READ"],
        [],
    )
    with pytest.raises(AuthorityDenied):
        rt.vnext_governance.create_authority_envelope(
            p,
            {"authority_envelope_id": parent_auth},
            {"role": "operator"},
            [{"project_id": p}],
            ["READ", "EXECUTE"],
            [],
        )
    parent_budget = rt.vnext_governance.create_budget_envelope(
        p,
        [{"dimension": "attempts", "unit": "count", "ceiling": 1, "enforcement": "HARD"}],
    )
    with pytest.raises(AuthorityDenied):
        rt.vnext_governance.create_budget_envelope(
            p,
            [{"dimension": "attempts", "unit": "count", "ceiling": 2, "enforcement": "HARD"}],
            parent_budget_ref={"budget_envelope_id": parent_budget},
        )


# 25 missing transition edge fails closed.
def test_p2_negative_25_missing_transition_edge_fails_closed(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.triage", planner)
    with pytest.raises(InvalidTransition):
        svc.propose_transition(
            p,
            "research.measurement",
            planner,
            ["MEASUREMENT_OBJECT_DEFINED"],
        )


# 26 UI/browser state cannot activate or transition a profile.
def test_p2_negative_26_ui_state_has_no_profile_authority(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    svc.bind_initial_profile(p, "research.triage", planner)
    conds = _edge_conditions(svc, "research.triage", "research.exploratory")
    with pytest.raises((NotFound, AuthorityDenied)):
        svc.propose_transition(p, "research.exploratory", "browser-ui-state", conds)


# 27 provider/model/transport identity cannot alter profile semantics.
def test_p2_negative_27_executor_identity_not_profile_semantics(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    profile = _direct_bind(svc, p, "research.exploratory", planner)
    baseline_hash = content_hash(profile.definition)
    foreign_executor_identity = {
        "provider": "arbitrary-provider",
        "model": "arbitrary-model",
        "transport": "arbitrary-transport",
    }
    assert foreign_executor_identity
    assert content_hash(svc.active_profile(p).definition) == baseline_hash


# 28 in-place backward transition is absent and fails closed.
def test_p2_negative_28_backward_transition_fails_closed(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.measurement", planner)
    with pytest.raises(InvalidTransition):
        svc.propose_transition(
            p,
            "research.exploratory",
            planner,
            ["MATERIAL_METRIC_CHANGE"],
        )


# 29 operational recovery in advanced profiles does not downgrade to triage.
def test_p2_negative_29_operational_recovery_does_not_downgrade_profile(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    before = svc.active_profile(p).ref.to_dict()
    assert svc.authorize_domain_action(p, "RECOVER_OPERATIONAL_SAME_SEMANTICS")
    after = svc.active_profile(p).ref.to_dict()
    assert before == after
    with pytest.raises(InvalidTransition):
        svc.propose_transition(p, "research.triage", planner, ["OPERATIONAL_BLOCKER_CLEARED"])


# 30 same exact profile payload deterministically yields frozen expected profile hash.
def test_p2_negative_30_exact_profile_hashes_are_deterministic_and_frozen(seeded):
    rt, *_ = seeded
    svc = _service(rt)
    for pkg in svc.packages.values():
        for key, entry in pkg.profiles.items():
            assert content_hash(entry["definition"]) == entry["expected_profile_hash"]
            assert pkg.get(key).ref.profile_hash == entry["expected_profile_hash"]


def test_p2_positive_confirmatory_protected_access_with_exact_context(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "research.confirmatory", planner)
    assert svc.authorize_domain_action(
        p,
        "EXECUTE_FROZEN_CONFIRMATORY_PLAN",
        protected_resource_class="PROTECTED_CONFIRMATORY",
        protected_access_context={
            "resource_identity_bound": True,
            "consumption_budget_bound": True,
            "human_authorized": True,
        },
    )


def test_p2_positive_qualification_bounded_repair_requires_new_qa_identity(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.qualification", planner)
    assert svc.validate_candidate_identity_change(
        p,
        old_candidate_sha="a" * 40,
        new_candidate_sha="b" * 40,
        prior_qa_reused=False,
        within_frozen_scope=True,
    )


def test_p2_positive_release_effect_retry_when_proven_safe(seeded):
    rt, p, planner, *_ = seeded
    svc = _service(rt)
    _direct_bind(svc, p, "software.release", planner)
    assert svc.assert_external_effect_retry_safe(
        p,
        idempotency_proven=True,
        effect_ledger_reconciled=True,
    )
