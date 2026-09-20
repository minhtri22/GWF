# GWF — Future Node-Level Agent Orchestration Parking Lot

## 1. Purpose

This document records future architecture decisions that should influence current interfaces **without authorizing implementation now**.

It exists to prevent two opposite mistakes:

1. implementing multi-agent orchestration prematurely; or
2. designing today's interfaces so narrowly that node-level agent assignment later requires breaking GWF core contracts.

## 2. Frozen conceptual decisions

The following conceptual decisions are accepted for future compatibility.

### Decision A — Agent Pool is not synonymous with fallback

An Agent Pool worker may be the intended primary executor of a node from the start.

Examples:

- paper scout;
- GitHub/source-code scout;
- junior developer;
- test writer;
- documentation worker;
- log-analysis worker.

Fallback/reassignment is only one possible policy.

### Decision B — role precedes agent identity

Future node configuration should prefer:

```text
node → role → capability/authority requirements → agent binding
```

rather than hard-coding a vendor/model directly into every node.

### Decision C — harness agents and pool agents are different resource classes

Harness agents are valuable because of their surrounding execution system.

Pool agents are valuable because they can provide specialized, local, free, cheap, or scalable workers.

Neither class is globally superior; assignment depends on the node contract.

### Decision D — GWF remains authoritative

No agent, harness, ARC node, MCP client, or future protocol can directly redefine authoritative workflow state, scientific gates, lineage, or release completion outside GWF governance.

### Decision E — delegation must be observable

If a senior agent delegates to junior agents in the future, delegated work must remain attributable in GWF lineage.

## 3. Intended future node contract

A future node may carry fields conceptually equivalent to:

```yaml
node_id: reference.code_search
role: source_code_scout
required_capabilities:
  - code_search
  - repository_read
authority_scope: read_only
risk_class: low
scientific_sensitivity: low
privacy_requirement: public_only
binding_mode: dynamic
evidence_contract:
  - reference_registry_entries
  - retrieval_log
  - exact_repository_sha
```

This YAML is illustrative only. It is not a current schema proposal.

## 4. Example future role allocation

### Small/simple software project

```text
requirements
   ↓
junior_dev          → Agent Pool worker
   ↓
test_writer         → Agent Pool worker
   ↓
qa_reviewer         → harness or independent pool reviewer
```

A small project may require no premium harness at all if its risk/capability contract is satisfied.

### Larger software project

```text
architect / lead    → Codex or another strong harness
      ↓
implementation A    → Agent Pool junior
implementation B    → Agent Pool junior
specialized change  → harness specialist
      ↓
independent QA      → separate reviewer
```

### Research reference acquisition

```text
paper_scout         → Agent Pool worker
source_code_scout   → Agent Pool worker
standards_scout     → Agent Pool worker
      ↓
reference_curator   → stronger reviewer/harness
      ↓
literature_review   → governed synthesis
```

## 5. Routing dimensions to preserve in future design

Potential routing inputs include:

- capability;
- complexity;
- risk;
- authority;
- scientific sensitivity;
- privacy/locality;
- cost;
- latency;
- availability;
- reproducibility;
- harness requirement.

No routing algorithm is selected yet.

## 6. Items deliberately not implemented now

- agent registry;
- node-agent binding database tables;
- automatic assignment;
- ARC worker pool;
- harness adapters;
- delegation runtime;
- agent ranking;
- cost optimizer;
- fallback policy engine;
- UI for assigning agents to nodes;
- multi-agent scheduling.

## 7. Compatibility requirement for near-term work

Near-term GWF changes should avoid assumptions that would make this architecture impossible, especially:

- assuming one global agent for an entire project;
- assuming model/vendor identity is the same thing as a role;
- assuming every external executor is a fallback;
- assuming all agents share the same authority;
- assuming external session IDs are authoritative GWF IDs;
- assuming every node may dynamically change executor without provenance;
- assuming a harness can be represented only as a raw model API.

## 8. Revisit trigger

This parking lot should be reopened only when at least one of the following is true:

- Reference Acquisition requires parallel scout roles;
- a real project needs junior/senior node assignment;
- GWF begins an MCP/harness integration increment;
- an ARC Agent Pool experiment is authorized;
- a concrete cost/availability problem justifies multi-agent scheduling.

Until then, this remains design guidance, not implementation scope.
