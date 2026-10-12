from __future__ import annotations

import copy

import pytest

from gwr.errors import AuthorityDenied, GateBlocked, InvalidTransition, ValidationError
from gwr.remotemcp_execution_vnext import (
    CANONICAL_PLUGIN,
    CANONICAL_TRANSPORT,
    ENVIRONMENT_TYPE,
    RemoteMCPExecutionEnvironmentVNext,
    argv_sha256,
)
from gwr.utils import content_hash


H = "a" * 64
H2 = "b" * 64
H3 = "c" * 64
H4 = "d" * 64


@pytest.fixture
def adapter():
    return RemoteMCPExecutionEnvironmentVNext()


def exact_ref(name: str, digest: str = H):
    return {"object_id": name, "revision_id": "r1", "content_hash": digest}


def base_session():
    return {
        "available": True,
        "plugin_identity": CANONICAL_PLUGIN,
        "transport": CANONICAL_TRANSPORT,
        "backend_namespace": "opaque-backend-name",
    }


def base_worker():
    return {
        "worker_context_ref": "worker-context-1",
        "agent_identity_projection_hash": H,
        "session_binding_class": "APP_BACKED",
        "backend_namespace": "opaque-backend-name",
    }


def base_placement():
    value = {
        "placement_id": "plc-1",
        "revision": 1,
        "work_assignment_id": "wa-1",
        "work_assignment_revision": 1,
        "work_assignment_frozen_hash": H,
        "executor_binding_id": "eb-1",
        "executor_binding_resolved_payload_hash": H2,
        "execution_environment_id": "env-remotemcp-1",
        "worker_context_ref": "worker-context-1",
        "device_id": "device-1",
        "device_key_fingerprint_sha256": H3,
        "route_generation": 7,
        "project_id": "project-1",
        "project_binding_generation": 3,
        "task_id": "task-1",
        "repository_or_source_ref": "repo-1",
        "base_commit_or_source_digest": H4,
        "branch_ref": "pivot/test",
        "worktree_ref_or_explicit_non_git_qualification": "worktree-1",
        "project_root": r"D:\WORK\RESEARCH\SYNTHETIC-P5",
    }
    value["content_hash"] = content_hash(value)
    return value


def placement_expected():
    p = base_placement()
    return {
        key: p[key]
        for key in (
            "work_assignment_id",
            "work_assignment_revision",
            "work_assignment_frozen_hash",
            "executor_binding_id",
            "executor_binding_resolved_payload_hash",
            "execution_environment_id",
            "worker_context_ref",
            "device_id",
            "device_key_fingerprint_sha256",
            "route_generation",
            "project_id",
            "project_binding_generation",
            "task_id",
            "repository_or_source_ref",
            "base_commit_or_source_digest",
            "branch_ref",
            "worktree_ref_or_explicit_non_git_qualification",
        )
    }


def base_job_submission():
    argv = ["python", "-m", "pytest", "-q", "synthetic_fixture.py"]
    return {
        "task_id": "task-1",
        "project_id": "project-1",
        "device_id": "device-1",
        "lease_epoch": 11,
        "submitted_argv_sha256": argv_sha256(argv),
        "argv": argv,
        "mutating": False,
        "semantic_duplicate": False,
        "task_scoped_routed": True,
    }


def base_job_observation():
    sub = base_job_submission()
    return {
        "proxy_job_id": "rjob-1",
        "node_job_id": "node-job-1",
        "task_id": "task-1",
        "project_id": "project-1",
        "device_id": "device-1",
        "submitted_argv_sha256": sub["submitted_argv_sha256"],
        "state": "SUCCEEDED",
        "terminal": True,
        "terminal_event_id": "term-1",
    }


def base_checkpoint():
    return {
        "checkpoint_id": "cp-1",
        "revision": 1,
        "g2e_execution_attempt_exact_ref": exact_ref("attempt-1"),
        "work_assignment_exact_ref": exact_ref("wa-1", H2),
        "executor_binding_exact_ref": exact_ref("eb-1", H3),
        "placement_exact_ref": exact_ref("plc-1", H4),
        "source_state_ref": {"source": "repo-1", "digest": H4, "worktree": "worktree-1"},
        "latest_job_refs": [{"proxy_job_id": "rjob-1", "node_job_id": "node-job-1"}],
        "protected_resource_state": "RESERVED",
        "semantic_state_digest": H,
    }


