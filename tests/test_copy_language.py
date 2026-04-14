import asyncio
import importlib
import logging
import re
import sys
import types
from pathlib import Path

import pytest


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    return module


@pytest.fixture
def app_main(monkeypatch):
    class _FastAPI:
        def __init__(self, *args, **kwargs):
            pass

        def mount(self, *args, **kwargs):
            return None

        def get(self, *args, **kwargs):
            return lambda func: func

        def post(self, *args, **kwargs):
            return lambda func: func

    class _Jinja2Templates:
        def __init__(self, *args, **kwargs):
            pass

        def TemplateResponse(self, *args, **kwargs):
            return {"args": args, "kwargs": kwargs}

    class _StaticFiles:
        def __init__(self, *args, **kwargs):
            pass

    class _HTMLResponse:
        def __init__(self, content="", *args, **kwargs):
            self.content = content

    geocoders = _module(
        "geopy.geocoders",
        Nominatim=type("Nominatim", (), {"__init__": lambda self, *args, **kwargs: None, "geocode": lambda self, *args, **kwargs: None}),
    )

    stub_modules = {
        "fastapi": _module(
            "fastapi",
            FastAPI=_FastAPI,
            Request=object,
            BackgroundTasks=object,
            Form=lambda default=None, *args, **kwargs: default,
        ),
        "fastapi.templating": _module("fastapi.templating", Jinja2Templates=_Jinja2Templates),
        "fastapi.staticfiles": _module("fastapi.staticfiles", StaticFiles=_StaticFiles),
        "fastapi.responses": _module("fastapi.responses", HTMLResponse=_HTMLResponse),
        "create_map_poster": _module(
            "create_map_poster",
            THEME={},
            get_available_themes=lambda: [],
            create_poster=lambda *args, **kwargs: None,
            load_theme=lambda *args, **kwargs: {},
        ),
        "font_management": _module("font_management", load_fonts=lambda *args, **kwargs: ["stub-font"]),
        "geopy": _module("geopy", geocoders=geocoders),
        "geopy.geocoders": geocoders,
        "osmnx": _module(
            "osmnx",
            settings=types.SimpleNamespace(
                log_console=False,
                use_cache=False,
                http_user_agent="",
                requests_kwargs={},
            ),
        ),
    }

    monkeypatch.delitem(sys.modules, "app.main", raising=False)
    for name, module in stub_modules.items():
        monkeypatch.setitem(sys.modules, name, module)

    importlib.invalidate_caches()
    module = importlib.import_module("app.main")
    try:
        yield module
    finally:
        monkeypatch.delitem(sys.modules, "app.main", raising=False)


class RecordingBackgroundTasks:
    def __init__(self):
        self.calls = []

    def add_task(self, func, **kwargs):
        self.calls.append((func, kwargs))


class FakeLocation:
    def __init__(self, latitude, longitude, address, name=""):
        self.latitude = latitude
        self.longitude = longitude
        self.raw = {"address": address, "name": name}


def test_index_template_exposes_copy_language_selector():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'name="copy_language"' in template
    assert re.search(r'<option\b[^>]*value="en"', template)
    assert re.search(r'<option\b[^>]*value="zh"', template)


def test_index_template_defaults_copy_language_to_english():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert re.search(r'<option\b[^>]*value="en"[^>]*selected', template)


def test_generate_poster_uses_chinese_lookup_for_display_labels(app_main, monkeypatch):
    geocode_calls = []

    class FakeGeolocator:
        def geocode(self, query, **kwargs):
            geocode_calls.append((query, kwargs["language"]))
            if kwargs["language"] == "en":
                return FakeLocation(31.23, 121.47, {"city": "Shanghai", "country": "China"})
            return FakeLocation(31.23, 121.47, {"city": "上海", "country": "中国"})

    background_tasks = RecordingBackgroundTasks()

    monkeypatch.setattr(app_main, "Nominatim", lambda *args, **kwargs: FakeGeolocator())
    monkeypatch.setattr(app_main, "load_fonts", lambda font_name: [font_name])

    response = asyncio.run(
        app_main.generate_poster(
            request=object(),
            background_tasks=background_tasks,
            city="Shanghai",
            country="China",
            copy_language="zh",
        )
    )

    assert geocode_calls == [("Shanghai, China", "en"), ("Shanghai, China", "zh")]
    assert len(background_tasks.calls) == 1
    _, task_kwargs = background_tasks.calls[0]
    assert task_kwargs["city"] == "上海"
    assert task_kwargs["country"] == "中国"
    assert task_kwargs["original_city"] == "Shanghai"
    assert task_kwargs["original_country"] == "China"
    assert task_kwargs["active_fonts"] == ["poster_zh_cn"]
    assert "progress-container" in response.content


def test_generate_poster_logs_and_falls_back_when_chinese_lookup_fails(app_main, monkeypatch, caplog):
    class FakeGeolocator:
        def geocode(self, query, **kwargs):
            if kwargs["language"] == "en":
                return FakeLocation(48.85, 2.35, {"city": "Paris", "country": "France"})
            raise RuntimeError("zh lookup exploded")

    background_tasks = RecordingBackgroundTasks()

    monkeypatch.setattr(app_main, "Nominatim", lambda *args, **kwargs: FakeGeolocator())
    monkeypatch.setattr(app_main, "load_fonts", lambda font_name: [font_name])

    with caplog.at_level(logging.WARNING):
        asyncio.run(
            app_main.generate_poster(
                request=object(),
                background_tasks=background_tasks,
                city="Paris",
                country="France",
                copy_language="zh",
            )
        )

    _, task_kwargs = background_tasks.calls[0]
    assert task_kwargs["city"] == "Paris"
    assert task_kwargs["country"] == "France"
    assert task_kwargs["active_fonts"] is None
    assert "Chinese display lookup failed" in caplog.text


def test_generate_poster_uses_chinese_font_preset_for_manual_chinese_override(app_main, monkeypatch):
    class FakeGeolocator:
        def geocode(self, query, **kwargs):
            return FakeLocation(31.23, 121.47, {"city": "Shanghai", "country": "China"})

    background_tasks = RecordingBackgroundTasks()

    monkeypatch.setattr(app_main, "Nominatim", lambda *args, **kwargs: FakeGeolocator())
    monkeypatch.setattr(app_main, "load_fonts", lambda font_name: [font_name])

    asyncio.run(
        app_main.generate_poster(
            request=object(),
            background_tasks=background_tasks,
            city="Shanghai",
            country="China",
            copy_language="en",
            display_city="上海",
            display_country="中国",
        )
    )

    _, task_kwargs = background_tasks.calls[0]
    assert task_kwargs["city"] == "上海"
    assert task_kwargs["country"] == "中国"
    assert task_kwargs["active_fonts"] == ["poster_zh_cn"]
