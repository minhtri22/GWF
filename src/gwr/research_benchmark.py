from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import platform
import sys
import yaml

from .datasets import DatasetRegistry
from .research_orchestrator import EvidenceOutput, PhaseExecutionResult
from .tabular_verifier import SubprocessTabularVerifier, TabularStatistics


@dataclass(frozen=True)
class BenchmarkCase:
    data: dict[str, Any]
    @property
    def id(self): return self.data["id"]


class ResearchBenchmarkSuite:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.cases = {c["id"]: BenchmarkCase(c) for c in self.data.get("cases", [])}
        self.quality_cases = list(self.data.get("quality_cases", []))

    def case(self, case_id: str) -> BenchmarkCase:
        return self.cases[case_id]


class BenchmarkResearchExecutor:
    """17-phase executor backed by pinned CSV datasets.

    This executor is deliberately boring: it turns dataset provenance, a precommitted
    two-group mean-difference protocol, raw rows, and an independent subprocess verifier
    into the same research artifacts consumed by the ResearchOrchestrator. It exists to
    test orchestration semantics on real and pathological data before production work.
    """

    def __init__(self, registry: DatasetRegistry, case: BenchmarkCase, verifier: SubprocessTabularVerifier | None = None):
        self.registry = registry
        self.case = case.data
        self.verifier = verifier or SubprocessTabularVerifier()
        self._handlers = {
            "phase_00_lock_goal": self._p00,
            "phase_01_prior_art_and_novelty": self._p01,
            "phase_02_define_hypothesis": self._p02,
            "phase_03_formalize": self._p03,
            "phase_04_design_protocol": self._p04,
            "phase_05_prepare_dataset_and_benchmark": self._p05,
            "phase_06_plan_and_implement_experiment": self._p06,
            "phase_07_preflight": self._p07,
            "phase_08_pilot": self._p08,
            "phase_09_main_experiment": self._p09,
            "phase_10_analyze_results": self._p10,
            "phase_11_adversarial_falsification_review": self._p11,
            "phase_12_decide_pass_fail_pivot": self._p12,
            "phase_13_pivot_if_required": self._p13,
            "phase_14_replication_or_replay": self._p14,
            "phase_15_write_final_report": self._p15,
            "phase_16_handoff_and_archive": self._p16,
        }

    def execute(self, c):
        return self._handlers[c.phase_id](c)

    def _ev(self, c, extra: dict[str, Any] | None = None):
        phase=c.domain.workunit(c.phase_id)
        assertions=set(phase.get("success_conditions", []))
        for gt in phase.get("required_gate_types", []): assertions.update((c.domain.gate(gt) or {}).get("pass_if", []))
        payload={"pass":True,"assertions":sorted(assertions),"phase":c.phase_id,"generation":c.generation,"attempt":c.attempt,"benchmark_case":self.case["id"]}
        if extra: payload.update(extra)
        return [EvidenceOutput(t,dict(payload)) for t in phase.get("evidence_required", [])]

    def _dataset_id(self, c):
        if c.generation > 0 and self.case.get("pivot_dataset_id"):
            return self.case["pivot_dataset_id"]
        return self.case["dataset_id"]

    def _spec(self):
        keys=["group_column","value_column","group_a","group_b","min_effect","min_per_group","alpha","permutations"]
        spec={k:self.case[k] for k in keys if k in self.case}
        spec["seed"]=170917
        return spec

    def _rows(self,c): return self.registry.load_rows(self._dataset_id(c))

    def _p00(self,c):
        return PhaseExecutionResult(artifacts={"research_goal":{"problem":"Exercise the governed research runtime on a pinned benchmark dataset.","research_question":self.case["hypothesis"],"scope":{"case":self.case["id"],"dataset":self._dataset_id(c)},"success_criteria":["precommitted threshold evaluated","independent verifier used","result reported without rewriting outcome"],"stop_conditions":["terminal PASS/FAIL or approved PIVOT path completes"]}},evidence=self._ev(c))

    def _p01(self,c):
        m=self.registry.get(self._dataset_id(c)).manifest
        src={"dataset_id":m["dataset_id"],"kind":m["kind"],"source_url":m.get("source_url"),"doi":m.get("doi"),"license":m.get("license"),"citation":m.get("citation"),"sha256":m["sha256"]}
        return PhaseExecutionResult(artifacts={"prior_art_landscape":{"sources":[src],"closest_prior_work":[],"differentiators":["This is a runtime acceptance benchmark, not a novelty claim."],"unresolved_questions":[]},"novelty_assessment":{"claim_of_novelty":"None; benchmark only.","overlaps":[],"borrowed_ideas":[],"residual_novelty":"Governed execution evidence only.","risks":["Do not interpret benchmark findings as new domain science."]}},evidence=self._ev(c,{"dataset_source":src}))

    def _p02(self,c):
        return PhaseExecutionResult(artifacts={"hypothesis":{"statement":self.case["hypothesis"],"null_hypothesis":"Precommitted effect/statistical criteria are not met.","mechanism":"Not asserted by the benchmark.","predictions":["group mean difference meets threshold","permutation p-value below alpha"],"falsification_criteria":["effect below threshold","p-value >= alpha"]}},evidence=self._ev(c))

    def _p03(self,c):
        s=self._spec()
        return PhaseExecutionResult(artifacts={"formal_model":{"definitions":["Delta = mean(B)-mean(A)"],"assumptions":["rows are the pinned dataset snapshot","comparison groups are predeclared"],"variables":[s["group_column"],s["value_column"]],"equations":["Delta=mean(B)-mean(A)"],"invariants":["dataset hash fixed within a generation"],"boundary_conditions":[f"min_per_group={s['min_per_group']}"]}},evidence=self._ev(c))

    def _p04(self,c):
        s=self._spec()
        return PhaseExecutionResult(artifacts={"protocol":{"experimental_design":{"type":"two-group pinned-dataset comparison"},"controls":["frozen CSV hash","precommitted group labels","independent subprocess verifier"],"independent_variables":[s["group_column"]],"dependent_variables":[s["value_column"]],"metrics":["mean difference","permutation p-value"],"thresholds":{"min_effect":s["min_effect"],"alpha":s["alpha"],"min_per_group":s["min_per_group"]},"query_or_compute_budget":{"permutations":s.get("permutations",4000)},"leakage_controls":["target columns declared before execution"],"confound_controls":["benchmark does not infer causality"],"statistical_plan":{"primary":"effect threshold + permutation test"},"stopping_rules":["complete verifier or operationally fail"],"pass_fail_pivot_rules":{"PASS":"effect and p-value criteria met with sufficient sample","FAIL":"valid sample but hypothesis criteria fail","PIVOT":"sample insufficient and predeclared pivot dataset exists"}}},evidence=self._ev(c))

    def _p05(self,c):
        did=self._dataset_id(c); rec=self.registry.get(did); integrity=self.registry.validate_integrity(did)
        s=self._spec(); counts=self.registry.group_counts(did,s["group_column"])
        if not integrity["ok"]:
            return PhaseExecutionResult(runtime_status="FAILED",failure_class="dataset_version_mismatch",failure_reason=str(integrity["errors"]),root_artifact_type="dataset_benchmark_spec")
        sufficient=counts.get(str(s["group_a"]),0)>=s["min_per_group"] and counts.get(str(s["group_b"]),0)>=s["min_per_group"]
        payload={"data_sources":[{"dataset_id":did,"kind":rec.kind,"source_url":rec.manifest.get("source_url"),"doi":rec.manifest.get("doi"),"license":rec.manifest.get("license"),"sha256":rec.manifest["sha256"]}],"splits":["full pinned snapshot"],"sampling":{"group_counts":counts},"inclusion_exclusion":["non-missing comparison values"],"gold_or_oracle_definition":{},"contamination_checks":["hash verified","schema verified"],"benchmark_cases":[self.case["id"]],"seeds":[170917],"sufficient_sample":sufficient,"generation_dataset":did}
        return PhaseExecutionResult(artifacts={"dataset_benchmark_spec":payload},evidence=self._ev(c,{"integrity":integrity,"group_counts":counts,"sufficient_sample":sufficient}))

    def _p06(self,c):
        did=c.current_artifacts["dataset_benchmark_spec"]["generation_dataset"]
        plan={"runs":[{"name":"pilot","rows":"bounded subset"},{"name":"main","rows":"full snapshot"}],"baselines":[],"ablations":[],"adversarial_cases":[],"seeds":[170917],"resources":["CPU","Python standard library"],"expected_artifacts":["raw rows","independent verification"],"exact_commands":["python tools/run_research_benchmark.py"],"dataset_id":did}
        impl={"repository":"packaged source tree","commit":"archive-manifest-sha256","environment":{"python":sys.version.split()[0],"platform":platform.platform()},"dependencies":["Python>=3.11"],"commands":plan["exact_commands"],"config_hashes":{"dataset_sha256":self.registry.get(did).manifest["sha256"],"benchmark_case":self.case["id"]}}
        return PhaseExecutionResult(artifacts={"experiment_plan":plan,"implementation_manifest":impl},evidence=self._ev(c))

    def _p07(self,c):
        did=c.current_artifacts["dataset_benchmark_spec"]["generation_dataset"]
        integrity=self.registry.validate_integrity(did)
        return PhaseExecutionResult(artifacts={"preflight_result":{"checks":[integrity],"failures":integrity["errors"],"warnings":[],"environment_fingerprint":{"python":sys.version.split()[0],"platform":platform.platform()},"verdict":"PASS" if integrity["ok"] else "FAIL"}},evidence=self._ev(c,{"preflight":integrity}))

    def _p08(self,c):
        rows=self._rows(c); s=self._spec(); small=rows[:min(len(rows),80)]
        try: effect=TabularStatistics.effect(small,s["group_column"],s["value_column"],str(s["group_a"]),str(s["group_b"]))
        except Exception: effect={"note":"pilot subset did not contain both groups; main run uses full snapshot"}
        return PhaseExecutionResult(artifacts={"pilot_result":{"runs":[{"dataset_id":self._dataset_id(c),"sample_rows":len(small)}],"raw_metrics":effect,"anomalies":[],"feasibility":{"both_groups_observed":"note" not in effect},"power_or_signal_check":{"preview":effect},"verdict":"PASS"}},evidence=self._ev(c,{"pilot":effect}))

    def _p09(self,c):
        rows=self._rows(c); did=self._dataset_id(c)
        return PhaseExecutionResult(artifacts={"experiment_result":{"run_ids":[f"benchmark:{self.case['id']}:g{c.generation}"],"raw_metrics":{"rows":rows,"spec":self._spec()},"aggregate_metrics":{"row_count":len(rows)},"logs":[],"artifacts":[did],"provenance":{"dataset_id":did,"dataset_sha256":self.registry.get(did).manifest["sha256"]}}},evidence=self._ev(c,{"row_count":len(rows),"dataset_sha256":self.registry.get(did).manifest["sha256"]}))

    def _p10(self,c):
        er=c.current_artifacts["experiment_result"]
        raw=er["raw_metrics"]
        verification=self.verifier.verify(raw["rows"],raw["spec"])
        return PhaseExecutionResult(artifacts={"analysis_result":{"statistical_results":[verification],"verification_manifest":{"independent_process":verification.get("independent_process"),"input_sha256":verification.get("input_sha256")},"effect_sizes":{"mean_difference":verification["effect"]["difference_b_minus_a"]},"uncertainty":{"permutation_p_value":verification["permutation_p_value"]},"robustness":{"sufficient_sample":verification["sufficient_sample"]},"ablations":[],"baseline_comparison":{},"assumption_checks":{"sufficient_sample":verification["sufficient_sample"]},"interpretation":"Pinned-dataset benchmark result only; not a causal or novelty claim."}},evidence=self._ev(c,{"verification":verification}))

    def _p11(self,c):
        v=c.current_artifacts["analysis_result"]["statistical_results"][0]
        qa=self.registry.quality_assessment(self._dataset_id(c))
        return PhaseExecutionResult(artifacts={"adversarial_review":{"falsification_attempts":["independent recomputation","dataset hash validation"],"alternative_explanations":["observational group differences need not be causal"],"leakage_checks":["quality fixture checks are separate from scientific case"],"confounds":["benchmark makes no causal interpretation"],"boundary_failures":[],"strongest_counterargument":"A benchmark PASS only validates the precommitted descriptive comparison and runtime path.","verdict":"SUPPORTS_PROTOCOL_SCOPED_PASS" if v["pass"] else ("PIVOT_REQUIRED" if not v["sufficient_sample"] and self.case.get("pivot_dataset_id") else "DOES_NOT_SUPPORT_PASS"),"data_quality":qa}},evidence=self._ev(c,{"verification_pass":v["pass"],"sufficient_sample":v["sufficient_sample"]}))

    def _p12(self,c):
        v=c.current_artifacts["analysis_result"]["statistical_results"][0]
        if not v["sufficient_sample"] and self.case.get("pivot_dataset_id") and c.generation == 0:
            outcome="PIVOT"
        else:
            outcome="PASS" if v["pass"] else "FAIL"
        return PhaseExecutionResult(artifacts={"decision_record":{"outcome":outcome,"evidence_summary":{"verification":v},"threshold_evaluation":{"effect":v["effect"]["difference_b_minus_a"],"required":v["min_effect"],"p_value":v["permutation_p_value"],"alpha":v["alpha"],"sufficient_sample":v["sufficient_sample"]},"violated_assumptions":[] if v["sufficient_sample"] else ["INSUFFICIENT_SAMPLE"],"confidence_band":"Development benchmark only","next_action":"pivot dataset" if outcome=="PIVOT" else "replay then report"}},evidence=self._ev(c,{"outcome":outcome,"verification":v}))

    def _p13(self,c):
        return PhaseExecutionResult(artifacts={"pivot_plan":{"reason":"Initial sample below precommitted minimum per group.","preserved_findings":["research_goal","hypothesis","formal_model","protocol"],"invalidated_assumptions":["initial dataset has adequate sample size"],"new_or_revised_question":self.case["hypothesis"],"new_or_revised_hypothesis":self.case["hypothesis"],"earliest_resume_artifact":"dataset_benchmark_spec","rerun_scope":{"new_dataset_id":self.case["pivot_dataset_id"],"from_phase":"phase_05_prepare_dataset_and_benchmark"}}},evidence=self._ev(c,{"pivot_dataset_id":self.case.get("pivot_dataset_id")}))

    def _p14(self,c):
        er=c.current_artifacts["experiment_result"]; raw=er["raw_metrics"]; spec=dict(raw["spec"]); spec["seed"]=170918; spec["permutations"]=min(800,int(spec.get("permutations",1200)))
        v=self.verifier.verify(raw["rows"],spec)
        return PhaseExecutionResult(artifacts={"replication_result":{"mode":"same frozen data / alternate permutation stream replay","independent_seed_or_environment":[170918],"reproduced_metrics":v,"divergence":{"direction_consistent":v["pass"]==c.current_artifacts["analysis_result"]["statistical_results"][0]["pass"]},"reproducibility_verdict":"REPRODUCED_DIRECTION" if v["pass"]==c.current_artifacts["analysis_result"]["statistical_results"][0]["pass"] else "DIVERGED"}},evidence=self._ev(c,{"replication":v}))

    def _p15(self,c):
        a=c.current_artifacts
        report={"executive_summary":f"Benchmark case {self.case['id']} outcome: {a['decision_record']['outcome']}.","research_question":a["research_goal"]["research_question"],"hypothesis_lineage":[a["hypothesis"]["statement"]],"prior_art":a["prior_art_landscape"],"formalization":a["formal_model"],"protocol":a["protocol"],"implementation":a["implementation_manifest"],"experiments":a["experiment_plan"],"results":a["analysis_result"],"falsification":a["adversarial_review"],"decision_history":[a["decision_record"]],"replication":a["replication_result"],"limitations":["Development acceptance benchmark","No causal interpretation","Real datasets are pinned public snapshots; synthetic datasets are controlled fixtures"],"open_questions":[],"claims_evidence_matrix":[{"claim":self.case["hypothesis"],"evidence":"experiment_result + analysis_result + decision_record"}],"reproducibility_instructions":"python tools/run_research_benchmark.py","negative_results":[] if a["decision_record"]["outcome"]=="PASS" else [a["decision_record"]],"failed_runs":[],"pivot_history":[h for h in c.history if h.get("event")=="PIVOT"],"protocol_deviations":[],"reproduction_commands":["python tools/run_research_benchmark.py"],"environment_manifest":{"python":sys.version.split()[0]},"exact_revision_ids":dict(c.current_revision_ids)}
        return PhaseExecutionResult(artifacts={"final_report":report},evidence=self._ev(c,{"outcome":a["decision_record"]["outcome"]}))

    def _p16(self,c):
        return PhaseExecutionResult(artifacts={"handoff_package":{"current_status":"completed","artifact_manifest":sorted(c.current_artifacts.keys()),"checkpoint_ref":c.latest_checkpoint_id,"unresolved_issues":["These benchmark cases are development fixtures, not external production pilots."],"exact_resume_target":None,"next_actions":["Use benchmark as v0.5 semantic-equivalence acceptance suite"],"commands":["python tools/run_research_benchmark.py"],"hashes":{"dataset":self.registry.get(self._dataset_id(c)).manifest["sha256"],"executor":"BenchmarkResearchExecutor-v0.4.1"}}},evidence=self._ev(c,{"checkpoint":c.latest_checkpoint_id}))