def checkpoint_expected():
    cp = base_checkpoint()
    return {
        key: cp[key]
        for key in (
            "g2e_execution_attempt_exact_ref",
            "work_assignment_exact_ref",
            "executor_binding_exact_ref",
            "placement_exact_ref",
            "source_state_ref",
        )
    }


def base_result():
    sub = base_job_submission()
    return {
        "g2e_execution_attempt_exact_ref": exact_ref("attempt-1"),
        "work_assignment_exact_ref": exact_ref("wa-1", H2),
        "executor_binding_exact_ref": exact_ref("eb-1", H3),
        "execution_environment_ref": {
            "execution_environment_id": "env-remotemcp-1",
            "environment_type": ENVIRONMENT_TYPE,
        },
        "worker_context_ref": "worker-context-1",
        "placement_exact_ref": exact_ref("plc-1", H4),
        "device_id": "device-1",
        "device_key_fingerprint_sha256": H3,
        "route_generation": 7,
        "project_id": "project-1",
        "project_binding_generation": 3,
        "task_id": "task-1",
        "worktree_or_source_state_ref": {
            "source": "repo-1",
            "digest": H4,
            "worktree": "worktree-1",
        },
        "proxy_job_id": "rjob-1",
        "node_job_id": "node-job-1",
        "submitted_argv_sha256": sub["submitted_argv_sha256"],
        "terminal_event_id": "term-1",
        "terminal_state": "SUCCEEDED",
        "exit_code": 0,
        "stdout_ref_and_digest": {"ref": "stdout-1", "digest": H},
        "stderr_ref_and_digest": {"ref": "stderr-1", "digest": H2},
        "artifact_refs_and_digests": [{"ref": "artifact-1", "digest": H3}],
        "checkpoint_ref_if_any": {"checkpoint_id": "cp-1", "content_hash": H4},
        "environment_attestation_ref": {"attestation_id": "att-1", "digest": H},
        "protected_resource_state": "RESERVED",
        "operational_status": "OPERATIONAL_SUCCEEDED",
        "independently_retrievable": True,
    }


def result_expected():
    r = base_result()
    return {
        key: r[key]
        for key in (
            "g2e_execution_attempt_exact_ref",
            "work_assignment_exact_ref",
            "executor_binding_exact_ref",
            "device_id",
            "device_key_fingerprint_sha256",
            "route_generation",
            "project_id",
            "project_binding_generation",
            "task_id",
            "proxy_job_id",
            "node_job_id",
            "submitted_argv_sha256",
        )
    }


def test_p5_positive_01_canonical_session_and_worker_context(adapter):
    env = adapter.validate_session_binding(base_session())
    assert env["environment_type"] == ENVIRONMENT_TYPE
    assert adapter.validate_worker_context(
        base_worker(), executor_agent_projection_hash=H
    )["worker_context_ref"] == "worker-context-1"


def test_p5_positive_02_exact_placement(adapter):
    p = base_placement()
    assert adapter.validate_placement(
        p,
        expected=placement_expected(),
        approved_project_root=r"D:\WORK\RESEARCH\SYNTHETIC-P5",
    )["placement_id"] == "plc-1"


def test_p5_positive_03_lease_job_and_reconciliation(adapter):
    adapter.validate_lease_observation(
        {"task_id": "task-1", "lease_epoch": 11, "acquired_at": "t0", "expires_at": "t1"},
        expected_task_id="task-1",
        current_epoch=11,
    )
    p = base_placement()
    sub = base_job_submission()
    adapter.validate_job_submission(
        sub,
        placement=p,
        current_lease_epoch=11,
        ephemeral_lease_present=True,
        active_mutating_jobs=0,
    )
    rec = adapter.reconcile_job(
        base_job_observation(),
        placement=p,
        expected_proxy_job_id="rjob-1",
        expected_argv_sha256=sub["submitted_argv_sha256"],
    )
    assert rec["execution_proven"] is True


def test_p5_positive_04_checkpoint_and_recovery(adapter):
    cp = base_checkpoint()
    adapter.validate_checkpoint(
        cp,
        expected_refs=checkpoint_expected(),
        previous_protected_state="FRESH",
    )
    old = base_placement() | {"protected_resource_state": "FRESH"}
    new = copy.deepcopy(old)
    new["protected_resource_state"] = "RESERVED"
    adapter.validate_recovery(old, new)


