# Chinese Poster Copy Option Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in Chinese poster-copy mode that leaves the default English behavior unchanged, and update compose/documentation so slim and offline-enhanced usage are both clearly documented.

**Architecture:** Keep the existing geocoding and poster pipeline intact, but add a small copy-language branch in the FastAPI form handler. The UI will submit a new `copy_language` field, the backend will resolve Chinese city/country labels only when requested, and existing manual overrides will still win. Documentation changes will clarify both deployment modes and note that the Chinese copy option works in either mode.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2 templates, Geopy Nominatim, pytest, Docker Compose

---

## File Map

### New Files

- `tests/test_copy_language.py`
  Unit tests for the new `copy_language` selector and copy-resolution priority rules.
- `tests/test_deployment_docs.py`
  Text-level tests that guard the slim/ offline-enhanced README and compose wording.

### Modified Files

- `app/main.py`
  Add form field handling, Chinese copy resolution helpers, and fallback behavior while preserving the current English default.
- `app/templates/index.html`
  Add the poster-copy language selector and helper text.
- `README.md`
  Clarify slim online mode vs offline-enhanced mode and document the optional Chinese copy feature.
- `docker-compose.offline-cn.yml`
  Improve comments or service metadata so the offline-enhanced usage is self-explanatory.

## Task 1: Add The Poster Copy Language Selector In The UI

**Files:**
- Modify: `app/templates/index.html`
- Create: `tests/test_copy_language.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_copy_language.py
from pathlib import Path


def test_index_template_exposes_copy_language_selector():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'name="copy_language"' in template
    assert "英文（默认）" in template
    assert "中文" in template


def test_index_template_defaults_copy_language_to_english():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'option value="en" selected' in template
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_copy_language.py -v`

Expected: FAIL because the selector markup does not yet exist.

- [ ] **Step 3: Write minimal implementation**

```html
<!-- app/templates/index.html -->
<div class="mt-3">
  <label class="block text-xs font-medium text-gray-700 mb-1">海报文案语言</label>
  <select name="copy_language" class="w-full border rounded px-3 py-2 text-sm">
    <option value="en" selected>英文（默认）</option>
    <option value="zh">中文</option>
  </select>
  <p class="mt-1 text-[11px] text-gray-500">
    默认保持原版英文文案。选择中文后，仅替换自动生成的城市/国家名称；手动填写的标题副标题优先。
  </p>
</div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_copy_language.py -v`

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add app/templates/index.html tests/test_copy_language.py
git commit -m "feat: add poster copy language selector"
```

## Task 2: Add Copy-Language Resolution And Chinese Fallback Handling

**Files:**
- Modify: `app/main.py`
- Modify: `tests/test_copy_language.py`

- [ ] **Step 1: Write the failing tests**

Append these tests to `tests/test_copy_language.py`:

```python
from app.main import choose_poster_labels, has_chinese


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_copy_language.py -v`

Expected: FAIL because `choose_poster_labels` does not yet exist in `app/main.py`.

- [ ] **Step 3: Write minimal implementation**

Add these helpers to `app/main.py` near the existing text-handling logic:

```python
def choose_poster_labels(
    copy_language: str,
    display_city: str,
    display_country: str,
    english_city: str,
    english_country: str,
    chinese_city: str,
    chinese_country: str,
) -> tuple[str, str]:
    if display_city or display_country:
        return (
            display_city if display_city else (chinese_city if copy_language == "zh" and chinese_city else english_city),
            display_country if display_country else (chinese_country if copy_language == "zh" and chinese_country else english_country),
        )

    if copy_language == "zh" and chinese_city and chinese_country:
        return chinese_city, chinese_country

    return english_city, english_country
```

Update the form signature:

```python
copy_language: str = Form("en"),
```

Update the geocoding branch so Chinese mode performs a second display-only lookup:

```python
zh_city = ""
zh_country = ""
if copy_language == "zh":
    try:
        zh_location = geolocator.geocode(
            f"{city}, {country}",
            timeout=10,
            language="zh",
            exactly_one=True,
            addressdetails=True,
        )
        if zh_location:
            zh_address = zh_location.raw.get("address", {})
            zh_city = zh_address.get("city") or zh_address.get("town") or zh_address.get("county") or zh_address.get("village") or zh_location.raw.get("name") or ""
            zh_country = zh_address.get("country", "")
    except Exception:
        zh_city = ""
        zh_country = ""
