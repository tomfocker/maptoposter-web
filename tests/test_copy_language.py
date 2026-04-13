import re
from pathlib import Path


def test_index_template_exposes_copy_language_selector():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'name="copy_language"' in template
    assert re.search(r'<option\b[^>]*value="en"', template)
    assert re.search(r'<option\b[^>]*value="zh"', template)


def test_index_template_defaults_copy_language_to_english():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert re.search(r'<option\b[^>]*value="en"[^>]*selected', template)
