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
  home: "Home unlocks in BPS-M01 after its own QA and local UAT. No KPI, run, project or activity data is fabricated in the foundation shell.",
  projects: "Projects and access management unlock in BPS-M02. No project entities or lifecycle actions are fabricated here.",
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
    ["SYSTEM", ["github", "diagnostics", "settings"]],
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
  if (path.startsWith("/app/projects/")) return capabilityById("projects");
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
    "Attention count unavailable" :
    ("Attention required: " + count + " · feed opens with Operations in a later screen");
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
  $("#lockedRouteView").hidden = true;
  $("#diagnosticsRouteView").hidden = true;
  $("#projectsRouteView").hidden = false;
  document.title = "GWF — Projects";
  if (state.projects) renderProjectsIndex();
  else if (state.projectsError) renderProjectsError(state.projectsError);
  else void refreshProjectsIndex(true);
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
  $("#actorName").textContent = me.principal_id || me.actor_id;
  $("#actorInitial").textContent = (me.principal_id || "?").slice(0, 1).toUpperCase();
  $("#authMethod").textContent = me.auth_method;
  $("#foundationBuild").textContent = product.version + " · " + String(product.build_sha || "unknown").slice(0, 8);
  $("#exactBuild").textContent = product.version + " · " + product.build_sha;
  $("#exactDomain").textContent = product.domain_id;
  $("#exactBackend").textContent = product.backend + " · " + product.server_mode;
  $("#exactActor").textContent = me.principal_id || me.actor_id;
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

$("#projectsRefreshButton").addEventListener("click", async () => {
  await refreshProjectsIndex(true);
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
