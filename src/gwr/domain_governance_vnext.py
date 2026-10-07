from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import AuthorityDenied, InvalidTransition, NotFound, ValidationError
from .governance_vnext import GovernanceProfileRef, VNextGovernanceService
from .utils import content_hash, parse_json, utcnow


@dataclass(frozen=True)
class DomainGovernanceProfile:
    canonical_key: str
    ref: GovernanceProfileRef
    definition: dict[str, Any]


class DomainGovernanceProfilePackage:
    """Exact-hash domain-owned governance profile package."""

    def __init__(self, data: dict[str, Any], *, source_path: str | None = None):
        self.data = data
        self.source_path = source_path
        self.domain_id = str(data.get("domain_id") or "")
        self.profile_order = list(data.get("profile_order") or [])
        self.profiles = dict(data.get("profiles") or {})
        self.transition_topology = data.get("transition_topology")
        self.later_operational_incidents = data.get("later_operational_incidents")
        self._validate()

    @classmethod
    def load(cls, source: str | Path) -> "DomainGovernanceProfilePackage":
        path = Path(source)
        return cls(json.loads(path.read_text(encoding="utf-8")), source_path=str(path))

    def _validate(self) -> None:
        if self.data.get("schema_id") != "GWF-DOMAIN-GOVERNANCE-PROFILES-v1":
            raise ValidationError("Unsupported governance profile package schema")
        if not self.domain_id or not self.profiles:
            raise ValidationError("Governance profile package missing domain_id/profiles")
        if self.transition_topology != "ACYCLIC_FORWARD_ONLY":
            raise ValidationError("P2 governance profile package must be ACYCLIC_FORWARD_ONLY")
        if set(self.profile_order) != set(self.profiles):
            raise ValidationError("profile_order must exactly enumerate package profiles")

        by_identity: dict[tuple[str, str, str, str], str] = {}
        for key, entry in self.profiles.items():
            if entry.get("canonical_key") != key:
                raise ValidationError("Canonical profile key mismatch", details={"profile": key})
            definition = entry.get("definition")
            if not isinstance(definition, dict):
                raise ValidationError("Profile definition must be an object", details={"profile": key})
            if definition.get("domain_id") != self.domain_id:
                raise ValidationError("Cross-domain profile definition", details={"profile": key})
            expected = entry.get("expected_profile_hash")
            actual = content_hash(definition)
            if expected != actual:
                raise ValidationError(
                    "Governance profile hash mismatch",
                    details={"profile": key, "expected": expected, "actual": actual},
                )
            identity = (
                definition["domain_id"],
                definition["profile_id"],
                definition["version"],
                expected,
            )
            if identity in by_identity:
                raise ValidationError("Duplicate governance profile identity")
            by_identity[identity] = key

            policy = definition.get("policy") or {}
            allowed_sections = {
                "authority_overlay",
                "budget_overlay",
                "autonomy_policy",
                "mutation_policy",
                "protected_resource_policy",
                "lineage_policy",
                "approval_policy",
                "retry_recovery_policy",
                "claim_permission_policy",
            }
            unknown = sorted(set(policy) - allowed_sections)
            if unknown:
                raise ValidationError("Unknown governance policy section", details={"profile": key, "sections": unknown})

        graph: dict[str, list[str]] = {key: [] for key in self.profiles}
        order_index = {key: i for i, key in enumerate(self.profile_order)}
        for key, entry in self.profiles.items():
            for edge in entry["definition"].get("transition_edges") or []:
                target = edge.get("target_profile_ref") or {}
                ident = (
                    target.get("domain_id"),
                    target.get("profile_id"),
                    target.get("profile_version"),
                    target.get("profile_hash"),
                )
                target_key = by_identity.get(ident)
                if not target_key:
                    raise ValidationError("Transition target does not resolve exactly", details={"profile": key})
                if target_key == key or order_index[target_key] <= order_index[key]:
                    raise ValidationError(
                        "In-place governance transition must be strictly forward",
                        details={"from": key, "to": target_key},
                    )
                graph[key].append(target_key)

        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(node: str) -> None:
            if node in visiting:
                raise ValidationError("Governance profile transition cycle detected")
            if node in visited:
                return
            visiting.add(node)
            for target in graph[node]:
                dfs(target)
            visiting.remove(node)
            visited.add(node)

        for key in graph:
            dfs(key)

    def get(self, canonical_key: str) -> DomainGovernanceProfile:
        entry = self.profiles.get(canonical_key)
        if not entry:
            raise NotFound("Governance profile not found")
        d = entry["definition"]
        return DomainGovernanceProfile(
            canonical_key=canonical_key,
            ref=GovernanceProfileRef(
                d["domain_id"],
                d["profile_id"],
                d["version"],
                entry["expected_profile_hash"],
            ),
            definition=d,
        )

    def key_for_ref(self, ref: GovernanceProfileRef | dict[str, Any]) -> str:
        data = ref.to_dict() if isinstance(ref, GovernanceProfileRef) else dict(ref)
        for key, entry in self.profiles.items():
            d = entry["definition"]
            if (
                d["domain_id"] == data.get("domain_id")
                and d["profile_id"] == data.get("profile_id")
                and d["version"] == data.get("profile_version")
                and entry["expected_profile_hash"] == data.get("profile_hash")
            ):
                return key
        raise NotFound("GovernanceProfileRef does not belong to package")

    def transition_edge(self, from_key: str, to_key: str) -> dict[str, Any]:
        source = self.get(from_key)
        target = self.get(to_key)
        for edge in source.definition.get("transition_edges") or []:
            if edge.get("target_profile_ref") == target.ref.to_dict():
                return edge
        raise InvalidTransition(
            "No exact in-place governance transition edge",
            details={"from": from_key, "to": to_key},
        )


