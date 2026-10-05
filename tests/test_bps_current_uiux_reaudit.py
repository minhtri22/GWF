from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id" and value:
                self.ids.append(value)


def test_current_uiux_shell_has_no_duplicate_ids_or_missing_static_targets():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    parser = IdCollector()
    parser.feed(html)
    assert len(parser.ids) == len(set(parser.ids))

    static_targets = set(re.findall(r'\$\("#([A-Za-z0-9_-]+)"\)', js))
    missing = sorted(static_targets.difference(parser.ids))
    assert missing == []


def test_current_uiux_browser_local_persistence_is_presentation_only():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    keys = re.findall(
        r"localStorage\.(?:getItem|setItem)\(\s*([A-Z_]+)",
        js,
    )
    assert keys
    assert set(keys) == {"THEME_KEY", "SIDEBAR_KEY"}
    assert "localStorage.removeItem" not in js
    assert "localStorage.clear" not in js

    forbidden = (
        "projectState",
        "approvalState",
        "runState",
        "githubState",
        "packageState",
        "lifecycleState",
    )
    assert all(token not in js for token in forbidden)


def test_current_uiux_capability_maturity_matches_opened_scope():
    api = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")

    expected_live = {
        "home": ("LIVE_MODULE", "BPS-M01", "/app/home"),
        "projects": ("LIVE_MODULE", "BPS-M02", "/app/projects"),
        "operations": ("LIVE_MODULE", "BPS-M03", "/app/operations"),
        "packages": ("LIVE_MODULE", "BPS-M06", "/app/research/packages"),
        "github": ("LIVE_MODULE", "BPS-M07", "/app/system/github"),
        "access": ("LIVE_MODULE", "BPS-M02", "/app/system/access"),
        "diagnostics": (
            "LIVE_FOUNDATION",
            "BPS-I00",
            "/app/system/diagnostics",
        ),
    }
    for capability_id, (state, slice_id, route) in expected_live.items():
        needle = (
            f'{{"id": "{capability_id}", "label": '
        )
        start = api.find(needle)
        assert start >= 0, capability_id
        row_end = api.find("\n", start)
        row = api[start:row_end]
        assert f'"state": "{state}"' in row
        assert f'"slice": "{slice_id}"' in row
        assert f'"route": "{route}"' in row

    for capability_id in (
        "shared-library",
        "reference-acquisition",
        "agents",
    ):
        start = api.find(f'{{"id": "{capability_id}", "label": ')
        assert start >= 0
        row = api[start:api.find("\n", start)]
        assert '"state": "PLANNED_BLOCKED"' in row

    settings = api.find('{"id": "settings", "label": ')
    assert settings >= 0
    assert '"state": "SKELETON_LOCKED"' in api[
        settings:api.find("\n", settings)
    ]


def test_current_uiux_global_navigation_and_live_cross_screen_paths_are_real():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert 'id="commandPaletteButton"' in html
    assert 'id="commandPaletteDialog"' in html
    assert "Go to a product area" in html
    assert "Search projects, documents, artifacts" not in html
    assert "Ctrl K" not in html

    assert 'data-home-project-overview="' in js
    assert 'data-home-project-execution="' in js
    assert 'data-home-run-id="' in js
    assert 'data-run-id="' in js
    assert "projectRunPath(" in js
    assert 'data-home-attention-kind="' in js
    assert 'data-package-project="' in js
    assert 'projectWorkspacePath(project.dataset.packageProject, "overview")' in js

    assert 'navigateTo("/app/operations/approvals")' in js
    assert 'navigateTo("/app/system/github")' in js
    assert 'navigateTo("/app/system/diagnostics")' in js


def test_current_uiux_project_mutations_are_governed_and_service_backed():
    api = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert "@app.get('/browser/projects/create-options')" in api
    assert "@app.post('/browser/projects')" in api
    assert "@app.patch('/browser/projects/{project_id}')" in api
    assert "@app.post('/browser/projects/{project_id}/archive')" in api
    assert "@app.post('/browser/projects/{project_id}/restore')" in api

    assert "runtime.create_scoped_project(" in api
    assert "runtime.project_governance.rename(" in api
    assert "runtime.project_governance.archive(" in api
    assert "runtime.project_governance.restore(" in api
    assert "MANAGE_MEMBERS" in api

    assert "confirmGovernedAction({" in js
    assert 'performProjectLifecycleAction("RENAME")' in js
    assert 'performProjectLifecycleAction("ARCHIVE")' in js
    assert 'performProjectLifecycleAction("RESTORE")' in js


def test_current_uiux_diagnostics_contract_is_single_and_authoritative():
    api = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    assert api.count("@app.get('/browser/diagnostics')") == 1
    assert api.count("def browser_diagnostics") == 1
    assert "expected_checksum" in api
    assert "checksum_matches" in api
    assert "provider_events" in api
    assert "product.github_summary(" in api

    for target in (
        "diagnosticsMigrationList",
        "diagnosticsFoundationServices",
        "diagnosticsGithubStatus",
        "diagnosticsProviderBody",
    ):
        assert f'id="{target}"' in html

    assert 'api("/browser/diagnostics")' in js
    assert "renderDiagnosticsSummary" in js
    assert "refreshDiagnostics" in js

