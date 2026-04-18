import asyncio
from pathlib import Path

from tests._app_main_bootstrap import app_main


def test_index_template_exposes_simplified_homepage_contract():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'data-ui="studio-shell"' in template
    assert 'data-ui="quick-generate-panel"' in template
    assert 'data-ui="poster-stage"' in template
    assert 'data-ui="recent-works"' in template
    assert 'data-ui="theme-picker"' in template
    assert 'data-ui="output-settings"' in template
    assert 'data-ui="copy-settings"' in template
    assert 'data-ui="composition-settings"' in template
    assert 'data-ui="theme-modal"' in template
    assert 'data-ui="theme-modal-open"' in template
    assert 'data-ui="theme-modal-close"' in template
    assert 'name="theme"' in template
    assert 'name="size"' in template
    assert 'name="copy_language"' in template
    assert 'data-ui="theme-current-preview"' in template
    assert 'data-ui="theme-gallery"' in template


def test_template_moves_theme_gallery_into_modal_container():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    modal_start = template.index('data-ui="theme-modal"')
    pre_modal = template[:modal_start]
    modal = template[modal_start:]

    assert 'data-ui="theme-gallery"' not in pre_modal
    assert 'data-ui="theme-gallery"' in modal
    assert "查看全部主题" in template


def test_template_removes_nonessential_english_microcopy():
    base_template = Path("app/templates/base.html").read_text(encoding="utf-8")
    index_template = Path("app/templates/index.html").read_text(encoding="utf-8")

    for snippet in (
        "MapToPoster Studio",
        "Preview-first poster workflow",
        "Search, tune, and export from one workspace.",
    ):
        assert snippet not in base_template

    for snippet in ("Quick Generate", "Poster Stage", "Recent Works", "Advanced"):
        assert snippet not in index_template


def test_template_keeps_only_minimal_top_level_microcopy():
    base_template = Path("app/templates/base.html").read_text(encoding="utf-8")
    index_template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert "地图海报工作室" in base_template
    assert "输入地点，快速生成一张可下载的城市海报" in base_template
    assert "首屏只保留最常用操作，完整主题和精修设置都收进下方折叠区。" not in base_template
    assert "先输入地点与主题，右侧会即时承接生成进度和结果。" not in index_template
    assert "支持 PNG、PDF 与 SVG 导出。" not in index_template


def test_template_replaces_refine_panel_with_always_visible_sections():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'data-ui="refine-toggle"' not in template
    assert 'data-ui="refine-panel"' not in template
    assert 'data-ui="copy-settings"' in template
    assert 'data-ui="composition-settings"' in template


def test_template_places_recent_works_inside_results_column():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'data-ui="results-column"' in template

    results_column_start = template.index('data-ui="results-column"')
    results_column = template[results_column_start:]

    assert 'data-ui="poster-stage"' in results_column
    assert 'data-ui="recent-works"' in results_column


def test_template_adds_scroll_body_for_recent_works():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert 'data-ui="recent-works-body"' in template
    assert "ResizeObserver" in template


def test_template_includes_theme_modal_interaction_hooks():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert "themeModalOpen" in template
    assert "themeModalClosers" in template
    assert "Escape" in template
    assert "overflow-hidden" in template


def test_theme_modal_hidden_state_has_explicit_css_rule():
    stylesheet = Path("app/static/css/style.css").read_text(encoding="utf-8")
    assert '[data-ui="theme-modal"][hidden]' in stylesheet
    assert "display: none !important;" in stylesheet


def test_loading_partial_preserves_spinner_between_status_polls():
    template = Path("app/templates/partials/poster_stage_loading.html").read_text(encoding="utf-8")

    assert 'hx-swap="outerHTML"' in template
    assert 'hx-preserve="true"' in template
    assert 'id="loading-spinner-{{ task_id }}"' in template


def test_stylesheet_uses_cool_gallery_palette():
    stylesheet = Path("app/static/css/style.css").read_text(encoding="utf-8")

    assert "--studio-bg: #eef3f8;" in stylesheet
    assert "--studio-accent: #2e5b88;" in stylesheet
    assert "--studio-highlight: #dbe7f4;" in stylesheet
    assert "#b26d3b" not in stylesheet


def test_template_removes_redundant_output_helper_copy():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert "导出会严格按所选比例和 DPI 计算，不额外裁边。" not in template
    assert "4000-6000 适合紧凑中心区，8000 以上更适合完整城市视图。" not in template


def test_template_removes_redundant_hero_and_cache_copy():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert "把城市变成一张可以马上预览的海报" not in template
    assert "智能缓存机制" not in template