def test_p5_positive_05_result_is_candidate_only(adapter):
    result = base_result()
    adapter.validate_result_envelope(
        result,
        expected=result_expected(),
        observed_digests={"stdout": H, "stderr": H2, "artifact-1": H3},
    )
    candidate = adapter.candidate_evidence_projection(result)
    assert candidate["admission_state"] == "CANDIDATE"
    assert candidate["scientific_verdict"] is None


def test_p5_positive_06_authority_and_qualification_scope(adapter):
    allowed = adapter.validate_authority(
        requested_actions=["READ"],
        work_assignment_actions=["READ", "WRITE"],
        executor_binding_actions=["READ"],
        governance_profile_actions=["READ"],
        environment_capabilities=["READ", "EXECUTE"],
        placement_policy_actions=["READ"],
        human_action_actions=["READ"],
    )
    assert allowed == {"READ"}
    adapter.validate_qualification_scope(
        {
            "synthetic_only": True,
            "zero_science_only": True,
            "real_project_execution": False,
            "protected_evidence_consumption": False,
            "p6_route_import": False,
            "mission_control_refactor": False,
        }
    )


def test_p5_negative_01_canonical_plugin_missing_no_legacy_fallback(adapter):
    with pytest.raises(GateBlocked):
        adapter.validate_session_binding(
            {"available": False, "plugin_identity": "remote-mcp-v2-web", "transport": "direct-mcp"}
        )


def test_p5_negative_02_plugin_session_failure_no_node_repair(adapter):
    with pytest.raises(GateBlocked):
        adapter.validate_session_binding(
            {"available": False, "plugin_identity": CANONICAL_PLUGIN, "transport": CANONICAL_TRANSPORT}
        )
    with pytest.raises(AuthorityDenied):
        adapter.assert_infrastructure_action("device_restart")


def test_p5_negative_03_backend_namespace_not_environment_identity(adapter):
    binding = base_session()
    binding["backend_namespace"] = "RemoteDesktop"
    env = adapter.validate_session_binding(binding)
    assert env == {
        "environment_type": ENVIRONMENT_TYPE,
        "plugin_identity": CANONICAL_PLUGIN,
        "transport": CANONICAL_TRANSPORT,
    }


def test_p5_negative_04_worker_context_executor_binding_mismatch(adapter):
    with pytest.raises(ValidationError):
        adapter.validate_worker_context(base_worker(), executor_agent_projection_hash=H2)


def test_p5_negative_05_material_worker_identity_substitution_no_in_place_reuse(adapter):
    with pytest.raises(InvalidTransition):
        adapter.validate_worker_context(
            base_worker(),
            executor_agent_projection_hash=H,
            material_identity_substitution=True,
        )


def test_p5_negative_06_device_id_substitution(adapter):
    p = base_placement()
    p["device_id"] = "device-other"
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_07_device_fingerprint_substitution(adapter):
    p = base_placement()
    p["device_key_fingerprint_sha256"] = H4
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_08_unapproved_route_generation_change(adapter):
    with pytest.raises(InvalidTransition):
        adapter.validate_route_generation(previous=7, current=8)


def test_p5_negative_09_project_id_substitution(adapter):
    p = base_placement()
    p["project_id"] = "project-other"
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_10_project_binding_generation_substitution(adapter):
    p = base_placement()
    p["project_binding_generation"] = 99
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_11_project_root_mismatch_no_widen(adapter):
    p = base_placement()
    with pytest.raises(GateBlocked):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=r"D:\OTHER"
        )


def test_p5_negative_12_root_mismatch_no_replacement_device_or_project(adapter):
    p = base_placement()
    with pytest.raises(GateBlocked):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=r"D:\UNAPPROVED"
        )


def test_p5_negative_13_task_cannot_override_device_placement(adapter):
    p = base_placement()
    p["task_device_override"] = "device-other"
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_14_task_cannot_override_project_identity(adapter):
    p = base_placement()
    p["task_project_override"] = "project-other"
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_15_git_source_worktree_base_mismatch(adapter):
    p = base_placement()
    p["base_commit_or_source_digest"] = "e" * 64
    p["content_hash"] = content_hash({k: v for k, v in p.items() if k != "content_hash"})
    with pytest.raises(ValidationError):
        adapter.validate_placement(
            p, expected=placement_expected(), approved_project_root=p["project_root"]
        )


