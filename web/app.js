"use strict";

const THEME_KEY = "gwr-ui-theme";
const SIDEBAR_KEY = "gwr-ui-sidebar";
const state = {
  bootstrap: null,
  me: null,
  health: null,
  home: null,
  homeError: null,
  homeLoading: false,
  projects: null,
  projectsError: null,
  projectsLoading: false,
  access: null,
  accessError: null,
  accessLoading: false,
  accessMutation: false,
  operationsRuns: null,
  operationsRunsError: null,
  operationsRunsLoading: false,
  operationsRunsFilters: { text: "", tenant: "", workspace: "", project: "", status: "" },
  operationsApprovals: null,
  operationsApprovalsError: null,
  operationsApprovalsLoading: false,
  selectedApprovalId: null,
  operationsAudit: null,
  operationsAuditError: null,
  operationsAuditLoading: false,
  operationsAuditFilters: {
    text: "", tenant: "", workspace: "", project: "", actor: "", action: "", resource: "", from: "", to: ""
  },
  projectsFilters: {
    text: "",
    lifecycle: "",
    tenant: "",
    workspace: "",
    domain: "",
    activity: "",
    attention: "",
  },
};
const DEFAULT_ROUTE = "/app/system/diagnostics";
const ROUTE_COPY = {
  home: "Home is owned by BPS-M01. No KPI, run, project or activity data is fabricated outside its authoritative projection.",
  projects: "Projects and access management are owned by BPS-M02. No project entities or lifecycle actions are fabricated here.",
  access: "Tenant, workspace, project membership and session access administration is owned by BPS-M02.",
  operations: "Global Runs, Approvals, Audit and Runtime unlock in BPS-M03. This foundation route contains no synthetic operational data.",
  packages: "Research package registry and usage unlock in BPS-M06. No package or project-usage records are fabricated here.",
  github: "GitHub product surfaces unlock in BPS-M07. No repository binding or ChangeSet action is fabricated here.",
  settings: "System settings unlock with BPS-M07. Foundation theme/sidebar preferences remain available from the shell controls.",
  "shared-library": "Shared Library remains planned and blocked by its own backend governance program.",
  "reference-acquisition": "Reference Acquisition remains planned and blocked until its backend program is qualified.",
  agents: "Agents / Codex remains planned and blocked until its interoperability prerequisites are qualified."
};

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[ch]));

const ICON_PATHS = {
  home: '<path d="M3 10.8 12 3l9 7.8v9.2a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1z"/>',
  projects: '<path d="M3 7.5h7l2 2H21v9.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 7.5V5a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v2.5"/>',
  operations: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21h-4v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H3v-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V3h4v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.1v4H21a1.7 1.7 0 0 0-1.6 1z"/>',
  packages: '<path d="M9 3h6"/><path d="M10 3v5.2L5.2 17a2.7 2.7 0 0 0 2.4 4h8.8a2.7 2.7 0 0 0 2.4-4L14 8.2V3"/><path d="M8 15h8"/>',
  "reference-acquisition": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/><path d="M11 8v6M8 11h6"/>',
  "shared-library": '<path d="M4 4h5v16H4zM10 4h5v16h-5zM16 6h4v14h-4z"/>',
  agents: '<circle cx="12" cy="8" r="3"/><path d="M5 20c.8-4 3.1-6 7-6s6.2 2 7 6"/><path d="M18 4h3v3"/>',
  github: '<path d="M8 6h8M8 12h8M8 18h8"/><circle cx="5" cy="6" r="1.5"/><circle cx="19" cy="12" r="1.5"/><circle cx="5" cy="18" r="1.5"/>',
  access: '<circle cx="9" cy="8" r="3"/><path d="M3.5 20c.6-3.7 2.5-5.5 5.5-5.5s4.9 1.8 5.5 5.5"/><path d="M16 11h5M18.5 8.5v5"/>',
  diagnostics: '<path d="M12 3 4.5 6v5.2c0 4.7 3.2 8 7.5 9.8 4.3-1.8 7.5-5.1 7.5-9.8V6z"/><path d="m9 12 2 2 4-4"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 15.2A8.5 8.5 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2z"/>',
  system: '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
  panel: '<path d="M9 4 4 9l5 5M15 4l5 5-5 5"/>',
  shield: '<path d="M12 3 4.5 6v5.2c0 4.7 3.2 8 7.5 9.8 4.3-1.8 7.5-5.1 7.5-9.8V6z"/>'
};

function iconSvg(name, className = "icon") {
  const path = ICON_PATHS[name] || ICON_PATHS.panel;
  return '<svg class="' + className + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + path + "</svg>";
}

async function api(path, options = {}) {
  const request = { credentials: "same-origin", ...options };
  request.headers = { ...(options.headers || {}) };
  if (request.body && typeof request.body !== "string") {
    request.headers["Content-Type"] = "application/json";
    request.body = JSON.stringify(request.body);
  }
  const response = await fetch(path, request);
  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { raw: text }; }
  if (!response.ok) {
    const error = new Error(body?.detail || body?.error?.message || ("HTTP " + response.status));
    error.status = response.status;
    error.body = body;
    throw error;
  }
  return body;
}

function storedTheme() {
  const value = localStorage.getItem(THEME_KEY);
  return ["system", "light", "dark"].includes(value) ? value : "system";
}

function applyTheme(value) {
  const theme = ["system", "light", "dark"].includes(value) ? value : "system";
  document.documentElement.dataset.theme = theme;
  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    button.classList.toggle("active", button.dataset.themeOption === theme);
    button.setAttribute("aria-pressed", button.dataset.themeOption === theme ? "true" : "false");
  });
  localStorage.setItem(THEME_KEY, theme);
}

function applySidebar(value) {
  const collapsed = value === "collapsed";
  $("#sidebar").classList.toggle("collapsed", collapsed);
  $("#appView").classList.toggle("sidebar-collapsed", collapsed);
  $("#sidebarToggle").innerHTML = iconSvg(collapsed ? "panel" : "panel", "icon");
  $("#sidebarToggle").classList.toggle("is-collapsed", collapsed);
  $("#sidebarToggle").setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
  $("#sidebarToggle").setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
  localStorage.setItem(SIDEBAR_KEY, collapsed ? "collapsed" : "expanded");
}

function stateMeta(item) {
  if (item.state === "LIVE_FOUNDATION") return { cls: "live", label: "Live foundation" };
  if (item.state === "LIVE_MODULE") return { cls: "live", label: "Live" };
  if (item.state === "PLANNED_BLOCKED") return { cls: "planned", label: "Planned" };
  if (item.state === "SKELETON_LOCKED") return { cls: "locked", label: "Locked" };
  return { cls: "locked", label: item.state || "Locked" };
}

function statePill(item) {
  const meta = stateMeta(item);
  return '<span class="state-pill ' + meta.cls + '">' + meta.label + "</span>";
}

function displayLabel(item) {
  if (item.id === "packages") return "Research";
  if (item.id === "diagnostics") return "System";
  return item.label;
}

function displaySubtitle(item) {
  if (item.id === "packages") return "Packages · " + item.slice;
  if (item.id === "diagnostics") return "Diagnostics · " + item.slice;
  return item.slice;
}

function navGroups(capabilities) {
  const byId = Object.fromEntries(capabilities.map((item) => [item.id, item]));
  return [
    ["WORKSPACE", ["home", "projects"]],
    ["OPERATIONS", ["operations"]],
    ["RESEARCH", ["packages", "reference-acquisition"]],
    ["SHARED", ["shared-library"]],
    ["AI", ["agents"]],
    ["SYSTEM", ["github", "access", "diagnostics", "settings"]],
  ].map(([group, ids]) => [group, ids.map((id) => byId[id]).filter(Boolean)]);
}

function renderNav() {
  const groups = navGroups(state.bootstrap.capabilities);
  $("#mainNav").innerHTML = groups.map(([group, items]) => {
    const rows = items.map((item) => {
      const meta = stateMeta(item);
      const title = displayLabel(item) + " — " + meta.label + " · " + item.slice;
      const routeClass = item.state === "LIVE_FOUNDATION" || item.state === "LIVE_MODULE" ? "" : " locked-route";
      return '<button type="button" class="nav-item' + routeClass +
        '" data-capability="' + esc(item.id) + '" data-route="' + esc(item.route) +
        '" aria-label="' + esc(title) + '" title="' + esc(title) + '">' +
        '<span class="nav-icon">' + iconSvg(item.id, "icon") + '</span>' +
        '<span class="nav-label"><strong>' + esc(displayLabel(item)) + '</strong><small>' + esc(displaySubtitle(item)) + '</small></span>' +
        statePill(item) + "</button>";
    }).join("");
    return '<section class="nav-group"><p>' + esc(group) + "</p>" + rows + "</section>";
  }).join("");
}

function capabilityById(id) {
  return state.bootstrap.capabilities.find((item) => item.id === id);
}

function normalizedRoute(pathname = window.location.pathname) {
  const trimmed = pathname.replace(/\/+$/, "");
  return trimmed || "/app";
}

function capabilityForRoute(pathname = window.location.pathname) {
  const path = normalizedRoute(pathname);
  if (path === "/app") return capabilityById("diagnostics");
  const exact = state.bootstrap.capabilities.find((item) => item.route === path);
  if (exact) return exact;
  if (path.startsWith("/app/operations/")) return capabilityById("operations");
  return null;
}

