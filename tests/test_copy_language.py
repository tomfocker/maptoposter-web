import re
from pathlib import Path


def test_index_template_exposes_copy_language_selector():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'name="copy_language"' in template
    assert "英文（默认）" in template
    assert "中文" in template


def test_index_template_defaults_copy_language_to_english():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert re.search(r'<option\b[^>]*value="en"[^>]*selected', template)