def test_p5_negative_16_gateway_local_command_not_routed_evidence(adapter):
    sub = base_job_submission()
    sub["task_scoped_routed"] = False
    with pytest.raises(ValidationError):
        adapter.validate_job_submission(
            sub,
            placement=base_placement(),
            current_lease_epoch=11,
            ephemeral_lease_present=True,
            active_mutating_jobs=0,
        )


def test_p5_negative_17_lease_token_persistence_forbidden(adapter):
    with pytest.raises(ValidationError):
        adapter.validate_lease_observation(
            {"task_id": "task-1", "lease_epoch": 11, "lease_token": "capability-secret"},
            expected_task_id="task-1",
            current_epoch=11,
        )


def test_p5_negative_18_pairing_secret_in_task_job_or_repository_forbidden(adapter):
    sub = base_job_submission()
    sub["argv"] = ["python", "PAIRING_SECRET=do-not-store"]
    with pytest.raises(ValidationError):
        adapter.validate_job_submission(
            sub,
            placement=base_placement(),
            current_lease_epoch=11,
            ephemeral_lease_present=True,
            active_mutating_jobs=0,
        )


def test_p5_negative_19_connector_secret_in_log_checkpoint_evidence_forbidden(adapter):
    cp = base_checkpoint()
    cp["connector_secret"] = "secret"
    with pytest.raises(ValidationError):
        adapter.validate_checkpoint(
            cp, expected_refs=checkpoint_expected(), previous_protected_state="FRESH"
        )


def test_p5_negative_20_stale_lease_epoch_mutation(adapter):
    with pytest.raises(InvalidTransition):
        adapter.validate_lease_observation(
            {"task_id": "task-1", "lease_epoch": 10},
            expected_task_id="task-1",
            current_epoch=11,
        )


