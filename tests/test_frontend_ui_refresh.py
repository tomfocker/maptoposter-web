import asyncio
from pathlib import Path

from tests._app_main_bootstrap import app_main


def test_index_template_exposes_refine_panel_contract():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'data-ui="studio-shell"' in template
    assert 'data-ui="quick-generate-panel"' in template
    assert 'data-ui="poster-stage"' in template
    assert 'data-ui="recent-works"' in template
    assert 'data-ui="theme-picker"' in template
    assert 'data-ui="refine-toggle"' in template
    assert 'data-ui="refine-panel"' in template
    assert 'name="theme"' in template
    assert 'name="size"' in template
    assert 'name="copy_language"' in template
    assert 'data-ui="theme-current-preview"' in template
    assert 'data-ui="theme-gallery"' in template


def test_template_moves_theme_gallery_into_refine_panel():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    refine_panel_start = template.index('data-ui="refine-panel"')
    pre_refine_panel = template[:refine_panel_start]
    refine_panel = template[refine_panel_start:]

    assert "主题色板总览" not in pre_refine_panel
    assert "主题色板总览" in refine_panel
    assert 'data-ui="theme-current-preview"' in pre_refine_panel


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


def test_status_route_returns_success_partial_with_filename(app_main):
    app_main.TASKS_STATE["task-123"] = {"status": "done", "filename": "poster.png", "log": ""}
    response = asyncio.run(app_main.get_status("task-123"))
    _assert_partial_template_response(response, "partials/poster_stage_success.html", filename="poster.png")


def test_status_route_exposes_output_format_for_success_partial(app_main):
    app_main.TASKS_STATE["task-456"] = {
        "status": "done",
        "filename": "poster.pdf",
        "output_format": "pdf",
        "log": "",
    }

    response = asyncio.run(app_main.get_status("task-456"))
    _assert_partial_template_response(
        response,
        "partials/poster_stage_success.html",
        filename="poster.pdf",
        output_format="pdf",
    )

    template = Path("app/templates/partials/poster_stage_success.html").read_text(encoding="utf-8")
    assert "output_format" in template
    assert "application/pdf" in template
