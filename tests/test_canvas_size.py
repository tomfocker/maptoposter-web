from pathlib import Path

from app.poster_export import build_save_kwargs


def test_build_save_kwargs_preserves_canvas_size_for_png():
    save_kwargs = build_save_kwargs(output_format="png", dpi=150)

    assert save_kwargs["facecolor"] == "#FFFFFF"
    assert save_kwargs["dpi"] == 150
    assert "bbox_inches" not in save_kwargs
    assert "pad_inches" not in save_kwargs


def test_build_save_kwargs_does_not_force_dpi_for_vector_formats():
    save_kwargs = build_save_kwargs(output_format="pdf", dpi=600)

    assert save_kwargs["facecolor"] == "#FFFFFF"
    assert "dpi" not in save_kwargs


def test_index_template_includes_original_project_size_presets():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert 'value="3.6x3.6"' in template
    assert "Instagram" in template
    assert 'value="3.6x6.4"' in template
    assert "手机壁纸" in template
    assert 'value="6.4x3.6"' in template
    assert "高清横版" in template
    assert 'value="12.8x7.2"' in template
    assert "4K 横版" in template
    assert 'value="8.3x11.7"' in template
    assert "A4" in template
