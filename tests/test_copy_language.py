import re
import sys
import types
from pathlib import Path


def _install_import_stubs():
    if "fastapi" not in sys.modules:
        fastapi = types.ModuleType("fastapi")

        class FastAPI:
            def __init__(self, *args, **kwargs):
                pass

            def mount(self, *args, **kwargs):
                return None

            def get(self, *args, **kwargs):
                def decorator(func):
                    return func

                return decorator

            def post(self, *args, **kwargs):
                def decorator(func):
                    return func

                return decorator

        class Request:
            pass

        class BackgroundTasks:
            def add_task(self, *args, **kwargs):
                return None

        def Form(default=None, *args, **kwargs):
            return default

        fastapi.FastAPI = FastAPI
        fastapi.Request = Request
        fastapi.Form = Form
        fastapi.BackgroundTasks = BackgroundTasks
        sys.modules["fastapi"] = fastapi

        templating = types.ModuleType("fastapi.templating")

        class Jinja2Templates:
            def __init__(self, *args, **kwargs):
                pass

            def TemplateResponse(self, *args, **kwargs):
                return {"args": args, "kwargs": kwargs}

        templating.Jinja2Templates = Jinja2Templates
        sys.modules["fastapi.templating"] = templating

        staticfiles = types.ModuleType("fastapi.staticfiles")

        class StaticFiles:
            def __init__(self, *args, **kwargs):
                pass

        staticfiles.StaticFiles = StaticFiles
        sys.modules["fastapi.staticfiles"] = staticfiles

        responses = types.ModuleType("fastapi.responses")

        class HTMLResponse:
            def __init__(self, content="", *args, **kwargs):
                self.content = content

        responses.HTMLResponse = HTMLResponse
        sys.modules["fastapi.responses"] = responses

    if "create_map_poster" not in sys.modules:
        create_map_poster = types.ModuleType("create_map_poster")
        create_map_poster.THEME = {}
        create_map_poster.get_available_themes = lambda: []
        create_map_poster.create_poster = lambda *args, **kwargs: None
        create_map_poster.load_theme = lambda *args, **kwargs: {}
        sys.modules["create_map_poster"] = create_map_poster

    if "font_management" not in sys.modules:
        font_management = types.ModuleType("font_management")
        font_management.load_fonts = lambda *args, **kwargs: ["stub-font"]
        sys.modules["font_management"] = font_management

    if "geopy" not in sys.modules:
        geopy = types.ModuleType("geopy")
        geocoders = types.ModuleType("geopy.geocoders")

        class Nominatim:
            def __init__(self, *args, **kwargs):
                pass

            def geocode(self, *args, **kwargs):
                return None

        geocoders.Nominatim = Nominatim
        geopy.geocoders = geocoders
        sys.modules["geopy"] = geopy
        sys.modules["geopy.geocoders"] = geocoders

    if "osmnx" not in sys.modules:
        osmnx = types.ModuleType("osmnx")

        class Settings:
            log_console = False
            use_cache = False
            http_user_agent = ""
            requests_kwargs = {}

        osmnx.settings = Settings()
        sys.modules["osmnx"] = osmnx


_install_import_stubs()

from app.main import choose_poster_labels, has_chinese


def test_index_template_exposes_copy_language_selector():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'name="copy_language"' in template
    assert re.search(r'<option\b[^>]*value="en"', template)
    assert re.search(r'<option\b[^>]*value="zh"', template)


def test_index_template_defaults_copy_language_to_english():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert re.search(r'<option\b[^>]*value="en"[^>]*selected', template)


def test_choose_poster_labels_keeps_existing_english_default():
    city, country = choose_poster_labels(
        copy_language="en",
        display_city="",
        display_country="",
        english_city="Shanghai",
        english_country="China",
        chinese_city="上海",
        chinese_country="中国",
    )

    assert city == "Shanghai"
    assert country == "China"


def test_choose_poster_labels_prefers_chinese_when_selected():
    city, country = choose_poster_labels(
        copy_language="zh",
        display_city="",
        display_country="",
        english_city="Shanghai",
        english_country="China",
        chinese_city="上海",
        chinese_country="中国",
    )

    assert city == "上海"
    assert country == "中国"


def test_choose_poster_labels_keeps_manual_override_highest_priority():
    city, country = choose_poster_labels(
        copy_language="zh",
        display_city="魔都",
        display_country="中国",
        english_city="Shanghai",
        english_country="China",
        chinese_city="上海",
        chinese_country="中国",
    )

    assert city == "魔都"
    assert country == "中国"


def test_choose_poster_labels_falls_back_to_english_when_chinese_missing():
    city, country = choose_poster_labels(
        copy_language="zh",
        display_city="",
        display_country="",
        english_city="Paris",
        english_country="France",
        chinese_city="",
        chinese_country="",
    )

    assert city == "Paris"
    assert country == "France"


def test_has_chinese_detects_chinese_copy():
    assert has_chinese("上海中国")
