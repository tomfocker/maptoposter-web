# Homepage Output Controls Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move size, DPI, and export format into a prominent homepage output-settings block and remove duplicate helper copy from the refine panel.

**Architecture:** Keep the existing preview-first homepage structure, but split core decisions into three visible groups: location, theme, and output settings. Trim explanatory copy so the outer form stays concise while advanced controls remain available inside the refine panel.

**Tech Stack:** Jinja templates, Tailwind utility classes, custom CSS, pytest template-contract tests

---

### Task 1: Lock the new homepage hierarchy with tests

**Files:**
- Modify: `tests/test_frontend_ui_refresh.py`
- Test: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_promotes_output_controls_above_refine_panel():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    refine_panel_start = template.index('data-ui="refine-panel"')
    pre_refine_panel = template[:refine_panel_start]
    refine_panel = template[refine_panel_start:]

    assert 'data-ui="output-settings"' in pre_refine_panel
    assert 'name="size"' in pre_refine_panel
    assert 'name="dpi"' in pre_refine_panel
    assert 'name="output_format"' in pre_refine_panel
    assert 'name="size"' not in refine_panel
    assert 'name="dpi"' not in refine_panel
    assert 'name="output_format"' not in refine_panel
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_promotes_output_controls_above_refine_panel -q`
Expected: FAIL because `data-ui="output-settings"` does not exist yet and the controls still live inside the refine panel.

- [ ] **Step 3: Write minimal implementation**

```html
<section data-ui="output-settings">
  ...
</section>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_promotes_output_controls_above_refine_panel -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_frontend_ui_refresh.py app/templates/index.html app/static/css/style.css
git commit -m "refactor: promote output controls on homepage"
```

### Task 2: Simplify copy and preserve layout polish

**Files:**
- Modify: `app/templates/index.html`
- Modify: `app/static/css/style.css`
- Test: `tests/test_frontend_ui_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
def test_template_removes_redundant_output_helper_copy():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")

    assert "导出会严格按所选比例和 DPI 计算，不额外裁边。" not in template
    assert "4000-6000 适合紧凑中心区，8000 以上更适合完整城市视图。" not in template
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_removes_redundant_output_helper_copy -q`
Expected: FAIL because the copy is still present.

- [ ] **Step 3: Write minimal implementation**

```html
<section data-ui="output-settings" class="...">
  <label>画布尺寸</label>
  <label>图片质量 (DPI)</label>
  <label>导出格式</label>
</section>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_frontend_ui_refresh.py::test_template_removes_redundant_output_helper_copy -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_frontend_ui_refresh.py app/templates/index.html app/static/css/style.css
git commit -m "style: simplify homepage output copy"
```

### Task 3: Verify the touched homepage paths still pass

**Files:**
- Modify: `app/templates/index.html`
- Modify: `app/static/css/style.css`
- Test: `tests/test_frontend_ui_refresh.py`
- Test: `tests/test_copy_language.py`
- Test: `tests/test_canvas_size.py`

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
git diff -- app/templates/index.html app/static/css/style.css tests/test_frontend_ui_refresh.py
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_frontend_ui_refresh.py app/templates/index.html app/static/css/style.css docs/superpowers/plans/2026-04-18-homepage-output-controls-polish.md
git commit -m "refactor: refine homepage output settings hierarchy"
```