```

Replace the current final label selection with:

```python
final_city, final_country = choose_poster_labels(
    copy_language=copy_language,
    display_city=display_city,
    display_country=display_country,
    english_city=en_city,
    english_country=en_country,
    chinese_city=zh_city,
    chinese_country=zh_country,
)
```

Keep the existing font-loading branch:

```python
active_fonts = None
if has_chinese(final_city + final_country):
    active_fonts = load_fonts("Noto Sans SC")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_copy_language.py -v`

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_copy_language.py
git commit -m "feat: add optional chinese poster copy mode"
```

## Task 3: Clarify Slim And Offline-Enhanced Usage In Documentation

**Files:**
- Modify: `README.md`
- Modify: `docker-compose.offline-cn.yml`
- Create: `tests/test_deployment_docs.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_deployment_docs.py
from pathlib import Path


def test_readme_mentions_slim_and_offline_enhanced_modes():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "精简在线版" in readme
    assert "离线增强版" in readme
    assert "中文文案" in readme


def test_offline_compose_documents_seeded_cache_behavior():
    compose = Path("docker-compose.offline-cn.yml").read_text(encoding="utf-8")
    assert "首次启动" in compose
    assert "在线补全" in compose
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_deployment_docs.py -v`

Expected: FAIL because the new wording is not yet present.

- [ ] **Step 3: Write minimal implementation**

Add a short deployment guide section to `README.md` like:

```markdown
## 部署模式说明

### 精简在线版

- 使用 `tomfocker/maptoposter-web:latest` 或 `tomfocker/maptoposter-web:v1.0`
- 首次请求时在线下载地图数据
- 后续请求会复用本地缓存
- 支持可选中文文案模式，默认仍为英文

### 离线增强版

- 使用 `docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml up -d`
- 首次启动时把预置缓存灌入命名卷
- 离线缓存未命中时仍然会在线补全
- 同样支持可选中文文案模式
```

Add comments to `docker-compose.offline-cn.yml`:

```yaml
services:
  maptoposter:
    # 离线增强版：主应用仍然是精简镜像，地图缓存通过命名卷复用
  cache-init:
    # 首次启动时把离线种子缓存复制进命名卷；未命中区域后续仍可在线补全
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_deployment_docs.py -v`

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add README.md docker-compose.offline-cn.yml tests/test_deployment_docs.py
git commit -m "docs: clarify slim and offline deployment modes"
```

## Task 4: Final Verification

**Files:**
- Verify only

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_copy_language.py tests/test_deployment_docs.py -v
```

Expected: PASS

- [ ] **Step 2: Re-run existing regression tests that touch related docs/compose behavior**

Run:

```bash
python3 -m pytest tests/test_copy_semantics.py tests/test_offline_compose.py -v
```

Expected: PASS

- [ ] **Step 3: Validate compose rendering**

Run:

```bash
docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml config
```

Expected: exits `0`

- [ ] **Step 4: Commit verification-safe follow-up changes only if needed**

```bash
git status --short
```

Expected: clean working tree or only intentional changes already committed

## Self-Review

### Spec Coverage

- Optional Chinese copy mode without changing default English behavior: covered by Task 1 and Task 2.
- Manual overrides keep highest priority: covered by Task 2 tests and helper logic.
- Compose and docs clarify slim vs offline-enhanced modes: covered by Task 3.
- Minimal testing around selector behavior and safe fallback: covered by Task 2 and Task 4.

### Placeholder Scan

- No `TODO`, `TBD`, or abstract "implement later" steps remain.
- Every task includes exact file paths, commands, and concrete code snippets.

### Type Consistency

- `copy_language` uses `en` / `zh` consistently in UI and backend.
- `choose_poster_labels` is the single copy-priority helper referenced across the plan.

## Suggested Verification Sequence

```bash
python3 -m pytest tests/test_copy_language.py tests/test_deployment_docs.py tests/test_copy_semantics.py tests/test_offline_compose.py -v
docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml config
```