class DomainGovernanceProfileService:
    """P2 enforcement layer built on the P1 provider-neutral governance kernel."""

    RESEARCH_CLAIM_ORDER = {
        "OPERATIONAL_OBSERVATION_ONLY": 0,
        "EXPLORATORY_FINDING": 1,
        "MEASUREMENT_RESULT": 2,
        "CONFIRMATORY_CANDIDATE": 3,
    }
    SOFTWARE_CLAIM_ORDER = {
        "OPERATIONAL_OBSERVATION_ONLY": 0,
        "IMPLEMENTATION_RESULT": 1,
        "QUALIFIED_CANDIDATE": 2,
        "RELEASE_CANDIDATE": 3,
    }
    RESEARCH_FORMAL_VERDICTS = {
        "PASS", "FAIL", "UNRESOLVED", "INVALID", "SPENT",
        "SCIENTIFIC_PASS", "SCIENTIFIC_FAIL", "FORMAL_SCIENTIFIC_VERDICT",
    }
    SOFTWARE_FORMAL_ACCEPTANCE = {
        "RELEASE_ACCEPTED", "PRODUCTION_APPROVED", "FORMAL_RELEASE_ACCEPTANCE",
    }

    def __init__(
        self,
        db,
        governance,
        vnext_governance: VNextGovernanceService,
        packages: list[DomainGovernanceProfilePackage],
    ):
        self.db = db
        self.governance = governance
        self.vnext = vnext_governance
        self.packages = {p.domain_id: p for p in packages}
        if len(self.packages) != len(packages):
            raise ValidationError("Duplicate domain governance profile package")

    @classmethod
    def from_runtime(cls, runtime, package_paths: list[str | Path]) -> "DomainGovernanceProfileService":
        return cls(
            runtime.db,
            runtime.governance,
            runtime.vnext_governance,
            [DomainGovernanceProfilePackage.load(path) for path in package_paths],
        )

    def register_package(self, domain_id: str) -> dict[str, GovernanceProfileRef]:
        package = self._package(domain_id)
        out: dict[str, GovernanceProfileRef] = {}
        # Terminal-first registration is not required by DB, but exact target hashes
        # are already frozen in package payloads.
        for key in reversed(package.profile_order):
            profile = package.get(key)
            d = profile.definition
            ref = self.vnext.register_profile_definition(
                d["domain_id"],
                d["profile_id"],
                d["version"],
                d["policy"],
                d.get("transition_edges") or [],
            )
            if ref.to_dict() != profile.ref.to_dict():
                raise ValidationError("Registered profile ref differs from frozen package", details={"profile": key})
            out[key] = ref
        return out

    def bind_initial_profile(self, project_id: str, canonical_key: str, actor_id: str) -> GovernanceProfileRef:
        package = self._package_for_key(canonical_key)
        if package.profile_order[0] != canonical_key:
            raise InvalidTransition("Initial profile must be the domain TRIAGE/bootstrap profile")
        try:
            self.vnext.current_profile_ref(project_id)
        except NotFound:
            pass
        else:
            raise InvalidTransition("Project already has an active GovernanceProfileRef")
        self.governance.authorize(
            actor_id,
            "PROPOSE",
            {"project_id": project_id, "resource_type": "GovernanceProfile"},
        )
        profile = package.get(canonical_key)
        self.vnext.resolve_profile_ref(profile.ref)
        self.vnext.bind_project_profile(project_id, profile.ref, actor_id=actor_id)
        return profile.ref

    def active_profile(self, project_id: str) -> DomainGovernanceProfile:
        ref = self.vnext.current_profile_ref(project_id)
        package = self._package(ref.domain_id)
        return package.get(package.key_for_ref(ref))

    def propose_transition(
        self,
        project_id: str,
        target_key: str,
        proposer_actor_id: str,
        satisfied_condition_codes: list[str],
        *,
        subject_ref: dict[str, Any] | None = None,
        evidence_refs: list[dict[str, Any]] | None = None,
        reason_codes: list[str] | None = None,
    ) -> str:
        active = self.active_profile(project_id)
        package = self._package(active.ref.domain_id)
        target = package.get(target_key)
        package.transition_edge(active.canonical_key, target_key)  # fail-closed and no backward edge

        condition_evidence = [
            {"kind": "GOVERNANCE_TRANSITION_CONDITION", "condition_code": code, "satisfied": True}
            for code in sorted(set(satisfied_condition_codes))
        ]
        return self.vnext.propose_transition(
            project_id,
            subject_ref or {"kind": "project", "id": project_id},
            active.ref,
            target.ref,
            proposer_actor_id,
            list(reason_codes or ["DOMAIN_PROFILE_TRANSITION"]),
            evidence_refs=condition_evidence + list(evidence_refs or []),
        )

    def evaluate_transition(self, transition_id: str) -> dict[str, Any]:
        row = self.db.one(
            "SELECT * FROM governance_transition_proposals WHERE transition_id=?",
            (transition_id,),
        )
        if not row:
            raise NotFound("GovernanceTransitionProposal not found")
        source_ref = parse_json(row["from_profile_ref"], {})
        target_ref = parse_json(row["to_profile_ref"], {})
        package = self._package(source_ref.get("domain_id"))
        if target_ref.get("domain_id") != package.domain_id:
            raise InvalidTransition("Cross-domain governance transition forbidden")

        from_key = package.key_for_ref(source_ref)
        to_key = package.key_for_ref(target_ref)
        edge = package.transition_edge(from_key, to_key)

        satisfied = {
            item.get("condition_code")
            for item in parse_json(row["evidence_refs"], [])
            if item.get("kind") == "GOVERNANCE_TRANSITION_CONDITION" and item.get("satisfied") is True
        }
        required = set(edge.get("condition_codes") or [])
        missing = sorted(required - satisfied)
        if missing:
            raise InvalidTransition(
                "Governance transition readiness conditions are incomplete",
                details={"missing_condition_codes": missing},
            )

        disposition = edge.get("disposition")
        if disposition not in {
            "AUTO_ALLOWED",
            "HUMAN_APPROVAL_REQUIRED",
            "FORBIDDEN",
            "SUCCESSOR_REQUIRED",
        }:
            raise ValidationError("Invalid governance transition disposition")

        har_id = None
        if disposition == "HUMAN_APPROVAL_REQUIRED":
            frozen_payload = {
                "transition_id": transition_id,
                "transition_payload_hash": row["frozen_payload_hash"],
                "from_profile_ref": source_ref,
                "to_profile_ref": target_ref,
                "required_condition_codes": sorted(required),
            }
            har_id = self.vnext.create_human_action_request(
                row["project_id"],
                edge.get("required_human_action_kind") or "GOVERNANCE_PROFILE_TRANSITION",
                {"kind": "GovernanceTransitionProposal", "id": transition_id},
                frozen_payload,
                "APPROVE",
                {"actor_type": "HUMAN"},
                ["DOMAIN_PROFILE_TRANSITION"],
                proposal_ref={"kind": "GovernanceTransitionProposal", "id": transition_id},
            )

        self.db.conn.execute(
            "UPDATE governance_transition_proposals "
            "SET state='EVALUATED',disposition=?,human_action_request_id=?,evaluated_at=? "
            "WHERE transition_id=?",
            (disposition, har_id, utcnow(), transition_id),
        )
        self.db.conn.commit()
        return {"disposition": disposition, "human_action_request_id": har_id}

    def activate_transition(self, transition_id: str, actor_id: str) -> GovernanceProfileRef:
        row = self.db.one(
            "SELECT * FROM governance_transition_proposals WHERE transition_id=?",
            (transition_id,),
        )
        if not row:
            raise NotFound("GovernanceTransitionProposal not found")
        if row["state"] != "EVALUATED":
            raise InvalidTransition("Governance transition must be evaluated before activation")
        disposition = row["disposition"]
        if disposition in {"FORBIDDEN", "SUCCESSOR_REQUIRED"}:
            raise InvalidTransition(
                "Governance transition cannot activate in-place",
                details={"disposition": disposition},
            )
        if disposition == "HUMAN_APPROVAL_REQUIRED":
            har_id = row["human_action_request_id"]
            har = self.db.one(
                "SELECT * FROM human_action_requests WHERE human_action_request_id=?",
                (har_id,),
            )
            if not har or har["state"] != "RESOLVED":
                raise AuthorityDenied("Required HumanActionRequest is not resolved")
            resolution = parse_json(har["resolution_ref"], {})
            approval_id = resolution.get("approval_id")
            approval = self.db.one("SELECT * FROM approvals WHERE approval_id=?", (approval_id,))
            if not approval or approval["decision"] != "APPROVED":
                raise AuthorityDenied("HumanActionRequest resolution lacks authoritative approval")
            approver = self.db.one("SELECT * FROM actors WHERE actor_id=?", (approval["approver_actor_id"],))
            if not approver or approver["actor_type"] != "HUMAN":
                raise AuthorityDenied("Governance profile elevation requires HUMAN approval")
            proposal = self.db.one("SELECT * FROM proposals WHERE proposal_id=?", (approval["proposal_id"],))
            if (
                not proposal
                or proposal["payload_hash"] != har["frozen_payload_hash"]
                or approval["proposal_hash"] != har["frozen_payload_hash"]
            ):
                raise AuthorityDenied("Human approval is not bound to the exact HumanActionRequest payload")
        elif disposition != "AUTO_ALLOWED":
            raise InvalidTransition("Unknown transition disposition")

        target_ref = GovernanceProfileRef(**parse_json(row["to_profile_ref"], {}))
        # Re-check current source to prevent stale transition activation.
        current = self.vnext.current_profile_ref(row["project_id"])
        if current.to_dict() != parse_json(row["from_profile_ref"], {}):
            raise InvalidTransition("Stale governance transition source profile")

        self.vnext.bind_project_profile(row["project_id"], target_ref, actor_id=actor_id)
        self.db.conn.execute(
            "UPDATE governance_transition_proposals SET state='RESOLVED',resolved_at=? WHERE transition_id=?",
            (utcnow(), transition_id),
        )
        self.db.conn.commit()
        return target_ref

    def authorize_domain_action(
        self,
        project_id: str,
        action: str,
        *,
        protected_resource_class: str | None = None,
        protected_access_context: dict[str, bool] | None = None,
    ) -> bool:
        profile = self.active_profile(project_id)
        policy = profile.definition["policy"]
        authority = policy.get("authority_overlay") or {}
        deny = set(authority.get("deny_domain_actions") or [])
        allow = set(authority.get("allow_domain_actions") or [])
        if action in deny:
            raise AuthorityDenied("Domain action denied by active GovernanceProfile", details={"action": action})
        if action not in allow:
            raise AuthorityDenied("Domain action absent from active GovernanceProfile ALLOW set", details={"action": action})

        if protected_resource_class is not None:
            protected = policy.get("protected_resource_policy") or {}
            forbidden = set(protected.get("forbidden_classes") or [])
            allowed = set(protected.get("allowed_classes") or [])
            if protected_resource_class in forbidden or (allowed and protected_resource_class not in allowed):
                raise AuthorityDenied(
                    "Protected resource class denied by active GovernanceProfile",
                    details={"resource_class": protected_resource_class},
                )
            if protected_resource_class == "PROTECTED_CONFIRMATORY":
                ctx = protected_access_context or {}
                required = {"resource_identity_bound", "consumption_budget_bound", "human_authorized"}
                missing = sorted(k for k in required if ctx.get(k) is not True)
                if missing:
                    raise AuthorityDenied(
                        "Protected confirmatory access context incomplete",
                        details={"missing": missing},
                    )
        return True

    def authorize_claim(self, project_id: str, claim_class: str) -> bool:
        profile = self.active_profile(project_id)
        policy = profile.definition["policy"].get("claim_permission_policy") or {}
        ceiling = policy.get("max_candidate_claim_class")

        if profile.ref.domain_id == "research.full-cycle":
            if claim_class in self.RESEARCH_FORMAL_VERDICTS:
                raise AuthorityDenied("GovernanceProfile cannot emit formal scientific verdict")
            order = self.RESEARCH_CLAIM_ORDER
        elif profile.ref.domain_id == "software.delivery":
            if claim_class in self.SOFTWARE_FORMAL_ACCEPTANCE:
                raise AuthorityDenied("GovernanceProfile cannot emit formal release acceptance")
            order = self.SOFTWARE_CLAIM_ORDER
        else:
            raise ValidationError("Unsupported domain for P2 claim policy")

        if claim_class not in order or ceiling not in order or order[claim_class] > order[ceiling]:
            raise AuthorityDenied(
                "Claim class exceeds active GovernanceProfile ceiling",
                details={"claim_class": claim_class, "ceiling": ceiling},
            )
        return True

    def require_successor_for_material_change(self, project_id: str, change_code: str) -> None:
        profile = self.active_profile(project_id)
        successor_codes = {
            "research.measurement": {
                "MATERIAL_METRIC_CHANGE",
                "MATERIAL_INSTRUMENT_CHANGE",
                "MATERIAL_PROTOCOL_CHANGE",
            },
            "research.confirmatory": {
                "MUTATE_HYPOTHESIS",
                "MUTATE_CONFIRMATORY_METRIC",
                "MUTATE_CONFIRMATORY_THRESHOLD",
                "MUTATE_CONFIRMATORY_COHORT",
                "MUTATE_CONFIRMATORY_SEED_NAMESPACE",
                "MATERIAL_EXECUTOR_ENVIRONMENT_CHANGE",
            },
            "software.qualification": {
                "MATERIAL_SCOPE_EXPANSION",
                "MATERIAL_PRODUCT_SEMANTIC_CHANGE",
            },
            "software.release": {
                "MUTATE_PRODUCT_CODE",
                "MATERIAL_SCOPE_EXPANSION",
                "MATERIAL_PRODUCT_SEMANTIC_CHANGE",
            },
        }
        if change_code in successor_codes.get(profile.canonical_key, set()):
            raise InvalidTransition(
                "Material change requires governed successor; in-place backward rescue is forbidden",
                details={
                    "disposition": "SUCCESSOR_REQUIRED",
                    "active_profile": profile.canonical_key,
                    "change_code": change_code,
                },
            )

    def validate_candidate_identity_change(
        self,
        project_id: str,
        *,
        old_candidate_sha: str,
        new_candidate_sha: str,
        prior_qa_reused: bool,
        within_frozen_scope: bool,
    ) -> bool:
        profile = self.active_profile(project_id)
        if profile.canonical_key != "software.qualification":
            raise InvalidTransition("Candidate identity change guard applies only in software.qualification")
        if new_candidate_sha == old_candidate_sha:
            return True
        if not within_frozen_scope:
            raise InvalidTransition(
                "Material scope change requires successor development cycle",
                details={"disposition": "SUCCESSOR_REQUIRED"},
            )
        if prior_qa_reused:
            raise AuthorityDenied("Changed candidate SHA invalidates prior candidate QA")
        return True

    def assert_external_effect_retry_safe(
        self,
        project_id: str,
        *,
        idempotency_proven: bool,
        effect_ledger_reconciled: bool,
    ) -> bool:
        profile = self.active_profile(project_id)
        if profile.canonical_key != "software.release":
            raise InvalidTransition("External release-effect retry guard applies only in software.release")
        if not idempotency_proven or not effect_ledger_reconciled:
            raise AuthorityDenied("External effect retry is not proven safe")
        return True

    def _package(self, domain_id: str) -> DomainGovernanceProfilePackage:
        package = self.packages.get(domain_id)
        if not package:
            raise NotFound("No P2 governance profile package for domain")
        return package

    def _package_for_key(self, canonical_key: str) -> DomainGovernanceProfilePackage:
        matches = [p for p in self.packages.values() if canonical_key in p.profiles]
        if len(matches) != 1:
            raise NotFound("Canonical profile key does not resolve uniquely")
        return matches[0]
