import importlib
import sys
import types

import pytest


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    return module


class TemplateResponseStub:
    def __init__(self, template_name, context, **kwargs):
        self.template_name = template_name
        self.context = context
        self.request = context.get("request")
        self.kwargs = kwargs


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

        def delete(self, *args, **kwargs):
            return lambda func: func

    class _Jinja2Templates:
        def __init__(self, *args, **kwargs):
            pass

        def TemplateResponse(self, template_name, context, *args, **kwargs):
            return TemplateResponseStub(template_name, context, **kwargs)

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