def _assert_partial_template_response(response, template_name, **context):
    assert getattr(response, "template_name", None) == template_name
    response_context = getattr(response, "context", None)
    assert isinstance(response_context, dict)
    for key, value in context.items():
        assert response_context[key] == value


def test_history_route_returns_empty_history_partial(app_main, monkeypatch):
    monkeypatch.setattr(app_main.os, "listdir", lambda *_: [])
    response = asyncio.run(app_main.get_history(request=object()))
    _assert_partial_template_response(response, "partials/history_empty.html", items=[])


def test_history_route_keeps_supported_non_png_exports(app_main, monkeypatch):
    monkeypatch.setattr(app_main.os, "listdir", lambda *_: ["poster.pdf", "poster.svg", "poster.png", "notes.txt"])
    monkeypatch.setattr(app_main.os.path, "getmtime", lambda *_: 1)

    response = asyncio.run(app_main.get_history(request=object()))

    _assert_partial_template_response(response, "partials/history_grid.html")
    assert response.context["items"] == [
        {"filename": "poster.pdf", "output_format": "pdf"},
        {"filename": "poster.svg", "output_format": "svg"},
        {"filename": "poster.png", "output_format": "png"},
    ]

    template = Path("app/templates/partials/history_grid.html").read_text(encoding="utf-8")
    assert "output_format" in template
    assert "application/pdf" in template
    assert 'hx-delete="/history/{{ item.filename }}"' in template
    assert "data-role=\"history-delete\"" in template


def test_delete_history_route_removes_file_and_returns_updated_history(app_main, monkeypatch):
    removed = []

    monkeypatch.setattr(app_main.os.path, "exists", lambda path: path.endswith("poster.png"))
    monkeypatch.setattr(app_main.os, "remove", lambda path: removed.append(path))
    monkeypatch.setattr(app_main.os, "listdir", lambda *_: [])

    response = asyncio.run(app_main.delete_history_item(object(), "poster.png"))

    assert removed == ["posters/poster.png"]
    _assert_partial_template_response(response, "partials/history_empty.html", items=[])


def test_delete_history_route_rejects_path_traversal(app_main, monkeypatch):
    removed = []

    monkeypatch.setattr(app_main.os.path, "exists", lambda *_: True)
    monkeypatch.setattr(app_main.os, "remove", lambda path: removed.append(path))
    monkeypatch.setattr(app_main.os, "listdir", lambda *_: [])

    response = asyncio.run(app_main.delete_history_item(object(), "../poster.png"))

    assert removed == []
    _assert_partial_template_response(response, "partials/history_empty.html", items=[])


def test_stylesheet_keeps_history_delete_button_absolutely_positioned():
    stylesheet = Path("app/static/css/style.css").read_text(encoding="utf-8")

    assert '#history-list > div > [data-role="history-delete"]' in stylesheet
    assert "position: absolute !important;" in stylesheet


def test_status_route_returns_success_partial_with_filename(app_main):
    app_main.TASKS_STATE["task-123"] = {"status": "done", "filename": "poster.png", "log": ""}
    request = object()
    response = asyncio.run(app_main.get_status(request, "task-123"))
    _assert_partial_template_response(
        response,
        "partials/poster_stage_success.html",
        request=request,
        filename="poster.png",
    )


def test_status_route_exposes_output_format_for_success_partial(app_main):
    app_main.TASKS_STATE["task-456"] = {
        "status": "done",
        "filename": "poster.pdf",
        "output_format": "pdf",
        "log": "",
    }

    request = object()
    response = asyncio.run(app_main.get_status(request, "task-456"))
    _assert_partial_template_response(
        response,
        "partials/poster_stage_success.html",
        request=request,
        filename="poster.pdf",
        output_format="pdf",
    )

    template = Path("app/templates/partials/poster_stage_success.html").read_text(encoding="utf-8")
    assert "output_format" in template
    assert "application/pdf" in template


def test_status_route_passes_request_for_loading_and_error_partials(app_main):
    request = object()
    app_main.TASKS_STATE["task-loading"] = {"status": "running", "filename": "", "log": "正在准备生成环境..."}
    app_main.TASKS_STATE["task-error"] = {"status": "error", "filename": "", "log": "出错了"}

    loading_response = asyncio.run(app_main.get_status(request, "task-loading"))
    error_response = asyncio.run(app_main.get_status(request, "task-error"))

    _assert_partial_template_response(
        loading_response,
        "partials/poster_stage_loading.html",
        request=request,
        task_id="task-loading",
        log="正在准备生成环境...",
    )
    _assert_partial_template_response(
        error_response,
        "partials/poster_stage_error.html",
        request=request,
        log="出错了",
    )
