"use strict";

const THEME_KEY = "gwr-ui-theme";
const SIDEBAR_KEY = "gwr-ui-sidebar";
const state = { bootstrap: null, me: null, health: null };

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
  if (item.state === "FOUNDATION_ONLY") return { cls: "foundation", label: "Foundation" };
  if (item.state === "PLANNED_BLOCKED") return { cls: "planned", label: "Planned" };
  return { cls: "locked", label: "Locked" };
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
      const enabled = item.state === "LIVE_FOUNDATION";
      const active = item.id === "diagnostics";
      const meta = stateMeta(item);
      const title = displayLabel(item) + " — " + meta.label + " · " + item.slice;
      return '<button type="button" class="nav-item ' + (active ? "active " : "") + (!enabled ? "disabled" : "") +
        '" data-capability="' + esc(item.id) + '" title="' + esc(title) + '" ' +
        (!enabled ? 'disabled aria-disabled="true"' : 'aria-current="page"') + '>' +
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
}

function showLogin() {
  $("#appView").hidden = true;
  $("#loginView").hidden = false;
  const product = state.bootstrap?.product;
  $("#loginProduct").textContent = product ?
    [product.version, product.build_sha, product.backend].filter(Boolean).join(" · ") :
    "Live GWF server";
}

function wireStaticIcons() {
  $("#searchIcon").innerHTML = iconSvg("search", "icon");
  $("#notificationButton").innerHTML = iconSvg("bell", "icon");
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
$("#refreshButton").addEventListener("click", async () => {
  state.bootstrap = await api("/browser/bootstrap");
  renderNav();
  renderFoundationCards();
  renderCapabilities();
  renderIdentity();
  await refreshHealth();
});

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (storedTheme() === "system") document.documentElement.dataset.theme = "system";
});

initialize().catch((error) => {
  $("#loginError").textContent = "Cannot reach the canonical GWF server: " + error.message;
  showLogin();
});