def test_p5_negative_21_job_submit_without_current_task_lease(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_job_submission(
            base_job_submission(),
            placement=base_placement(),
            current_lease_epoch=11,
            ephemeral_lease_present=False,
            active_mutating_jobs=0,
        )


def test_p5_negative_22_job_wrong_task_project_device(adapter):
    sub = base_job_submission()
    sub["task_id"] = "task-other"
    with pytest.raises(ValidationError):
        adapter.validate_job_submission(
            sub,
            placement=base_placement(),
            current_lease_epoch=11,
            ephemeral_lease_present=True,
            active_mutating_jobs=0,
        )


def test_p5_negative_23_proxy_node_job_provenance_mismatch(adapter):
    obs = base_job_observation()
    obs["proxy_job_id"] = "rjob-other"
    with pytest.raises(ValidationError):
        adapter.reconcile_job(
            obs,
            placement=base_placement(),
            expected_proxy_job_id="rjob-1",
            expected_argv_sha256=base_job_submission()["submitted_argv_sha256"],
        )


def test_p5_negative_24_submitted_argv_hash_mismatch(adapter):
    obs = base_job_observation()
    with pytest.raises(ValidationError):
        adapter.reconcile_job(
            obs,
            placement=base_placement(),
            expected_proxy_job_id="rjob-1",
            expected_argv_sha256="f" * 64,
        )


def test_p5_negative_25_second_mutating_active_job_same_task(adapter):
    sub = base_job_submission()
    sub["mutating"] = True
    with pytest.raises(InvalidTransition):
        adapter.validate_job_submission(
            sub,
            placement=base_placement(),
            current_lease_epoch=11,
            ephemeral_lease_present=True,
            active_mutating_jobs=1,
        )


def test_p5_negative_26_duplicate_scientific_command_after_observability_loss(adapter):
    sub = base_job_submission()
    sub["semantic_duplicate"] = True
    with pytest.raises(InvalidTransition):
        adapter.validate_job_submission(
            sub,
            placement=base_placement(),
            current_lease_epoch=11,
            ephemeral_lease_present=True,
            active_mutating_jobs=0,
            scientific_observability_lost=True,
        )


def test_p5_negative_27_technical_capability_not_authority(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_authority(
            requested_actions=["WRITE"],
            work_assignment_actions=["READ"],
            executor_binding_actions=["READ"],
            governance_profile_actions=["READ"],
            environment_capabilities=["READ", "WRITE"],
            placement_policy_actions=["READ"],
            human_action_actions=["READ"],
            technical_capabilities=["WRITE"],
        )


def test_p5_negative_28_connector_account_permission_not_authority(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_authority(
            requested_actions=["WRITE"],
            work_assignment_actions=["READ"],
            executor_binding_actions=["READ"],
            governance_profile_actions=["READ"],
            environment_capabilities=["READ", "WRITE"],
            placement_policy_actions=["READ"],
            human_action_actions=["READ"],
            connector_account_permissions=["WRITE"],
        )


def test_p5_negative_29_worker_prompt_not_authority(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_authority(
            requested_actions=["WRITE"],
            work_assignment_actions=["READ"],
            executor_binding_actions=["READ"],
            governance_profile_actions=["READ"],
            environment_capabilities=["READ", "WRITE"],
            placement_policy_actions=["READ"],
            human_action_actions=["READ"],
            worker_prompt_claimed_actions=["WRITE"],
        )


def test_p5_negative_30_task_capability_beyond_workassignment(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_authority(
            requested_actions=["EXECUTE"],
            work_assignment_actions=["READ"],
            executor_binding_actions=["READ", "EXECUTE"],
            governance_profile_actions=["READ", "EXECUTE"],
            environment_capabilities=["READ", "EXECUTE"],
            placement_policy_actions=["READ", "EXECUTE"],
            human_action_actions=["READ", "EXECUTE"],
        )


def test_p5_negative_31_destructive_external_action_without_authority(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_authority(
            requested_actions=["DELETE_EXTERNAL"],
            work_assignment_actions=["READ"],
            executor_binding_actions=["READ"],
            governance_profile_actions=["READ"],
            environment_capabilities=["READ", "DELETE_EXTERNAL"],
            placement_policy_actions=["READ"],
            human_action_actions=["READ"],
        )


def test_p5_negative_32_pair_repair_revoke_not_ordinary_worker_authority(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_infrastructure_action("device_pair_begin")


def test_p5_negative_33_device_restart_not_ordinary_worker_authority(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_infrastructure_action("device_restart")


def test_p5_negative_34_restart_with_active_jobs_without_explicit_confirmation(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_infrastructure_action(
            "device_restart",
            explicit_infrastructure_authorization=True,
            active_jobs=1,
            explicit_active_job_restart_confirmation=False,
        )


def test_p5_negative_35_project_register_bind_root_widening_not_implicit(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_infrastructure_action("project_register_on_device")


def test_p5_negative_36_adapter_cannot_widen_budget_profile_protected_policy(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.validate_authority(
            requested_actions=["PROTECTED_READ"],
            work_assignment_actions=["PROTECTED_READ"],
            executor_binding_actions=["PROTECTED_READ"],
            governance_profile_actions=[],
            environment_capabilities=["PROTECTED_READ"],
            placement_policy_actions=["PROTECTED_READ"],
            human_action_actions=["PROTECTED_READ"],
        )


def test_p5_negative_37_observability_loss_cannot_relaunch_scientific_job(adapter):
    with pytest.raises(InvalidTransition):
        adapter.assert_relaunch_allowed(
            observability_lost=True,
            existing_job_may_exist=True,
            explicit_scientific_relaunch_authorization=True,
            reconciliation_terminal=False,
        )


def test_p5_negative_38_proxy_without_node_job_id_no_blind_duplicate_submit(adapter):
    obs = base_job_observation()
    obs["node_job_id"] = None
    obs["terminal"] = False
    obs["terminal_event_id"] = None
    rec = adapter.reconcile_job(
        obs,
        placement=base_placement(),
        expected_proxy_job_id="rjob-1",
        expected_argv_sha256=base_job_submission()["submitted_argv_sha256"],
    )
    assert rec == {
        "state": "UNRESOLVED_PROVENANCE",
        "may_resubmit": False,
        "execution_proven": False,
    }


def test_p5_negative_39_unknown_nonterminal_job_no_replacement_before_reconciliation(adapter):
    with pytest.raises(InvalidTransition):
        adapter.assert_relaunch_allowed(
            observability_lost=True,
            existing_job_may_exist=True,
            explicit_scientific_relaunch_authorization=True,
            reconciliation_terminal=False,
        )


def test_p5_negative_40_recovery_different_task_worktree_source_state(adapter):
    old = base_placement() | {"protected_resource_state": "FRESH"}
    new = copy.deepcopy(old)
    new["task_id"] = "task-other"
    new["worktree_ref_or_explicit_non_git_qualification"] = "worktree-other"
    with pytest.raises(InvalidTransition):
        adapter.validate_recovery(old, new)


def test_p5_negative_41_checkpoint_g2e_workassignment_executor_ref_mismatch(adapter):
    cp = base_checkpoint()
    cp["work_assignment_exact_ref"] = exact_ref("wa-other", H2)
    with pytest.raises(ValidationError):
        adapter.validate_checkpoint(
            cp, expected_refs=checkpoint_expected(), previous_protected_state="FRESH"
        )


def test_p5_negative_42_recovery_cannot_rollback_protected_resource_exposure(adapter):
    old = base_placement() | {"protected_resource_state": "EXPOSED"}
    new = copy.deepcopy(old)
    new["protected_resource_state"] = "RESERVED"
    with pytest.raises(InvalidTransition):
        adapter.validate_recovery(old, new)


def test_p5_negative_43_device_or_fingerprint_change_requires_governed_rebind(adapter):
    old = base_placement() | {"protected_resource_state": "FRESH"}
    new = copy.deepcopy(old)
    new["device_key_fingerprint_sha256"] = H4
    with pytest.raises(InvalidTransition):
        adapter.validate_recovery(old, new)


def test_p5_negative_44_operational_failure_not_scientific_fail(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_cross_boundary_action("CREATE_SCIENTIFIC_FAIL")


def test_p5_negative_45_runtime_success_not_evidence_admission(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_cross_boundary_action("ADMIT_EVIDENCE")


def test_p5_negative_46_runtime_success_not_scientific_pass(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_cross_boundary_action("CREATE_SCIENTIFIC_PASS")


def test_p5_negative_47_result_envelope_missing_exact_provenance_rejected(adapter):
    r = base_result()
    del r["work_assignment_exact_ref"]
    with pytest.raises(ValidationError):
        adapter.validate_result_envelope(r, expected=result_expected())


def test_p5_negative_48_artifact_or_log_digest_mismatch(adapter):
    with pytest.raises(ValidationError):
        adapter.validate_result_envelope(
            base_result(),
            expected=result_expected(),
            observed_digests={"artifact-1": H4},
        )


def test_p5_negative_49_raw_log_not_evidence_without_normalization_admission(adapter):
    candidate = adapter.candidate_evidence_projection(base_result())
    assert candidate["admission_state"] == "CANDIDATE"
    assert candidate["scientific_verdict"] is None


def test_p5_negative_50_result_wrong_workassignment_or_attempt(adapter):
    r = base_result()
    r["work_assignment_exact_ref"] = exact_ref("wa-other", H2)
    with pytest.raises(ValidationError):
        adapter.validate_result_envelope(r, expected=result_expected())


def test_p5_negative_51_terminal_result_not_independently_retrievable(adapter):
    r = base_result()
    r["independently_retrievable"] = False
    with pytest.raises(ValidationError):
        adapter.validate_result_envelope(r, expected=result_expected())


def test_p5_negative_52_secret_material_in_result_envelope(adapter):
    r = base_result()
    r["access_token"] = "secret"
    with pytest.raises(ValidationError):
        adapter.validate_result_envelope(r, expected=result_expected())


def test_p5_negative_53_worker_cannot_rewrite_terminal_adjudication(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_cross_boundary_action("REWRITE_TERMINAL_ADJUDICATION")


def test_p5_negative_54_pm_cannot_direct_dispatch_through_remotemcp(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_cross_boundary_action("PM_DIRECT_DISPATCH")


def test_p5_negative_55_remotemcp_cannot_create_replacement_g2e_attempt(adapter):
    with pytest.raises(AuthorityDenied):
        adapter.assert_cross_boundary_action("CREATE_REPLACEMENT_G2E_ATTEMPT")


def test_p5_negative_56_p5_qualification_no_real_project_protected_evidence_or_p6_route(adapter):
    with pytest.raises(GateBlocked):
        adapter.validate_qualification_scope(
            {
                "synthetic_only": True,
                "zero_science_only": True,
                "real_project_execution": True,
                "protected_evidence_consumption": False,
                "p6_route_import": False,
                "mission_control_refactor": False,
            }
        )