function setActiveNav(capabilityId) {
  document.querySelectorAll("#mainNav .nav-item").forEach((button) => {
    const active = button.dataset.capability === capabilityId;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
}

function renderLockedRoute(item) {
  const meta = stateMeta(item);
  $("#homeRouteView").hidden = true;
  $("#projectsRouteView").hidden = true;
  $("#accessRouteView").hidden = true;
  $("#operationsRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = true;
  $("#lockedRouteView").hidden = false;
  $("#routeStateIcon").innerHTML = iconSvg(item.id, "icon");
  $("#routeStateShield").innerHTML = iconSvg("shield", "icon");
  $("#routeStateTitle").textContent = displayLabel(item);
  $("#routeStateDescription").textContent = ROUTE_COPY[item.id] || "This product module is not yet unlocked.";
  $("#routeStatePath").textContent = item.route;
  $("#routeStateOwner").textContent = item.slice;
  $("#routeStateMaturity").textContent = meta.label;
  $("#routeStateBadge").className = "state-pill " + meta.cls;
  $("#routeStateBadge").textContent = meta.label;
}

function renderDiagnosticsRoute(item) {
  $("#homeRouteView").hidden = true;
  $("#projectsRouteView").hidden = true;
  $("#accessRouteView").hidden = true;
  $("#operationsRouteView").hidden = true;
  $("#lockedRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = false;
  document.title = "GWF — System Diagnostics";
}


function formatHomeTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function formatDuration(startedAt) {
  const start = new Date(startedAt).getTime();
  if (!Number.isFinite(start)) return "—";
  const seconds = Math.max(0, Math.floor((Date.now() - start) / 1000));
  if (seconds < 60) return seconds + "s";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + "m";
  const hours = Math.floor(minutes / 60);
  return hours + "h " + (minutes % 60) + "m";
}

function homeEmpty(message, colspan = 1) {
  return '<tr><td class="empty-cell" colspan="' + colspan + '">' + esc(message) + "</td></tr>";
}

function renderAttentionIndicator() {
  const count = state.home?.kpis?.attention_required;
  $("#notificationButton").innerHTML = iconSvg("bell", "icon") +
    '<span id="attentionCount" class="attention-count">' + esc(count ?? "—") + "</span>";
  $("#notificationButton").title = count == null ?
    "Attention count unavailable — open Home" :
    ("Attention required: " + count + " · open Home attention");
}

function renderHomeError(message) {
  $("#homeStateBanner").hidden = false;
  $("#homeStateBanner").className = "home-state-banner error";
  $("#homeStateBanner").textContent = "Home data unavailable — " + message;
  $("#homeKpis").innerHTML = "";
  $("#executingProjectsBody").innerHTML = homeEmpty("Executing projects unavailable.", 8);
  $("#liveRunsBody").innerHTML = homeEmpty("Live runs unavailable.", 6);
  $("#homeAttentionList").innerHTML = '<div class="feed-empty">Attention data unavailable.</div>';
  $("#recentActivityList").innerHTML = '<div class="feed-empty">Recent activity unavailable.</div>';
}

function renderHomeSummary() {
  const summary = state.home;
  if (!summary) {
    renderHomeError(state.homeError || "No authoritative summary returned.");
    return;
  }

  const complete = summary.query_status === "COMPLETE";
  $("#homeStateBanner").hidden = complete;
  if (!complete) {
    $("#homeStateBanner").className = "home-state-banner warn";
    $("#homeStateBanner").textContent = "Home projection is not complete. Zero values are not treated as authoritative.";
  }
  $("#homeScopeBadge").textContent = summary.scope?.label || "Authorized scope";
  $("#homeGeneratedAt").textContent = formatHomeTime(summary.generated_at);
  $("#homeBuildSha").textContent = summary.build_sha || "unknown";

  const k = summary.kpis || {};
  const cards = [
    ["Total Projects", k.total_projects, "Authorized scope"],
    ["Lifecycle Active", k.lifecycle_active, "Lifecycle = ACTIVE"],
    ["Executing Now", k.executing_now, "Authoritative execution"],
    ["Running Runs", k.running_runs, "runtime_status = RUNNING"],
    ["Pending Approvals", k.pending_approvals, "PENDING_APPROVAL"],
    ["Attention Required", k.attention_required, "Unresolved records"],
    ["Core Health", k.core_health || "UNKNOWN", "Categorical readiness"],
  ];
  $("#homeKpis").innerHTML = cards.map(([label, value, note]) => {
    const danger = label === "Attention Required" && Number(value) > 0;
    const health = label === "Core Health";
    const cls = danger ? " attention" : (health ? " health-" + String(value).toLowerCase() : "");
    return '<article class="home-kpi' + cls + '"><span>' + esc(label) + '</span><strong>' +
      esc(value ?? "—") + '</strong><small>' + esc(note) + "</small></article>";
  }).join("");

  const projects = summary.executing_projects || [];
  $("#executingProjectsCount").textContent = projects.length;
  $("#executingProjectsBody").innerHTML = projects.length ? projects.map((p) => {
    const domain = p.domain || {};
    const domainText = domain.revision_id ?
      (domain.domain_id + " · " + domain.revision_id) :
      ((domain.domain_id || "—") + " · unpinned");
    const phase = p.phase_label || "—";
    const phaseIds = [p.orchestration_id, p.phase_execution_id].filter(Boolean).join(" · ");
    return "<tr>" +
      '<td><strong>' + esc(p.project_name) + '</strong><code>' + esc(p.project_id) + "</code></td>" +
      '<td><span class="data-state">' + esc(p.lifecycle) + '</span><small>' + esc(p.execution_activity) + "</small></td>" +
      '<td><span>' + esc(domainText) + "</span></td>" +
      '<td><span>' + esc(phase) + '</span><code>' + esc(phaseIds || "—") + "</code></td>" +
      '<td><code>' + esc(p.current_actor || "SYSTEM") + "</code></td>" +
      '<td><code>' + esc(p.running_run_id || "—") + "</code></td>" +
      '<td><span>' + esc(formatHomeTime(p.latest_event_at)) + "</span></td>" +
      '<td><strong class="' + (Number(p.attention_count) > 0 ? "attention-text" : "") + '">' + esc(p.attention_count ?? 0) + "</strong></td>" +
      "</tr>";
  }).join("") : homeEmpty("No projects are executing in the current authorized scope.", 8);

  const runs = summary.live_runs || [];
  $("#liveRunsCount").textContent = runs.length;
  $("#liveRunsBody").innerHTML = runs.length ? runs.map((run) =>
    "<tr>" +
      '<td><code>' + esc(run.run_id) + '</code><small class="run-status">' + esc(run.status) + "</small></td>" +
      '<td><strong>' + esc(run.project_name) + '</strong><code>' + esc(run.project_id) + "</code></td>" +
      '<td><span>' + esc(run.workunit_type || "—") + '</span><small>' + esc(run.phase_label || "—") + "</small></td>" +
      '<td><span>' + esc(formatHomeTime(run.started_at)) + '</span><small>' + esc(formatDuration(run.started_at)) + "</small></td>" +
      '<td><code>' + esc(run.actor || "SYSTEM") + "</code></td>" +
      '<td><span>' + esc(run.latest_event_action || "—") + '</span><small>' + esc(formatHomeTime(run.latest_event_at)) + "</small></td>" +
      "</tr>"
  ).join("") : homeEmpty("No RUNNING execution runs.", 6);

  const attention = summary.attention || [];
  $("#homeAttentionCount").textContent = attention.length;
  $("#homeAttentionList").innerHTML = attention.length ? attention.map((item) =>
    '<div class="feed-item attention-item"><div><strong>' + esc(item.kind) + '</strong><span>' +
    esc(item.project_name || "System") + '</span></div><p>' + esc(item.label || item.record_id) +
    '</p><code>' + esc(item.record_id) + '</code><time>' + esc(formatHomeTime(item.created_at)) + "</time></div>"
  ).join("") : '<div class="feed-empty">No authoritative attention items.</div>';

  const activity = summary.recent_activity || [];
  $("#recentActivityList").innerHTML = activity.length ? activity.map((item) =>
    '<div class="feed-item"><div><strong>' + esc(item.action) + '</strong><span>' +
    esc(item.project_name || item.project_id) + '</span></div><p>' +
    esc(item.resource_type + " · " + item.resource_id) + '</p><code>' +
    esc(item.actor_id || "SYSTEM") + '</code><time>' + esc(formatHomeTime(item.timestamp)) + "</time></div>"
  ).join("") : '<div class="feed-empty">No authoritative activity in this scope yet.</div>';

  renderAttentionIndicator();
}

async function refreshHomeSummary(render = true) {
  if (state.homeLoading) return;
  state.homeLoading = true;
  state.homeError = null;
  if (render) {
    $("#homeStateBanner").hidden = false;
    $("#homeStateBanner").className = "home-state-banner loading";
    $("#homeStateBanner").textContent = "Loading authoritative Home summary…";
  }
  try {
    state.home = await api("/browser/home-summary");
  } catch (error) {
    state.home = null;
    state.homeError = error.message;
    if (error.status === 401) {
      showLogin();
      return;
    }
  } finally {
    state.homeLoading = false;
  }
  renderAttentionIndicator();
  if (render && !$("#homeRouteView").hidden) {
    if (state.home) renderHomeSummary();
    else renderHomeError(state.homeError || "Unknown error");
  }
}

function renderHomeRoute(item) {
  $("#lockedRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = true;
  $("#projectsRouteView").hidden = true;
  $("#accessRouteView").hidden = true;
  $("#operationsRouteView").hidden = true;
  $("#homeRouteView").hidden = false;
  document.title = "GWF — Home";
  if (state.home) renderHomeSummary();
  else if (state.homeError) renderHomeError(state.homeError);
  else void refreshHomeSummary(true);
}

function projectDomainFilterKey(project) {
  const domain = project.domain || {};
  if (domain.revision_id) return "revision:" + domain.revision_id;
  if (domain.domain_id) return "unbound:" + domain.domain_id;
  return "unbound";
}

function projectDomainLabel(project) {
  const domain = project.domain || {};
  if (domain.bound) {
    const name = domain.domain_name || domain.domain_id || "Domain";
    const version = domain.semantic_version || (domain.revision_number != null ? ("r" + domain.revision_number) : "");
    return [name, version].filter(Boolean).join(" · ");
  }
  return "Unpinned · " + (domain.domain_id || "No domain identity");
}

function setProjectsSelectOptions(selector, baseLabel, options, selectedValue) {
  const select = $(selector);
  const rows = ['<option value="">' + esc(baseLabel) + "</option>"];
  for (const option of options) {
    rows.push('<option value="' + esc(option.value) + '">' + esc(option.label) + "</option>");
  }
  select.innerHTML = rows.join("");
  select.value = selectedValue || "";
  if (select.value !== (selectedValue || "")) {
    select.value = "";
  }
}

function populateProjectsFilterOptions() {
  const projects = state.projects?.projects || [];
  const tenantMap = new Map();
  const workspaceMap = new Map();
  const domainMap = new Map();

  for (const project of projects) {
    const scope = project.scope || {};
    if (scope.tenant_id) {
      tenantMap.set(scope.tenant_id, (scope.tenant_name || "Tenant") + " · " + scope.tenant_id);
    }
    if (scope.workspace_id) {
      workspaceMap.set(scope.workspace_id, (scope.workspace_name || "Workspace") + " · " + scope.workspace_id);
    }
    const key = projectDomainFilterKey(project);
    domainMap.set(key, projectDomainLabel(project));
  }

  const sorted = (map) => Array.from(map, ([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label));

  setProjectsSelectOptions("#projectsTenantFilter", "All tenants", sorted(tenantMap), state.projectsFilters.tenant);
  setProjectsSelectOptions("#projectsWorkspaceFilter", "All workspaces", sorted(workspaceMap), state.projectsFilters.workspace);
  setProjectsSelectOptions("#projectsDomainFilter", "All domains", sorted(domainMap), state.projectsFilters.domain);
}

function filteredProjects() {
  const projects = state.projects?.projects || [];
  const f = state.projectsFilters;
  const needle = f.text.trim().toLowerCase();

  return projects.filter((project) => {
    const scope = project.scope || {};
    if (needle && !String(project.name || "").toLowerCase().includes(needle) &&
        !String(project.project_id || "").toLowerCase().includes(needle)) return false;
    if (f.lifecycle && project.lifecycle !== f.lifecycle) return false;
    if (f.tenant && scope.tenant_id !== f.tenant) return false;
    if (f.workspace && scope.workspace_id !== f.workspace) return false;
    if (f.domain && projectDomainFilterKey(project) !== f.domain) return false;
    if (f.activity && project.execution_activity !== f.activity) return false;
    if (f.attention === "required" && Number(project.attention_required || 0) < 1) return false;
    if (f.attention === "clear" && Number(project.attention_required || 0) !== 0) return false;
    return true;
  });
}

function renderProjectsRows() {
  if (!state.projects) return;
  const all = state.projects.projects || [];
  const projects = filteredProjects();
  $("#projectsVisibleCount").textContent = projects.length;

  if (!all.length) {
    $("#projectsTableBody").innerHTML = homeEmpty("No projects are available in the current authorized scope.", 8);
    return;
  }
  if (!projects.length) {
    $("#projectsTableBody").innerHTML = homeEmpty("No projects match the current page filters.", 8);
    return;
  }

  $("#projectsTableBody").innerHTML = projects.map((project) => {
    const scope = project.scope || {};
    const domain = project.domain || {};
    const boundDomain = domain.bound === true;
    const domainTitle = boundDomain ? (domain.domain_name || domain.domain_id || "Pinned domain") : "Unpinned";
    const domainExact = boundDomain ?
      [domain.package_id, domain.revision_id].filter(Boolean).join(" · ") :
      (domain.domain_id || "No pinned revision");
    const domainVersion = boundDomain ?
      [domain.semantic_version, domain.revision_number != null ? ("r" + domain.revision_number) : null]
        .filter(Boolean).join(" · ") :
      "No floating/latest revision implied";
    const latest = project.latest_event || null;
    const attention = Number(project.attention_required || 0);
    const activityClass = project.execution_activity === "EXECUTING" ? "run-status" : "";
    return "<tr>" +
      '<td><strong>' + esc(project.name) + '</strong><code>' + esc(project.project_id) + "</code></td>" +
      '<td><span>' + esc(scope.tenant_name || "Tenant") + '</span><code>' + esc(scope.tenant_id || "—") +
      '</code><small>' + esc(scope.workspace_name || "Workspace") + '</small><code>' + esc(scope.workspace_id || "—") + "</code></td>" +
      '<td><span class="data-state">' + esc(project.lifecycle || "Unavailable") +
      '</span><small class="' + activityClass + '">' + esc(project.execution_activity || "Unavailable") + "</small></td>" +
      '<td><span>' + esc(domainTitle) + '</span><code>' + esc(domainExact) +
      '</code><small>' + esc(domainVersion) + "</small></td>" +
      '<td><strong>' + esc(project.running_runs ?? 0) + ' running</strong><small>' +
      esc(project.active_jobs ?? 0) + " active jobs</small></td>" +
      '<td><strong>' + esc(project.pending_approvals ?? 0) + ' pending</strong><small class="' +
      (attention > 0 ? "attention-text" : "") + '">' + esc(attention) + " attention</small></td>" +
      '<td><span>' + esc(latest?.action || "—") + '</span><small>' + esc(formatHomeTime(latest?.timestamp)) + "</small></td>" +
      '<td><span>' + esc(formatHomeTime(project.created_at)) + "</span></td>" +
      "</tr>";
  }).join("");
}

function renderProjectsError(message) {
  $("#projectsStateBanner").hidden = false;
  $("#projectsStateBanner").className = "home-state-banner error";
  $("#projectsStateBanner").textContent = "Projects data unavailable — " + message;
  $("#projectsTableBody").innerHTML = homeEmpty("Projects index unavailable.", 8);
  $("#projectsVisibleCount").textContent = "—";
  $("#projectsGeneratedAt").textContent = "—";
  $("#projectsBuildSha").textContent = "—";
}

function renderProjectsIndex() {
  const summary = state.projects;
  if (!summary) {
    renderProjectsError(state.projectsError || "No authoritative Projects projection returned.");
    return;
  }

  const complete = summary.query_status === "COMPLETE";
  $("#projectsStateBanner").hidden = complete;
  if (!complete) {
    $("#projectsStateBanner").className = "home-state-banner warn";
    $("#projectsStateBanner").textContent = "Projects projection is partial. Missing authoritative fields are not treated as zero or inferred values.";
  }

  $("#projectsScopeBadge").textContent = summary.scope?.label || "Authorized scope";
  $("#projectsGeneratedAt").textContent = formatHomeTime(summary.generated_at);
  $("#projectsBuildSha").textContent = summary.build_sha || "unknown";
  populateProjectsFilterOptions();
  renderProjectsRows();
}

async function refreshProjectsIndex(render = true) {
  if (state.projectsLoading) return;
  state.projectsLoading = true;
  state.projectsError = null;
  if (render) {
    $("#projectsStateBanner").hidden = false;
    $("#projectsStateBanner").className = "home-state-banner loading";
    $("#projectsStateBanner").textContent = "Loading authorized Projects projection…";
  }
  try {
    state.projects = await api("/browser/projects-index");
  } catch (error) {
    state.projects = null;
    state.projectsError = error.message;
    if (error.status === 401) {
      showLogin();
      return;
    }
  } finally {
    state.projectsLoading = false;
  }

  if (render && !$("#projectsRouteView").hidden) {
    if (state.projects) renderProjectsIndex();
    else renderProjectsError(state.projectsError || "Unknown error");
  }
}

function renderProjectsRoute(item) {
  $("#homeRouteView").hidden = true;
  $("#accessRouteView").hidden = true;
  $("#operationsRouteView").hidden = true;
  $("#lockedRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = true;
  $("#projectsRouteView").hidden = false;
  document.title = "GWF — Projects";
  if (state.projects) renderProjectsIndex();
  else if (state.projectsError) renderProjectsError(state.projectsError);
  else void refreshProjectsIndex(true);
}

function confirmGovernedAction({ title, action, target, scope, consequence }) {
  const dialog = $("#governedActionDialog");
  $("#governedActionTitle").textContent = title;
  $("#governedActionName").textContent = action;
  $("#governedActionTarget").textContent = target;
  $("#governedActionScope").textContent = scope;
  $("#governedActionConsequence").textContent = consequence;
  return new Promise((resolve) => {
    const close = () => {
      dialog.removeEventListener("close", close);
      resolve(dialog.returnValue === "confirm");
    };
    dialog.addEventListener("close", close);
    dialog.showModal();
  });
}

function accessScopeRows(kind) {
  if (!state.access) return [];
  if (kind === "tenant") return state.access.tenants || [];
  if (kind === "workspace") return state.access.workspaces || [];
  return state.access.projects || [];
}

function accessScopeId(kind, row) {
  if (kind === "tenant") return row.tenant_id;
  if (kind === "workspace") return row.workspace_id;
  return row.project_id;
}

function accessScopeLabel(kind, row) {
  if (kind === "tenant") return (row.name || "Tenant") + " · " + row.tenant_id;
  if (kind === "workspace") return (row.workspace_name || "Workspace") + " · " + row.workspace_id;
  return (row.project_name || "Project") + " · " + row.project_id;
}

function accessSelectedScope() {
  const kind = $("#accessScopeKind").value;
  const id = $("#accessScopeTarget").value;
  return accessScopeRows(kind).find((row) => accessScopeId(kind, row) === id) || null;
}

function renderAccessMembers() {
  const selected = accessSelectedScope();
  const root = $("#accessCurrentMembers");
  if (!selected) {
    root.innerHTML = '<div class="feed-empty">No manageable scope selected.</div>';
    return;
  }
  const members = selected.members || [];
  root.innerHTML = members.length ? members.map((member) =>
    '<div class="access-member-row"><code>' + esc(member.actor_id) + '</code><strong>' +
    esc(member.role) + '</strong><span>' + esc(member.status) + '</span><small>' +
    esc(formatHomeTime(member.created_at)) + "</small></div>"
  ).join("") : '<div class="feed-empty">No direct membership records in this scope.</div>';
}

function populateAccessControls() {
  const summary = state.access;
  if (!summary) return;

  const workspaceTenants = (summary.tenants || []).filter((row) => row.can_manage_workspaces);
  $("#createWorkspaceTenant").innerHTML = workspaceTenants.length ?
    workspaceTenants.map((row) =>
      '<option value="' + esc(row.tenant_id) + '">' + esc(row.name + " · " + row.tenant_id) + "</option>"
    ).join("") :
    '<option value="">No manageable tenant</option>';

  const kind = $("#accessScopeKind").value;
  const scopes = accessScopeRows(kind).filter((row) => row.can_manage_members);
  const prior = $("#accessScopeTarget").value;
  $("#accessScopeTarget").innerHTML = scopes.length ?
    scopes.map((row) =>
      '<option value="' + esc(accessScopeId(kind, row)) + '">' + esc(accessScopeLabel(kind, row)) + "</option>"
    ).join("") :
    '<option value="">No manageable scope</option>';
  if (scopes.some((row) => accessScopeId(kind, row) === prior)) {
    $("#accessScopeTarget").value = prior;
  }

  const roles = summary.roles?.[kind] || [];
  $("#accessMemberRole").innerHTML = roles.map((role) =>
    '<option value="' + esc(role) + '">' + esc(role) + "</option>"
  ).join("");
  renderAccessMembers();
}

function renderAccessError(message) {
  $("#accessStateBanner").hidden = false;
  $("#accessStateBanner").className = "home-state-banner error";
  $("#accessStateBanner").textContent = "Access data unavailable — " + message;
  $("#accessTenantBody").innerHTML = homeEmpty("Tenant access unavailable.", 4);
  $("#accessWorkspaceBody").innerHTML = homeEmpty("Workspace access unavailable.", 4);
  $("#accessProjectBody").innerHTML = homeEmpty("Project access unavailable.", 4);
  $("#accessCurrentMembers").innerHTML = '<div class="feed-empty">Membership data unavailable.</div>';
}

function renderAccessSummary() {
  const summary = state.access;
  if (!summary) {
    renderAccessError(state.accessError || "No authoritative Access projection returned.");
    return;
  }

  $("#accessStateBanner").hidden = true;
  const session = summary.session || state.me || {};
  $("#accessPrincipal").textContent = session.principal_id || summary.actor?.principal_id || "—";
  $("#accessActorId").textContent = session.actor_id || summary.actor?.actor_id || "—";
  $("#accessAuthMethod").textContent = session.auth_method || state.me?.auth_method || "—";
  $("#accessExpiry").textContent = "Expires " + formatHomeTime(session.expires_at || state.me?.expires_at);
  $("#accessScopeCounts").textContent =
    (summary.tenants?.length || 0) + " · " +
    (summary.workspaces?.length || 0) + " · " +
    (summary.projects?.length || 0);
  $("#accessGeneratedAt").textContent = formatHomeTime(summary.generated_at);
  $("#accessBuildSha").textContent = summary.build_sha || "unknown";

  const tenants = summary.tenants || [];
  $("#accessTenantCount").textContent = tenants.length;
  $("#accessTenantBody").innerHTML = tenants.length ? tenants.map((row) =>
    "<tr>" +
      '<td><strong>' + esc(row.name) + '</strong><code>' + esc(row.tenant_id) + "</code></td>" +
      '<td><strong>' + esc(row.actor_role || "—") + '</strong><small>' + esc(row.actor_membership_status || "—") + "</small></td>" +
      '<td><span>' + esc(row.can_manage_members ? "Manage members" : "View") + '</span><small>' +
      esc(row.can_manage_workspaces ? "Create workspaces" : "No workspace mutation") + "</small></td>" +
      '<td><span>' + esc(formatHomeTime(row.created_at)) + '</span><code>' + esc(row.created_by_actor_id || "—") + "</code></td>" +
    "</tr>"
  ).join("") : homeEmpty("No tenant memberships are visible.", 4);

  const workspaces = summary.workspaces || [];
  $("#accessWorkspaceCount").textContent = workspaces.length;
  $("#accessWorkspaceBody").innerHTML = workspaces.length ? workspaces.map((row) =>
    "<tr>" +
      '<td><strong>' + esc(row.workspace_name) + '</strong><code>' + esc(row.workspace_id) + "</code></td>" +
      '<td><span>' + esc(row.tenant_name || "Tenant") + '</span><code>' + esc(row.tenant_id) + "</code></td>" +
      '<td><strong>' + esc(row.actor_role || "—") + '</strong><small>' + esc(row.role_source || "—") + "</small></td>" +
      '<td><span>' + esc(row.can_manage_members ? "Manage members" : "View") + '</span><small>' +
      esc(row.can_manage_projects ? "Create projects" : "No project mutation") + "</small></td>" +
    "</tr>"
  ).join("") : homeEmpty("No workspaces are visible.", 4);

  const projects = summary.projects || [];
  $("#accessProjectCount").textContent = projects.length;
  $("#accessProjectBody").innerHTML = projects.length ? projects.map((row) =>
    "<tr>" +
      '<td><strong>' + esc(row.project_name) + '</strong><code>' + esc(row.project_id) + "</code></td>" +
      '<td><span>' + esc(row.tenant_name || "Tenant") + '</span><small>' + esc(row.workspace_name || "Workspace") +
      '</small><code>' + esc(row.tenant_id + " · " + row.workspace_id) + "</code></td>" +
      '<td><strong>' + esc(row.actor_role || "—") + '</strong><small>' + esc(row.role_source || "—") + "</small></td>" +
      '<td><span>' + esc(row.can_manage_members ? "Manage members" : "View") + "</span></td>" +
    "</tr>"
  ).join("") : homeEmpty("No projects are visible.", 4);

  populateAccessControls();
}

async function refreshAccessSummary(render = true) {
  if (state.accessLoading) return;
  state.accessLoading = true;
  state.accessError = null;
  if (render) {
    $("#accessStateBanner").hidden = false;
    $("#accessStateBanner").className = "home-state-banner loading";
    $("#accessStateBanner").textContent = "Loading authoritative Access projection…";
  }
  try {
    state.access = await api("/browser/access-summary");
  } catch (error) {
    state.access = null;
    state.accessError = error.message;
    if (error.status === 401) {
      showLogin();
      return;
    }
  } finally {
    state.accessLoading = false;
  }
  if (render && !$("#accessRouteView").hidden) {
    if (state.access) renderAccessSummary();
    else renderAccessError(state.accessError || "Unknown error");
  }
}

async function performAccessMutation(path, options) {
  if (state.accessMutation) return;
  state.accessMutation = true;
  $("#accessStateBanner").hidden = false;
  $("#accessStateBanner").className = "home-state-banner loading";
  $("#accessStateBanner").textContent = "Applying authoritative Access change…";
  try {
    await api(path, options);
    state.me = await api("/browser/auth/me");
    renderIdentity();
    state.home = null;
    state.homeError = null;
    state.projects = null;
    state.projectsError = null;
    await refreshAccessSummary(false);
    renderAccessSummary();
    $("#accessStateBanner").hidden = false;
    $("#accessStateBanner").className = "home-state-banner";
    $("#accessStateBanner").textContent = "Authoritative Access state refreshed.";
  } catch (error) {
    if (error.status === 401) {
      showLogin();
      return;
    }
    $("#accessStateBanner").hidden = false;
    $("#accessStateBanner").className = "home-state-banner error";
    $("#accessStateBanner").textContent = "Access change failed — " + error.message;
  } finally {
    state.accessMutation = false;
  }
}

function renderAccessRoute(item) {
  $("#homeRouteView").hidden = true;
  $("#projectsRouteView").hidden = true;
  $("#lockedRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = true;
  $("#operationsRouteView").hidden = true;
  $("#accessRouteView").hidden = false;
  document.title = "GWF — Access";
  if (state.access) renderAccessSummary();
  else if (state.accessError) renderAccessError(state.accessError);
  else void refreshAccessSummary(true);
}

function operationsIdentityDetails(values) {
  const ids = values || [];
  if (!ids.length) return '<span class="identity-none">0</span>';
  return '<details class="identity-details"><summary>' + esc(ids.length) + '</summary>' +
    ids.map((id) => '<code>' + esc(id) + '</code>').join("") + "</details>";
}

function setOperationsSelect(selector, label, map, selected) {
  const options = Array.from(map, ([value, text]) => ({ value, text }))
    .sort((a, b) => a.text.localeCompare(b.text));
  const node = $(selector);
  node.innerHTML = '<option value="">' + esc(label) + "</option>" +
    options.map((item) => '<option value="' + esc(item.value) + '">' + esc(item.text) + "</option>").join("");
  node.value = selected || "";
  if (node.value !== (selected || "")) node.value = "";
}

function populateOperationsRunFilters() {
  const runs = state.operationsRuns?.runs || [];
  const tenants = new Map(), workspaces = new Map(), projects = new Map(), statuses = new Map();
  for (const run of runs) {
    const scope = run.scope || {};
    if (scope.tenant_id) tenants.set(scope.tenant_id, (scope.tenant_name || "Tenant") + " · " + scope.tenant_id);
    if (scope.workspace_id) workspaces.set(scope.workspace_id, (scope.workspace_name || "Workspace") + " · " + scope.workspace_id);
    projects.set(run.project_id, (run.project_name || "Project") + " · " + run.project_id);
    if (run.runtime_status) statuses.set(run.runtime_status, run.runtime_status);
  }
  const f = state.operationsRunsFilters;
  setOperationsSelect("#operationsRunsTenantFilter", "All tenants", tenants, f.tenant);
  setOperationsSelect("#operationsRunsWorkspaceFilter", "All workspaces", workspaces, f.workspace);
  setOperationsSelect("#operationsRunsProjectFilter", "All projects", projects, f.project);
  setOperationsSelect("#operationsRunsStatusFilter", "All statuses", statuses, f.status);
}

function filteredOperationsRuns() {
  const f = state.operationsRunsFilters;
  const needle = f.text.trim().toLowerCase();
  return (state.operationsRuns?.runs || []).filter((run) => {
    const scope = run.scope || {};
    if (needle && ![
      run.run_id, run.project_id, run.project_name, run.workunit_id, run.workunit_type
    ].some((value) => String(value || "").toLowerCase().includes(needle))) return false;
    if (f.tenant && scope.tenant_id !== f.tenant) return false;
    if (f.workspace && scope.workspace_id !== f.workspace) return false;
    if (f.project && run.project_id !== f.project) return false;
    if (f.status && run.runtime_status !== f.status) return false;
    return true;
  });
}

function formatRunDuration(startedAt, finishedAt) {
  const start = new Date(startedAt).getTime();
  const end = finishedAt ? new Date(finishedAt).getTime() : Date.now();
  if (!Number.isFinite(start) || !Number.isFinite(end)) return "—";
  const seconds = Math.max(0, Math.floor((end - start) / 1000));
  if (seconds < 60) return seconds + "s";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + "m";
  const hours = Math.floor(minutes / 60);
  return hours + "h " + (minutes % 60) + "m";
}

function renderOperationsRunsRows() {
  const all = state.operationsRuns?.runs || [];
  const runs = filteredOperationsRuns();
  $("#operationsRunsVisibleCount").textContent = runs.length;
  if (!all.length) {
    $("#operationsRunsBody").innerHTML = homeEmpty("No runs exist in the current authorized scope.", 7);
    return;
  }
  if (!runs.length) {
    $("#operationsRunsBody").innerHTML = homeEmpty("No runs match the current page filters.", 7);
    return;
  }
  $("#operationsRunsBody").innerHTML = runs.map((run) => {
    const scope = run.scope || {};
    const phase = run.phase || {};
    const latest = run.latest_event || null;
    return "<tr>" +
      '<td><code>' + esc(run.run_id) + '</code><small>attempt ' + esc(run.attempt_number) + "</small></td>" +
      '<td><strong>' + esc(run.project_name) + '</strong><code>' + esc(run.project_id) +
      '</code><small>' + esc((scope.tenant_name || "Tenant") + " / " + (scope.workspace_name || "Workspace")) +
      '</small><code>' + esc((scope.tenant_id || "—") + " · " + (scope.workspace_id || "—")) + "</code></td>" +
      '<td><strong>' + esc(run.workunit_type || "—") + '</strong><code>' + esc(run.workunit_id) +
      '</code><small>' + esc(phase.phase_id || "No linked phase") + '</small><code>' +
      esc([phase.orchestration_id, phase.phase_execution_id].filter(Boolean).join(" · ") || "—") + "</code></td>" +
      '<td><strong class="' + (run.runtime_status === "RUNNING" ? "run-status" : "") + '">' + esc(run.runtime_status) +
      '</strong><small>' + esc(formatHomeTime(run.started_at)) + '</small><small>' +
      esc((run.finished_at ? "finished " + formatHomeTime(run.finished_at) : "running") + " · " +
      formatRunDuration(run.started_at, run.finished_at)) + "</small></td>" +
      '<td><code>' + esc(run.executor_actor_id || "SYSTEM") + '</code><small>correlation</small><code>' +
      esc(run.correlation_id || "—") + "</code></td>" +
      '<td><span>Inputs</span>' + operationsIdentityDetails(run.input_revision_ids) +
      '<span>Outputs</span>' + operationsIdentityDetails(run.produced_revision_ids) +
      '<span>Evidence</span>' + operationsIdentityDetails(run.evidence_ids) + "</td>" +
      '<td><strong>' + esc(latest?.action || "—") + '</strong><code>' + esc(latest?.event_id || "—") +
      '</code><small>' + esc(formatHomeTime(latest?.timestamp)) + "</small></td>" +
    "</tr>";
  }).join("");
}

function renderOperationsRunsError(message) {
  $("#operationsRunsStateBanner").hidden = false;
  $("#operationsRunsStateBanner").className = "home-state-banner error";
  $("#operationsRunsStateBanner").textContent = "Runs data unavailable — " + message;
  $("#operationsRunsBody").innerHTML = homeEmpty("Runs index unavailable.", 7);
  $("#operationsRunsVisibleCount").textContent = "—";
  $("#operationsRunsGeneratedAt").textContent = "—";
  $("#operationsRunsBuildSha").textContent = "—";
}

function renderOperationsRuns() {
  const summary = state.operationsRuns;
  if (!summary) {
    renderOperationsRunsError(state.operationsRunsError || "No authoritative Runs projection returned.");
    return;
  }
  const complete = summary.query_status === "COMPLETE";
  $("#operationsRunsStateBanner").hidden = complete;
  if (!complete) {
    $("#operationsRunsStateBanner").className = "home-state-banner warn";
    $("#operationsRunsStateBanner").textContent = "Runs projection is partial. Missing authoritative fields are not inferred.";
  }
  $("#operationsRunsScope").textContent = summary.scope?.label || "Authorized scope";
  $("#operationsRunsGeneratedAt").textContent = formatHomeTime(summary.generated_at);
  $("#operationsRunsBuildSha").textContent = summary.build_sha || "unknown";
  populateOperationsRunFilters();
  renderOperationsRunsRows();
}

async function refreshOperationsRuns(render = true) {
  if (state.operationsRunsLoading) return;
  state.operationsRunsLoading = true;
  state.operationsRunsError = null;
  if (render) {
    $("#operationsRunsStateBanner").hidden = false;
    $("#operationsRunsStateBanner").className = "home-state-banner loading";
    $("#operationsRunsStateBanner").textContent = "Loading authorized Runs projection…";
  }
  try {
    state.operationsRuns = await api("/browser/operations/runs");
  } catch (error) {
    state.operationsRuns = null;
    state.operationsRunsError = error.message;
    if (error.status === 401) {
      showLogin();
      return;
    }
  } finally {
    state.operationsRunsLoading = false;
  }
  if (render && !$("#operationsRunsView").hidden) {
    if (state.operationsRuns) renderOperationsRuns();
    else renderOperationsRunsError(state.operationsRunsError || "Unknown error");
  }
}

function populateOperationsAuditFilters() {
  const events = state.operationsAudit?.events || [];
  const tenants = new Map(), workspaces = new Map(), projects = new Map();
  const actors = new Map(), actions = new Map(), resources = new Map();
  for (const event of events) {
    const scope = event.scope || {};
    if (scope.tenant_id) tenants.set(scope.tenant_id, (scope.tenant_name || "Tenant") + " · " + scope.tenant_id);
    if (scope.workspace_id) workspaces.set(scope.workspace_id, (scope.workspace_name || "Workspace") + " · " + scope.workspace_id);
    projects.set(event.project_id, (event.project_name || "Project") + " · " + event.project_id);
    if (event.actor_id) actors.set(event.actor_id, event.actor_id);
    if (event.action) actions.set(event.action, event.action);
    if (event.resource_type) resources.set(event.resource_type, event.resource_type);
  }
  const f = state.operationsAuditFilters;
  setOperationsSelect("#operationsAuditTenantFilter", "All tenants", tenants, f.tenant);
  setOperationsSelect("#operationsAuditWorkspaceFilter", "All workspaces", workspaces, f.workspace);
  setOperationsSelect("#operationsAuditProjectFilter", "All projects", projects, f.project);
  setOperationsSelect("#operationsAuditActorFilter", "All actors", actors, f.actor);
  setOperationsSelect("#operationsAuditActionFilter", "All actions", actions, f.action);
  setOperationsSelect("#operationsAuditResourceFilter", "All resource types", resources, f.resource);
}

function filteredOperationsAudit() {
  const f = state.operationsAuditFilters;
  const needle = f.text.trim().toLowerCase();
  const fromMs = f.from ? new Date(f.from).getTime() : null;
  const toMs = f.to ? new Date(f.to).getTime() : null;
  return (state.operationsAudit?.events || []).filter((event) => {
    const scope = event.scope || {};
    if (needle && ![
      event.event_id, event.project_id, event.project_name, event.actor_id,
      event.action, event.resource_type, event.resource_id, event.proposal_id,
      event.approval_id, event.run_id, event.decision_id, event.correlation_id,
      event.reason_code
    ].some((value) => String(value || "").toLowerCase().includes(needle))) return false;
    if (f.tenant && scope.tenant_id !== f.tenant) return false;
    if (f.workspace && scope.workspace_id !== f.workspace) return false;
    if (f.project && event.project_id !== f.project) return false;
    if (f.actor && event.actor_id !== f.actor) return false;
    if (f.action && event.action !== f.action) return false;
    if (f.resource && event.resource_type !== f.resource) return false;
    const timestamp = new Date(event.timestamp).getTime();
    if (fromMs != null && Number.isFinite(fromMs) && timestamp < fromMs) return false;
    if (toMs != null && Number.isFinite(toMs) && timestamp > toMs) return false;
    return true;
  });
}

function linkedAuditIdentities(event) {
  const pairs = [
    ["proposal", event.proposal_id], ["approval", event.approval_id],
    ["run", event.run_id], ["decision", event.decision_id],
    ["correlation", event.correlation_id],
  ].filter(([, value]) => value);
  return pairs.length ? pairs.map(([label, value]) =>
    '<span>' + esc(label) + '</span><code>' + esc(value) + "</code>"
  ).join("") : '<span class="identity-none">No linked identity</span>';
}

function renderOperationsAuditRows() {
  const all = state.operationsAudit?.events || [];
  const events = filteredOperationsAudit();
  $("#operationsAuditVisibleCount").textContent = events.length;
  if (!all.length) {
    $("#operationsAuditBody").innerHTML = homeEmpty("No audit events exist in the current authorized scope.", 8);
    return;
  }
  if (!events.length) {
    $("#operationsAuditBody").innerHTML = homeEmpty("No audit events match the current page filters.", 8);
    return;
  }
  $("#operationsAuditBody").innerHTML = events.map((event) => {
    const scope = event.scope || {};
    return "<tr>" +
      '<td><code>' + esc(event.event_id) + "</code></td>" +
      '<td><strong>' + esc(event.project_name || "Project") + '</strong><code>' + esc(event.project_id) +
      '</code><small>' + esc((scope.tenant_name || "Tenant") + " / " + (scope.workspace_name || "Workspace")) +
      '</small><code>' + esc((scope.tenant_id || "—") + " · " + (scope.workspace_id || "—")) + "</code></td>" +
      '<td><code>' + esc(event.actor_id) + '</code><strong>' + esc(event.action) + "</strong></td>" +
      '<td><strong>' + esc(event.resource_type) + '</strong><code>' + esc(event.resource_id) + "</code></td>" +
      '<td class="audit-links">' + linkedAuditIdentities(event) + "</td>" +
      '<td><code>' + esc(event.reason_code) + "</code></td>" +
      '<td><span>before</span><code>' + esc(event.before_version || "—") + '</code><span>after</span><code>' +
      esc(event.after_version || "—") + '</code><span>metadata</span><code>' + esc(event.metadata_hash || "—") + "</code></td>" +
      '<td><span>' + esc(formatHomeTime(event.timestamp)) + "</span></td>" +
    "</tr>";
  }).join("");
}

function renderOperationsAudit() {
  const summary = state.operationsAudit;
  if (!summary) {
    $("#operationsAuditStateBanner").hidden = false;
    $("#operationsAuditStateBanner").className = "home-state-banner error";
    $("#operationsAuditStateBanner").textContent = "Audit data unavailable — " +
      (state.operationsAuditError || "No authoritative projection returned.");
    $("#operationsAuditBody").innerHTML = homeEmpty("Audit timeline unavailable.", 8);
    $("#operationsAuditVisibleCount").textContent = "—";
    $("#operationsAuditScope").textContent = "Authorized scope unavailable";
    $("#operationsAuditGeneratedAt").textContent = "—";
    $("#operationsAuditBuildSha").textContent = "—";
    for (const [selector, label] of [
      ["#operationsAuditTenantFilter", "All tenants"],
      ["#operationsAuditWorkspaceFilter", "All workspaces"],
      ["#operationsAuditProjectFilter", "All projects"],
      ["#operationsAuditActorFilter", "All actors"],
      ["#operationsAuditActionFilter", "All actions"],
      ["#operationsAuditResourceFilter", "All resource types"],
    ]) {
      $(selector).innerHTML = '<option value="">' + esc(label) + "</option>";
    }
    return;
  }
  const complete = summary.query_status === "COMPLETE";
  $("#operationsAuditStateBanner").hidden = complete;
  if (!complete) {
    $("#operationsAuditStateBanner").className = "home-state-banner warn";
    $("#operationsAuditStateBanner").textContent = "Audit projection is partial. Missing scope names are not inferred.";
  }
  $("#operationsAuditScope").textContent = summary.scope?.label || "Authorized scope";
  $("#operationsAuditGeneratedAt").textContent = formatHomeTime(summary.generated_at);
  $("#operationsAuditBuildSha").textContent = summary.build_sha || "unknown";
  populateOperationsAuditFilters();
  renderOperationsAuditRows();
}

async function refreshOperationsAudit(render = true) {
  if (state.operationsAuditLoading) return;
  state.operationsAuditLoading = true;
  state.operationsAuditError = null;
  if (render) {
    $("#operationsAuditStateBanner").hidden = false;
    $("#operationsAuditStateBanner").className = "home-state-banner loading";
    $("#operationsAuditStateBanner").textContent = "Loading authorized audit timeline…";
  }
  try {
    state.operationsAudit = await api("/browser/operations/audit");
  } catch (error) {
    state.operationsAudit = null;
    state.operationsAuditError = error.message;
    if (error.status === 401) {
      showLogin();
      return;
    }
  } finally {
    state.operationsAuditLoading = false;
  }
  if (render && !$("#operationsAuditView").hidden) renderOperationsAudit();
}

function selectedApproval() {
  return (state.operationsApprovals?.pending || []).find(
    (item) => item.proposal_id === state.selectedApprovalId
  ) || null;
}

function renderApprovalInspector() {
  const proposal = selectedApproval();
  const empty = $("#operationsApprovalInspectorEmpty");
  const inspector = $("#operationsApprovalInspector");
  if (!proposal) {
    empty.hidden = false;
    inspector.hidden = true;
    return;
  }
  empty.hidden = true;
  inspector.hidden = false;
  $("#approvalProposalId").textContent = proposal.proposal_id;
  $("#approvalProjectName").textContent = proposal.project_name || "Project";
  $("#approvalProjectId").textContent = proposal.project_id;
  $("#approvalAction").textContent = proposal.action;
  $("#approvalProposer").textContent = proposal.proposer_actor_id;
  $("#approvalPolicy").textContent = proposal.required_approval_policy || "No explicit policy";
  $("#approvalPayloadHash").textContent = proposal.payload_hash;
  $("#approvalResourceRefs").textContent = JSON.stringify(proposal.resource_refs || [], null, 2);
  $("#approvalFrozenPayload").textContent = JSON.stringify(proposal.frozen_payload || {}, null, 2);
  $("#approvalDecisionControls").hidden = !proposal.can_approve;
  $("#approvalNoAuthority").hidden = proposal.can_approve;
}

function renderOperationsApprovals() {
  const summary = state.operationsApprovals;
  if (!summary) {
    $("#operationsApprovalsStateBanner").hidden = false;
    $("#operationsApprovalsStateBanner").className = "home-state-banner error";
    $("#operationsApprovalsStateBanner").textContent = "Approvals data unavailable — " +
      (state.operationsApprovalsError || "No authoritative projection returned.");
    state.selectedApprovalId = null;
    $("#operationsApprovalsPendingCount").textContent = "—";
    $("#operationsApprovalDecisionCount").textContent = "—";
    $("#operationsApprovalsPendingList").innerHTML = '<div class="feed-empty">Pending approvals unavailable.</div>';
    $("#operationsApprovalDecisionBody").innerHTML = homeEmpty("Decision history unavailable.", 7);
    $("#operationsApprovalInspectorEmpty").hidden = false;
    $("#operationsApprovalInspector").hidden = true;
    $("#operationsApprovalsGeneratedAt").textContent = "—";
    $("#operationsApprovalsBuildSha").textContent = "—";
    return;
  }

  $("#operationsApprovalsStateBanner").hidden = summary.query_status === "COMPLETE";
  $("#operationsApprovalsScope").textContent = summary.scope?.label || "Authorized scope";
  $("#operationsApprovalsGeneratedAt").textContent = formatHomeTime(summary.generated_at);
  $("#operationsApprovalsBuildSha").textContent = summary.build_sha || "unknown";

  const pending = summary.pending || [];
  if (state.selectedApprovalId && !pending.some((item) => item.proposal_id === state.selectedApprovalId)) {
    state.selectedApprovalId = null;
  }
  $("#operationsApprovalsPendingCount").textContent = pending.length;
  $("#operationsApprovalsPendingList").innerHTML = pending.length ? pending.map((proposal) =>
    '<button type="button" class="approval-list-item' +
      (proposal.proposal_id === state.selectedApprovalId ? " active" : "") +
      '" data-proposal-id="' + esc(proposal.proposal_id) + '">' +
      '<span><strong>' + esc(proposal.action) + '</strong><small>' + esc(proposal.project_name || proposal.project_id) + '</small></span>' +
      '<code>' + esc(proposal.proposal_id) + '</code><time>' + esc(formatHomeTime(proposal.created_at)) + '</time>' +
      (proposal.can_approve ? '<span class="approval-authority">Can approve</span>' : '<span class="approval-viewonly">View only</span>') +
    "</button>"
  ).join("") : '<div class="feed-empty">No pending approvals in the current authorized scope.</div>';

  const decisions = summary.decisions || [];
  $("#operationsApprovalDecisionCount").textContent = decisions.length;
  $("#operationsApprovalDecisionBody").innerHTML = decisions.length ? decisions.map((item) =>
    "<tr>" +
      '<td><strong>' + esc(item.decision) + '</strong><code>' + esc(item.approval_id) + "</code></td>" +
      '<td><code>' + esc(item.proposal_id) + '</code><small>' + esc(item.action || "—") + "</small></td>" +
      '<td><strong>' + esc(item.project_name || "Project") + '</strong><code>' + esc(item.project_id) + "</code></td>" +
      '<td><code>' + esc(item.approver_actor_id) + "</code></td>" +
      '<td><code>' + esc(item.proposal_hash) + "</code></td>" +
      '<td><span>' + esc(item.conditions?.reason || "—") + "</span></td>" +
      '<td><span>' + esc(formatHomeTime(item.created_at)) + "</span></td>" +
    "</tr>"
  ).join("") : homeEmpty("No approval decisions in the current authorized scope.", 7);

  renderApprovalInspector();
}

async function refreshOperationsApprovals(render = true) {
  if (state.operationsApprovalsLoading) return;
  state.operationsApprovalsLoading = true;
  state.operationsApprovalsError = null;
  if (render) {
    $("#operationsApprovalsStateBanner").hidden = false;
    $("#operationsApprovalsStateBanner").className = "home-state-banner loading";
    $("#operationsApprovalsStateBanner").textContent = "Loading authorized approval inbox…";
  }
  try {
    state.operationsApprovals = await api("/browser/operations/approvals");
  } catch (error) {
    state.operationsApprovals = null;
    state.operationsApprovalsError = error.message;
    if (error.status === 401) {
      showLogin();
      return;
    }
  } finally {
    state.operationsApprovalsLoading = false;
  }
  if (render && !$("#operationsApprovalsView").hidden) renderOperationsApprovals();
}

async function decideApproval(decision) {
  const proposal = selectedApproval();
  if (!proposal || !proposal.can_approve) return;
  const isReject = decision === "reject";
  const reason = $("#approvalRejectReason").value.trim();
  if (isReject && !reason) {
    $("#operationsApprovalsStateBanner").hidden = false;
    $("#operationsApprovalsStateBanner").className = "home-state-banner error";
    $("#operationsApprovalsStateBanner").textContent = "Reject requires a reason.";
    return;
  }
  const confirmed = await confirmGovernedAction({
    title: isReject ? "Reject exact proposal hash" : "Approve exact proposal hash",
    action: isReject ? "REJECT PROPOSAL" : "APPROVE PROPOSAL",
    target: proposal.proposal_id + " · " + proposal.payload_hash,
    scope: proposal.project_name + " · " + proposal.project_id,
    consequence: isReject ?
      "Records a REJECTED decision with your reason for this exact frozen payload hash. It does not apply any underlying change." :
      "Records an APPROVED decision for this exact frozen payload hash. It does not apply the underlying governed change.",
  });
  if (!confirmed) return;

  $("#operationsApprovalsStateBanner").hidden = false;
  $("#operationsApprovalsStateBanner").className = "home-state-banner loading";
  $("#operationsApprovalsStateBanner").textContent = "Recording authoritative decision…";
  try {
    await api(
      "/browser/operations/approvals/" + encodeURIComponent(proposal.proposal_id) + "/" + decision,
      {
        method: "POST",
        body: isReject ?
          { expected_hash: proposal.payload_hash, reason } :
          { expected_hash: proposal.payload_hash },
      }
    );
    state.selectedApprovalId = null;
    $("#approvalRejectReason").value = "";
    await refreshOperationsApprovals(false);
    state.home = null;
    state.homeError = null;
    await refreshHomeSummary(false);
    renderOperationsApprovals();
    renderAttentionIndicator();
  } catch (error) {
    if (error.status === 401) {
      showLogin();
      return;
    }
    $("#operationsApprovalsStateBanner").hidden = false;
    $("#operationsApprovalsStateBanner").className = "home-state-banner error";
    $("#operationsApprovalsStateBanner").textContent = "Approval decision failed — " + error.message;
  }
}

function setOperationsSubnavActive(path) {
  document.querySelectorAll("[data-operations-route]").forEach((button) => {
    button.classList.toggle("active", normalizedRoute(button.dataset.operationsRoute) === normalizedRoute(path));
  });
}

function renderOperationsLocked(path) {
  const section = path.split("/").filter(Boolean).pop() || "operations";
  const labels = { approvals: "Approvals", audit: "Audit", runtime: "Runtime" };
  const label = labels[section] || "Operations";
  $("#operationsRunsView").hidden = true;
  $("#operationsApprovalsView").hidden = true;
  $("#operationsAuditView").hidden = true;
  $("#operationsLockedView").hidden = false;
  $("#operationsLockedIcon").innerHTML = iconSvg("operations", "icon");
  $("#operationsLockedShield").innerHTML = iconSvg("shield", "icon");
  $("#operationsLockedTitle").textContent = label;
  $("#operationsLockedDescription").textContent =
    label + " is the next BPS-M03 screen in the QA-first sequence. Its route is real, but no data or action is fabricated before implementation.";
}

function renderOperationsRoute(item) {
  $("#homeRouteView").hidden = true;
  $("#projectsRouteView").hidden = true;
  $("#accessRouteView").hidden = true;
  $("#lockedRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = true;
  $("#operationsRouteView").hidden = false;

  let path = normalizedRoute();
  if (path === "/app/operations") {
    path = "/app/operations/runs";
    history.replaceState({ route: path }, "", path);
  }
  setOperationsSubnavActive(path);
  if (path === "/app/operations/runs") {
    $("#operationsLockedView").hidden = true;
    $("#operationsApprovalsView").hidden = true;
    $("#operationsAuditView").hidden = true;
    $("#operationsRunsView").hidden = false;
    document.title = "GWF — Operations / Runs";
    if (state.operationsRuns) renderOperationsRuns();
    else if (state.operationsRunsError) renderOperationsRunsError(state.operationsRunsError);
    else void refreshOperationsRuns(true);
    return;
  }
  if (path === "/app/operations/approvals") {
    $("#operationsLockedView").hidden = true;
    $("#operationsRunsView").hidden = true;
    $("#operationsAuditView").hidden = true;
    $("#operationsApprovalsView").hidden = false;
    document.title = "GWF — Operations / Approvals";
    if (state.operationsApprovals) renderOperationsApprovals();
    else void refreshOperationsApprovals(true);
    return;
  }
  if (path === "/app/operations/audit") {
    $("#operationsLockedView").hidden = true;
    $("#operationsRunsView").hidden = true;
    $("#operationsApprovalsView").hidden = true;
    $("#operationsAuditView").hidden = false;
    document.title = "GWF — Operations / Audit";
    if (state.operationsAudit) renderOperationsAudit();
    else void refreshOperationsAudit(true);
    return;
  }
  $("#operationsApprovalsView").hidden = true;
  $("#operationsAuditView").hidden = true;
  document.title = "GWF — Operations / " + (path.split("/").pop() || "");
  renderOperationsLocked(path);
}

function renderRoute() {
  let path = normalizedRoute();
  if (path === "/app") {
    history.replaceState({ route: DEFAULT_ROUTE }, "", DEFAULT_ROUTE);
    path = DEFAULT_ROUTE;
  }
  const item = capabilityForRoute(path);
  if (!item) {
    history.replaceState({ route: DEFAULT_ROUTE }, "", DEFAULT_ROUTE);
    renderDiagnosticsRoute(capabilityById("diagnostics"));
    setActiveNav("diagnostics");
    return;
  }
  setActiveNav(item.id);
  document.title = "GWF — " + displayLabel(item);
  if (item.state === "LIVE_MODULE" && item.id === "home") renderHomeRoute(item);
  else if (item.state === "LIVE_MODULE" && item.id === "projects") renderProjectsRoute(item);
  else if (item.state === "LIVE_MODULE" && item.id === "access") renderAccessRoute(item);
  else if (item.state === "LIVE_MODULE" && item.id === "operations") renderOperationsRoute(item);
  else if (item.state === "LIVE_FOUNDATION" && item.id === "diagnostics") renderDiagnosticsRoute(item);
  else renderLockedRoute(item);
}

function navigateTo(path) {
  if (!path) return;
  if (normalizedRoute() !== normalizedRoute(path)) {
    history.pushState({ route: path }, "", path);
  }
  renderRoute();
  $("#sidebar").classList.remove("mobile-open");
}

function renderFoundationCards() {
  const ids = ["projects", "packages", "operations", "diagnostics"];
  const copy = {
    projects: "Manage research projects with governed workflows.",
    packages: "Research packages, domains and reusable skills.",
    operations: "Monitor runs, experiments, approvals and health.",
    diagnostics: "Configuration, runtime identity and system status."
  };
  $("#foundationCards").innerHTML = ids.map((id) => {
    const item = capabilityById(id);
    if (!item) return "";
    return '<article class="foundation-card">' +
      '<div class="feature-icon">' + iconSvg(id, "icon") + '</div>' +
      '<div class="feature-copy"><div class="feature-title"><strong>' + esc(displayLabel(item)) + '</strong>' + statePill(item) + '</div>' +
      '<p>' + esc(copy[id]) + '</p></div>' +
      "</article>";
  }).join("");
}

function renderCapabilities() {
  $("#capabilityList").innerHTML = state.bootstrap.capabilities.map((item) =>
    '<div class="capability-row"><span class="mini-icon">' + iconSvg(item.id, "icon") + '</span>' +
    '<span class="capability-name"><strong>' + esc(displayLabel(item)) + '</strong><small>' + esc(item.slice) + '</small></span>' +
    statePill(item) + "</div>"
  ).join("");
}

function renderIdentity() {
  const product = state.bootstrap.product;
  const me = state.me;
  const memberships = me.memberships || {};
  const membershipCount =
    (memberships.tenants?.length || 0) +
    (memberships.workspaces?.length || 0) +
    (memberships.projects?.length || 0);
  $("#actorName").textContent = me.principal_id || me.actor_id;
  $("#actorInitial").textContent = (me.principal_id || "?").slice(0, 1).toUpperCase();
  $("#authMethod").textContent = me.auth_method;
  $("#actorMenuPrincipal").textContent = me.principal_id || "—";
  $("#actorMenuActorId").textContent = me.actor_id || "—";
  $("#actorMenuAuth").textContent = me.auth_method || "—";
  $("#actorMenuExpires").textContent = formatHomeTime(me.expires_at);
  $("#actorMenuMemberships").textContent =
    (memberships.tenants?.length || 0) + " tenant · " +
    (memberships.workspaces?.length || 0) + " workspace · " +
    (memberships.projects?.length || 0) + " project" +
    (membershipCount === 0 ? " (none)" : "");
  $("#foundationBuild").textContent = product.version + " · " + String(product.build_sha || "unknown").slice(0, 8);
  $("#exactBuild").textContent = product.version + " · " + product.build_sha;
  $("#exactDomain").textContent = product.domain_id;
  $("#exactBackend").textContent = product.backend + " · " + product.server_mode;
  $("#exactActor").textContent = me.principal_id || me.actor_id;
}

function setActorMenu(open) {
  const menu = $("#actorMenu");
  const button = $("#actorMenuButton");
  menu.hidden = !open;
  button.setAttribute("aria-expanded", open ? "true" : "false");
}

function statusRow(icon, label, value, stateClass = "") {
  return '<div class="status-row"><span class="status-row-icon">' + iconSvg(icon, "icon") + '</span>' +
    '<span>' + esc(label) + '</span><strong class="' + esc(stateClass) + '">' + esc(value) + "</strong></div>";
}

function renderSystemStatus() {
  const product = state.bootstrap.product;
  const health = state.health;
  const healthValue = health?.core_health || "UNKNOWN";
  const healthClass = healthValue === "HEALTHY" ? "status-good" : "status-warn";
  $("#systemStatus").innerHTML =
    statusRow("diagnostics", "System", healthValue, healthClass) +
    statusRow("system", "Server", product.server_mode) +
    statusRow("packages", "Database", product.backend) +
    statusRow("panel", "Version", product.version) +
    statusRow("home", "Environment", product.domain_id);
}

async function refreshHealth() {
  try {
    state.health = await api("/ready");
    $("#healthDot").className = "health-dot healthy";
  } catch (error) {
    state.health = { core_health: "UNHEALTHY" };
    $("#healthDot").className = "health-dot unhealthy";
  }
  renderSystemStatus();
}

async function loadAuthenticatedShell() {
  state.bootstrap = await api("/browser/bootstrap");
  if (!state.bootstrap.authenticated) {
    showLogin();
    return;
  }
  try {
    state.me = await api("/browser/auth/me");
  } catch {
    showLogin();
    return;
  }
  renderNav();
  renderFoundationCards();
  renderCapabilities();
  renderIdentity();
  $("#loginView").hidden = true;
  $("#appView").hidden = false;
  await refreshHealth();
  await refreshHomeSummary(false);
  renderRoute();
}

function showLogin() {
  state.home = null;
  state.homeError = null;
  state.projects = null;
  state.projectsError = null;
  state.access = null;
  state.accessError = null;
  state.operationsRuns = null;
  state.operationsRunsError = null;
  state.operationsApprovals = null;
  state.operationsApprovalsError = null;
  state.selectedApprovalId = null;
  state.operationsAudit = null;
  state.operationsAuditError = null;
  setActorMenu(false);
  $("#appView").hidden = true;
  $("#loginView").hidden = false;
  const product = state.bootstrap?.product;
  $("#loginProduct").textContent = product ?
    [product.version, product.build_sha, product.backend].filter(Boolean).join(" · ") :
    "Live GWF server";
}

function wireStaticIcons() {
  $("#searchIcon").innerHTML = iconSvg("search", "icon");
  $("#notificationButton").innerHTML = iconSvg("bell", "icon") + '<span id="attentionCount" class="attention-count">—</span>';
  $("#mobileMenu").innerHTML = iconSvg("panel", "icon");
  $("#boundaryIcon").innerHTML = iconSvg("shield", "icon");
  document.querySelector('[data-theme-option="light"]').innerHTML = iconSvg("sun", "icon");
  document.querySelector('[data-theme-option="system"]').innerHTML = iconSvg("system", "icon");
  document.querySelector('[data-theme-option="dark"]').innerHTML = iconSvg("moon", "icon");
}

async function initialize() {
  wireStaticIcons();
  applyTheme(storedTheme());
  applySidebar(localStorage.getItem(SIDEBAR_KEY) || "expanded");
  state.bootstrap = await api("/browser/bootstrap");
  await loadAuthenticatedShell();
}

$("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("#loginError").textContent = "";
  try {
    await api("/browser/auth/login", {
      method: "POST",
      body: { username: $("#username").value, password: $("#password").value },
    });
    $("#password").value = "";
    await loadAuthenticatedShell();
  } catch (error) {
    $("#loginError").textContent = error.status === 401 ? "Invalid username or password." : error.message;
  }
});

$("#logoutButton").addEventListener("click", async () => {
  try { await api("/browser/auth/logout", { method: "POST" }); } catch {}
  state.me = null;
  state.bootstrap = await api("/browser/bootstrap");
  showLogin();
});

document.querySelectorAll("[data-theme-option]").forEach((button) => {
  button.addEventListener("click", () => applyTheme(button.dataset.themeOption));
});

$("#sidebarToggle").addEventListener("click", () => {
  const collapsed = $("#sidebar").classList.contains("collapsed");
  applySidebar(collapsed ? "expanded" : "collapsed");
});

$("#mobileMenu").addEventListener("click", () => $("#sidebar").classList.toggle("mobile-open"));

$("#mainNav").addEventListener("click", (event) => {
  const button = event.target.closest(".nav-item");
  if (!button) return;
  navigateTo(button.dataset.route);
});

window.addEventListener("popstate", () => {
  if (state.bootstrap?.authenticated) renderRoute();
});

$("#homeRefreshButton").addEventListener("click", async () => {
  await refreshHomeSummary(true);
});

$("#notificationButton").addEventListener("click", () => {
  const home = capabilityById("home");
  if (!home?.route) return;
  navigateTo(home.route);
  requestAnimationFrame(() => {
    $("#homeAttentionPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

$("#actorMenuButton").addEventListener("click", (event) => {
  event.stopPropagation();
  setActorMenu($("#actorMenu").hidden);
});

$("#actorMenu").addEventListener("click", (event) => event.stopPropagation());

document.addEventListener("click", () => setActorMenu(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setActorMenu(false);
});

$("#projectsRefreshButton").addEventListener("click", async () => {
  await refreshProjectsIndex(true);
});

$("#accessRefreshButton").addEventListener("click", async () => {
  await refreshAccessSummary(true);
});

$("#operationsRunsRefreshButton").addEventListener("click", async () => {
  await refreshOperationsRuns(true);
});

$("#operationsApprovalsRefreshButton").addEventListener("click", async () => {
  await refreshOperationsApprovals(true);
});

$("#operationsAuditRefreshButton").addEventListener("click", async () => {
  await refreshOperationsAudit(true);
});

$("#operationsAuditTextFilter").addEventListener("input", (event) => {
  state.operationsAuditFilters.text = event.target.value;
  renderOperationsAuditRows();
});

for (const [selector, key] of [
  ["#operationsAuditTenantFilter", "tenant"],
  ["#operationsAuditWorkspaceFilter", "workspace"],
  ["#operationsAuditProjectFilter", "project"],
  ["#operationsAuditActorFilter", "actor"],
  ["#operationsAuditActionFilter", "action"],
  ["#operationsAuditResourceFilter", "resource"],
  ["#operationsAuditFromFilter", "from"],
  ["#operationsAuditToFilter", "to"],
]) {
  $(selector).addEventListener("change", (event) => {
    state.operationsAuditFilters[key] = event.target.value;
    renderOperationsAuditRows();
  });
}

$("#operationsAuditResetFiltersButton").addEventListener("click", () => {
  state.operationsAuditFilters = {
    text: "", tenant: "", workspace: "", project: "", actor: "", action: "", resource: "", from: "", to: ""
  };
  $("#operationsAuditTextFilter").value = "";
  $("#operationsAuditFromFilter").value = "";
  $("#operationsAuditToFilter").value = "";
  populateOperationsAuditFilters();
  renderOperationsAuditRows();
});

$("#operationsApprovalsPendingList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-proposal-id]");
  if (!button) return;
  state.selectedApprovalId = button.dataset.proposalId;
  renderOperationsApprovals();
});

$("#approvalApproveButton").addEventListener("click", async () => {
  await decideApproval("approve");
});

$("#approvalRejectButton").addEventListener("click", async () => {
  await decideApproval("reject");
});

$("#operationsRouteView").addEventListener("click", (event) => {
  const button = event.target.closest("[data-operations-route]");
  if (!button) return;
  navigateTo(button.dataset.operationsRoute);
});

$("#operationsRunsTextFilter").addEventListener("input", (event) => {
  state.operationsRunsFilters.text = event.target.value;
  renderOperationsRunsRows();
});

for (const [selector, key] of [
  ["#operationsRunsTenantFilter", "tenant"],
  ["#operationsRunsWorkspaceFilter", "workspace"],
  ["#operationsRunsProjectFilter", "project"],
  ["#operationsRunsStatusFilter", "status"],
]) {
  $(selector).addEventListener("change", (event) => {
    state.operationsRunsFilters[key] = event.target.value;
    renderOperationsRunsRows();
  });
}

$("#operationsRunsResetFiltersButton").addEventListener("click", () => {
  state.operationsRunsFilters = { text: "", tenant: "", workspace: "", project: "", status: "" };
  $("#operationsRunsTextFilter").value = "";
  populateOperationsRunFilters();
  renderOperationsRunsRows();
});

$("#accessScopeKind").addEventListener("change", () => {
  populateAccessControls();
});

$("#accessScopeTarget").addEventListener("change", () => {
  renderAccessMembers();
});

$("#createTenantForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("#createTenantName").value.trim();
  if (!name) return;
  await performAccessMutation("/browser/access/tenants", {
    method: "POST",
    body: { name },
  });
  if (state.access) $("#createTenantName").value = "";
});

$("#createWorkspaceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const tenantId = $("#createWorkspaceTenant").value;
  const name = $("#createWorkspaceName").value.trim();
  if (!tenantId || !name) return;
  await performAccessMutation("/browser/access/tenants/" + encodeURIComponent(tenantId) + "/workspaces", {
    method: "POST",
    body: { name },
  });
  if (state.access) $("#createWorkspaceName").value = "";
});

$("#accessMemberForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const kind = $("#accessScopeKind").value;
  const scopeId = $("#accessScopeTarget").value;
  const actorId = $("#accessMemberActorId").value.trim();
  const role = $("#accessMemberRole").value;
  if (!scopeId || !actorId || !role) return;
  const plural = kind === "tenant" ? "tenants" : (kind === "workspace" ? "workspaces" : "projects");
  await performAccessMutation(
    "/browser/access/" + plural + "/" + encodeURIComponent(scopeId) + "/members",
    { method: "POST", body: { actor_id: actorId, role } }
  );
});

$("#accessMemberRevokeButton").addEventListener("click", async () => {
  const kind = $("#accessScopeKind").value;
  const scopeId = $("#accessScopeTarget").value;
  const actorId = $("#accessMemberActorId").value.trim();
  const selected = accessSelectedScope();
  if (!scopeId || !actorId || !selected) return;

  const confirmed = await confirmGovernedAction({
    title: "Revoke direct membership",
    action: "REVOKE " + kind.toUpperCase() + " MEMBER",
    target: actorId,
    scope: accessScopeLabel(kind, selected),
    consequence:
      "This direct membership will be marked REVOKED. Access inherited from another tenant, workspace or project membership may still remain.",
  });
  if (!confirmed) return;

  const plural = kind === "tenant" ? "tenants" : (kind === "workspace" ? "workspaces" : "projects");
  await performAccessMutation(
    "/browser/access/" + plural + "/" + encodeURIComponent(scopeId) +
      "/members/" + encodeURIComponent(actorId),
    { method: "DELETE" }
  );
});

$("#projectsTextFilter").addEventListener("input", (event) => {
  state.projectsFilters.text = event.target.value;
  renderProjectsRows();
});

for (const [selector, key] of [
  ["#projectsLifecycleFilter", "lifecycle"],
  ["#projectsTenantFilter", "tenant"],
  ["#projectsWorkspaceFilter", "workspace"],
  ["#projectsDomainFilter", "domain"],
  ["#projectsActivityFilter", "activity"],
  ["#projectsAttentionFilter", "attention"],
]) {
  $(selector).addEventListener("change", (event) => {
    state.projectsFilters[key] = event.target.value;
    renderProjectsRows();
  });
}

$("#projectsResetFiltersButton").addEventListener("click", () => {
  state.projectsFilters = {
    text: "",
    lifecycle: "",
    tenant: "",
    workspace: "",
    domain: "",
    activity: "",
    attention: "",
  };
  $("#projectsTextFilter").value = "";
  $("#projectsLifecycleFilter").value = "";
  $("#projectsActivityFilter").value = "";
  $("#projectsAttentionFilter").value = "";
  populateProjectsFilterOptions();
  renderProjectsRows();
});

$("#refreshButton").addEventListener("click", async () => {
  state.bootstrap = await api("/browser/bootstrap");
  renderNav();
  renderFoundationCards();
  renderCapabilities();
  renderIdentity();
  await refreshHealth();
  renderRoute();
});

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (storedTheme() === "system") document.documentElement.dataset.theme = "system";
});

initialize().catch((error) => {
  $("#loginError").textContent = "Cannot reach the canonical GWF server: " + error.message;
  showLogin();
});