def test_current_uiux_mobile_keeps_governed_decision_actions_available():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    css = (WEB / "styles.css").read_text(encoding="utf-8")

    assert ".ghost{display:none}" not in css
    assert 'id="approvalApproveButton"' in html
    assert 'id="approvalRejectButton" class="ghost"' in html
    assert 'data-recovery-decision="APPROVED"' in js
    assert 'data-recovery-decision="REJECTED"' in js
    assert 'id="accessMemberRevokeButton" class="ghost"' in html

def test_current_uiux_topbar_session_keyboard_and_attention_are_live():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    api = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")

    assert 'id="topbarScopeContext"' in html
    assert 'id="topbarRuntimeContext"' in html
    assert 'id="notificationButton"' in html
    assert 'id="actorMenuButton"' in html
    assert 'id="actorMenu"' in html
    assert 'id="logoutButton"' in html

    assert '"All authorized · "' in js
    assert 'product.domain_id || "runtime"' in js
    assert 'product.backend || "backend"' in js
    assert 'Attention required: ' in js
    assert '$("#homeAttentionPanel")?.scrollIntoView' in js
    assert 'if (event.key === "Escape") setActorMenu(false);' in js
    assert 'aria-expanded' in js
    assert 'window.addEventListener("popstate", () => {' in js
    assert "if (state.bootstrap?.authenticated) renderRoute();" in js

    assert "/browser/auth/logout" in js
    assert "showLogin();" in js
    assert "gwr_browser_session" in api
    assert "httponly=true" in api.lower()
    assert "Authorization: Bearer" not in js


def test_current_uiux_projects_create_lifecycle_and_domain_contract_are_live():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    api = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")
    create_doc = (
        ROOT / "docs" / "uiux" / "screens" /
        "PROJECT_CREATE_STRICT_PRELOCK.md"
    ).read_text(encoding="utf-8")

    assert 'id="projectsCreateButton"' in html
    assert 'id="projectCreateDialog"' in html
    assert 'id="projectCreateWorkspace"' in html
    assert 'id="projectCreateDomain"' in html
    assert 'id="projectLifecycleControls"' in html
    assert 'id="projectRenameButton"' in html
    assert 'id="projectArchiveButton"' in html
    assert 'id="projectRestoreButton"' in html

    assert 'api("/browser/projects/create-options")' in js
    assert 'api("/browser/projects", {method: "POST"' in js
    assert 'performProjectLifecycleAction("RENAME")' in js
    assert 'performProjectLifecycleAction("ARCHIVE")' in js
    assert 'performProjectLifecycleAction("RESTORE")' in js
    assert "confirmGovernedAction({" in js
    assert "refreshProjectsIndex(false)" in js
    assert "refreshHomeSummary(false)" in js
    assert "No floating/latest revision implied" in js

    assert "@app.get('/browser/projects/create-options')" in api
    assert "@app.post('/browser/projects')" in api
    assert "@app.patch('/browser/projects/{project_id}')" in api
    assert "@app.post('/browser/projects/{project_id}/archive')" in api
    assert "@app.post('/browser/projects/{project_id}/restore')" in api
    assert "runtime.create_scoped_project(" in api
    assert "runtime.project_governance.rename(" in api
    assert "runtime.project_governance.archive(" in api
    assert "runtime.project_governance.restore(" in api

    assert (
        "IMPLEMENTED / STRICT_CONTRACT_SATISFIED / "
        "MASTER_REAUDIT_PENDING"
    ) in create_doc


def test_current_uiux_live_cross_screen_inspection_paths_are_exact():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    html = (WEB / "index.html").read_text(encoding="utf-8")

    assert 'data-home-project-overview="' in js
    assert 'data-home-project-execution="' in js
    assert 'data-home-run-id="' in js
    assert 'data-home-attention-kind="' in js
    assert 'data-run-project-execution="' in js
    assert 'data-run-id="' in js
    assert 'data-package-project="' in js

    assert "projectRunPath(" in js
    assert 'navigateTo("/app/operations/approvals")' in js
    assert 'navigateTo("/app/system/github")' in js
    assert 'navigateTo("/app/system/diagnostics")' in js
    assert 'projectWorkspacePath(project.dataset.packageProject, "overview")' in js
    assert '$("#projectBackButton").addEventListener("click"' in js

    assert 'data-project-section="overview"><span>Overview</span><small>Live</small>' in html
    assert 'data-project-section="execution"><span>Execution</span><small>Live</small>' in html
    assert 'data-project-section="library"><span>Library</span><small>Locked</small>' in html
    assert 'data-project-section="governance"><span>Governance</span><small>Locked</small>' in html
    assert 'data-project-section="configuration"><span>Configuration</span><small>Locked</small>' in html


def test_current_uiux_opened_scope_does_not_expose_future_mutations():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    # Packages is intentionally read-first.
    for forbidden in (
        "Publish revision",
        "Validate revision",
        "Upgrade to latest",
        "Install Skill",
    ):
        assert forbidden not in html

    # M07-A is read-only. The browser may probe readiness, but it cannot
    # create/disable/bind/prepare/preflight/execute GitHub mutations yet.
    github_start = js.index("function renderGithub")
    github_end = js.index("function renderPackages", github_start)
    github_ui = js[github_start:github_end]
    for mutation_path in (
        "/plugins",
        "/repositories",
        "/change-sets",
        "/preflight",
        "/execute",
    ):
        assert 'method: "POST"' not in github_ui or mutation_path not in github_ui

    # Recovery browser workflow opens only the qualified human decision.
    assert "Apply recovery" not in html
    assert "Retry phase" not in html
    assert "Verify phase" not in html
    assert "Write handoff" not in html

