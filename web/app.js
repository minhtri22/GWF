"use strict";

const THEME_KEY = "gwr-ui-theme";
const SIDEBAR_KEY = "gwr-ui-sidebar";
const state = { bootstrap: null, me: null };

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[ch]));

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
  $("#themeSelect").value = theme;
  localStorage.setItem(THEME_KEY, theme);
}

function applySidebar(value) {
  const collapsed = value === "collapsed";
  $("#sidebar").classList.toggle("collapsed", collapsed);
  $("#sidebarToggle").textContent = collapsed ? "⇥" : "⇤";
  $("#sidebarToggle").setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
  localStorage.setItem(SIDEBAR_KEY, collapsed ? "collapsed" : "expanded");
}

function statePill(item) {
  const stateName = item.state;
  const className = stateName === "LIVE_FOUNDATION" ? "live" :
    stateName === "FOUNDATION_ONLY" ? "foundation" :
    stateName === "PLANNED_BLOCKED" ? "planned" : "locked";
  const label = stateName === "LIVE_FOUNDATION" ? "Live foundation" :
    stateName === "FOUNDATION_ONLY" ? "Foundation" :
    stateName === "PLANNED_BLOCKED" ? "Planned" : "Locked";
  return '<span class="state-pill ' + className + '">' + label + "</span>";
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
      return '<button class="nav-item ' + (active ? "active " : "") + (!enabled ? "disabled" : "") +
        '" data-capability="' + esc(item.id) + '" ' + (!enabled ? 'disabled aria-disabled="true"' : "") + '>' +
        '<span class="nav-icon">' + esc(item.label.slice(0, 1)) + '</span>' +
        '<span class="nav-label">' + esc(item.label) + '<small>' + esc(item.slice) + '</small></span>' +
        statePill(item) + "</button>";
    }).join("");
    return '<section class="nav-group"><p>' + esc(group) + "</p>" + rows + "</section>";
  }).join("");
}

function renderIdentity() {
  const product = state.bootstrap.product;
  const identity = [
    ["Product", product.product],
    ["Version", product.version],
    ["Build SHA", product.build_sha],
    ["Domain", product.domain_id],
    ["Backend", product.backend],
    ["Server mode", product.server_mode],
  ];
  $("#runtimeIdentity").innerHTML = identity.map(([key, value]) =>
    '<div><dt>' + esc(key) + '</dt><dd><code>' + esc(value) + "</code></dd></div>"
  ).join("");

  const me = state.me;
  const session = [
    ["Actor", me.actor_id],
    ["Principal", me.principal_id],
    ["Auth method", me.auth_method],
    ["Expires", me.expires_at],
  ];
  $("#sessionIdentity").innerHTML = session.map(([key, value]) =>
    '<div><dt>' + esc(key) + '</dt><dd><code>' + esc(value) + "</code></dd></div>"
  ).join("");
  $("#actorName").textContent = me.principal_id || me.actor_id;
  $("#actorInitial").textContent = (me.principal_id || "?").slice(0, 1).toUpperCase();
  $("#authMethod").textContent = me.auth_method;
  $("#serverMode").textContent = product.server_mode;
}

function renderCapabilities() {
  $("#capabilityGrid").innerHTML = state.bootstrap.capabilities.map((item) =>
    '<article class="capability-card"><div><strong>' + esc(item.label) + '</strong>' +
    '<p>' + esc(item.slice) + "</p></div>" + statePill(item) + "</article>"
  ).join("");
}

async function refreshHealth() {
  try {
    const health = await api("/ready");
    $("#healthLabel").textContent = health.core_health;
    $("#healthDot").className = "health-dot healthy";
  } catch (error) {
    $("#healthLabel").textContent = "UNHEALTHY";
    $("#healthDot").className = "health-dot unhealthy";
  }
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
  renderIdentity();
  renderCapabilities();
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

async function initialize() {
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

$("#themeSelect").addEventListener("change", (event) => applyTheme(event.target.value));
$("#sidebarToggle").addEventListener("click", () => {
  const collapsed = $("#sidebar").classList.contains("collapsed");
  applySidebar(collapsed ? "expanded" : "collapsed");
});
$("#mobileMenu").addEventListener("click", () => $("#sidebar").classList.toggle("mobile-open"));
$("#refreshButton").addEventListener("click", async () => {
  await loadAuthenticatedShell();
});

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (storedTheme() === "system") document.documentElement.dataset.theme = "system";
});

initialize().catch((error) => {
  $("#loginError").textContent = "Cannot reach the canonical GWF server: " + error.message;
  showLogin();
});
