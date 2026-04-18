import asyncio
import logging
import re
from pathlib import Path

from tests._app_main_bootstrap import app_main


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
    assert 'data-ui="refine-panel"' in template
    refine_panel_start = template.index('data-ui="refine-panel"')
    refine_panel = template[refine_panel_start:]
    assert re.search(r'<select\b[^>]*name="copy_language"\b', refine_panel)
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


def test_generate_poster_passes_selected_canvas_size_and_dpi(app_main, monkeypatch):
    class FakeGeolocator:
        def geocode(self, query, **kwargs):
            return FakeLocation(36.06, 120.37, {"city": "Qingdao", "country": "China"})

    background_tasks = RecordingBackgroundTasks()

    monkeypatch.setattr(app_main, "Nominatim", lambda *args, **kwargs: FakeGeolocator())

    asyncio.run(
        app_main.generate_poster(
            request=object(),
            background_tasks=background_tasks,
            city="Qingdao",
            country="China",
            size="8.3x11.7",
            dpi=150,
        )
    )

    _, task_kwargs = background_tasks.calls[0]
    assert task_kwargs["width"] == 8.3
    assert task_kwargs["height"] == 11.7
    assert task_kwargs["dpi"] == 150
