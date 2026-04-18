# Homepage Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the homepage foldout pattern, turn the full theme palette gallery into an internal modal, and strip remaining top-of-page microcopy so the interface feels more direct.

**Architecture:** Keep the existing preview-first two-column layout and existing form field names, but reorganize the left column into always-visible grouped cards. Replace the refine toggle and hidden panel with persistent sections, and move the theme gallery into a modal that is opened from the theme card and managed by lightweight inline JavaScript.

**Tech Stack:** Jinja templates, Tailwind utility classes, custom CSS, inline JavaScript, pytest template-contract tests

---

## File Structure

- `app/templates/base.html`
  Owns the top navigation copy. This file will lose the extra right-side sentence and keep only the minimal brand/title shell.
- `app/templates/index.html`
  Owns the homepage form structure, the theme preview, the theme modal markup, and the small inline JS that wires theme preview and modal open/close behavior.
- `app/static/css/style.css`
  Owns the visual treatment for the always-visible grouped cards and the new internal modal shell/backdrop.
- `tests/test_frontend_ui_refresh.py`
  Owns the template contract assertions for homepage structure. This is where we lock in the removal of the refine panel and the presence of the theme modal.

### Task 1: Lock the simplified homepage contract with failing tests

**Files:**
- Modify: `tests/test_frontend_ui_refresh.py`
- Test: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_replaces_refine_panel_with_always_visible_sections():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert 'data-ui="refine-toggle"' not in template
    assert 'data-ui="refine-panel"' not in template
    assert 'data-ui="copy-settings"' in template
    assert 'data-ui="composition-settings"' in template


def test_template_moves_theme_gallery_into_modal_container():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    modal_start = template.index('data-ui="theme-modal"')
    pre_modal = template[:modal_start]
    modal = template[modal_start:]

    assert 'data-ui="theme-gallery"' not in pre_modal
    assert 'data-ui="theme-gallery"' in modal
    assert "查看全部主题" in template


def test_template_removes_remaining_top_level_microcopy():
    base_template = Path("app/templates/base.html").read_text(encoding="utf-8")
    index_template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert "首屏只保留最常用操作，完整主题和精修设置都收进下方折叠区。" not in base_template
    assert "先输入地点与主题，右侧会即时承接生成进度和结果。" not in index_template
    assert "支持 PNG、PDF 与 SVG 导出。" not in index_template
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_replaces_refine_panel_with_always_visible_sections tests/test_frontend_ui_refresh.py::test_template_moves_theme_gallery_into_modal_container tests/test_frontend_ui_refresh.py::test_template_removes_remaining_top_level_microcopy -q`
Expected: FAIL because the refine toggle and panel still exist, the theme gallery is still inline, and the extra copy is still present.

- [ ] **Step 3: Write minimal implementation**

```python
# No production Python changes in this task.
# The green step is template-only: remove refine markers, add modal markers, and remove copy strings.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_replaces_refine_panel_with_always_visible_sections tests/test_frontend_ui_refresh.py::test_template_moves_theme_gallery_into_modal_container tests/test_frontend_ui_refresh.py::test_template_removes_remaining_top_level_microcopy -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_frontend_ui_refresh.py app/templates/base.html app/templates/index.html
git commit -m "test: lock homepage simplification contract"
```

### Task 2: Replace the foldout with always-visible grouped cards

**Files:**
- Modify: `app/templates/index.html`
- Modify: `app/static/css/style.css`
- Test: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_exposes_always_visible_settings_groups():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    for marker in (
        'data-ui="theme-picker"',
        'data-ui="output-settings"',
        'data-ui="copy-settings"',
        'data-ui="composition-settings"',
    ):
        assert marker in template
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_exposes_always_visible_settings_groups -q`
Expected: FAIL because `copy-settings` and `composition-settings` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```html
<section data-ui="copy-settings" class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
  <h3 class="text-sm font-semibold text-slate-900">文字覆盖</h3>
  ...
</section>

<section data-ui="composition-settings" class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
  <h3 class="text-sm font-semibold text-slate-900">构图微调</h3>
  ...
</section>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_exposes_always_visible_settings_groups -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/index.html app/static/css/style.css tests/test_frontend_ui_refresh.py
git commit -m "refactor: replace homepage foldout with visible groups"
```

### Task 3: Move the theme gallery into an internal modal

**Files:**
- Modify: `app/templates/index.html`
- Modify: `app/static/css/style.css`
- Test: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_includes_theme_modal_controls():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert 'data-ui="theme-modal"' in template
    assert 'data-ui="theme-modal-open"' in template
    assert 'data-ui="theme-modal-close"' in template
    assert "查看全部主题" in template
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_includes_theme_modal_controls -q`
Expected: FAIL because the modal container and controls do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```html
<button type="button" data-ui="theme-modal-open" class="...">查看全部主题</button>

<div data-ui="theme-modal" hidden class="...">
  <div data-ui="theme-modal-backdrop" class="..."></div>
  <div class="...">
    <button type="button" data-ui="theme-modal-close">关闭</button>
    <div data-ui="theme-gallery" class="grid gap-3 sm:grid-cols-2">
      ...
    </div>
  </div>
</div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_includes_theme_modal_controls -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/index.html app/static/css/style.css tests/test_frontend_ui_refresh.py
git commit -m "feat: show theme gallery in homepage modal"
```

### Task 4: Remove the remaining top-of-page explanatory copy

**Files:**
- Modify: `app/templates/base.html`
- Modify: `app/templates/index.html`
- Test: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_keeps_only_minimal_header_and_preview_copy():
    base_template = Path("app/templates/base.html").read_text(encoding="utf-8")
    index_template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert "地图海报工作室" in base_template
    assert "输入地点，快速生成一张可下载的城市海报" in base_template
    assert "先输入地点与主题，右侧会即时承接生成进度和结果。" not in index_template
    assert "支持 PNG、PDF 与 SVG 导出。" not in index_template
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_keeps_only_minimal_header_and_preview_copy -q`
Expected: FAIL because the extra copy is still present.

- [ ] **Step 3: Write minimal implementation**

```html
<div class="space-y-1">
  <h2 class="text-2xl font-semibold text-slate-900">把城市变成一张可以马上预览的海报</h2>
</div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_keeps_only_minimal_header_and_preview_copy -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/base.html app/templates/index.html tests/test_frontend_ui_refresh.py
git commit -m "style: trim homepage microcopy"
```

### Task 5: Final verification and cleanup

**Files:**
- Modify: `app/templates/base.html`
- Modify: `app/templates/index.html`
- Modify: `app/static/css/style.css`
- Modify: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Run focused regression tests**

```bash
python3 -m pytest tests/test_frontend_ui_refresh.py tests/test_copy_language.py tests/test_canvas_size.py -q
```

- [ ] **Step 2: Run template compile verification**

```bash
python3 -m compileall app
```

- [ ] **Step 3: Review the final diff**

```bash
git diff -- app/templates/base.html app/templates/index.html app/static/css/style.css tests/test_frontend_ui_refresh.py
```

- [ ] **Step 4: Commit**

```bash
git add app/templates/base.html app/templates/index.html app/static/css/style.css tests/test_frontend_ui_refresh.py docs/superpowers/plans/2026-04-18-homepage-simplification.md
git commit -m "refactor: simplify homepage layout"
```
