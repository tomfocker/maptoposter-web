# Web UI 体验优化与中国本地化实施计划

> **对于代理工人：** 必需的子技能：使用 superpowers:subagent-driven-development (推荐) 或 superpowers:executing-plans 来逐个任务实施此计划。步骤使用复选框 (`- [ ]`) 语法进行跟踪。

**目标：** 解决生成状态黑盒、中文支持、缓存机制不可见以及主题无法预览等问题，提供真正的极客和开箱即用体验。

**架构：** 利用 FastAPI 后台任务（BackgroundTasks）配合 HTMX 的轮询（Polling）机制实现实时进度条；通过解析主题 JSON 文件展示色彩预览；自动检测中文并加载开源思源黑体（Noto Sans SC）。

**技术栈：** HTMX (Polling), Python (sys.stdout 拦截, RegExp), Jinja2 (动态内联 CSS)

---

### 任务 1: 渲染主题的可视化预览

**文件：**
- 修改：`app/main.py`
- 修改：`app/templates/index.html`

- [ ] **步骤 1: 在后端解析主题文件并提取关键颜色**

```python
# app/main.py 的 index 路由
@app.get("/")
async def index(request: Request):
    themes = get_available_themes()
    theme_details = []
    for t in themes:
        try:
            theme_data = load_theme(t)
            theme_details.append({
                "id": t,
                "name": theme_data.get("name", t.capitalize()),
                "colors": [
                    theme_data.get("bg", "#fff"),
                    theme_data.get("road_primary", "#333"),
                    theme_data.get("water", "#888"),
                    theme_data.get("parks", "#aaa")
                ]
            })
        except Exception:
            continue
    return templates.TemplateResponse("index.html", {"request": request, "theme_details": theme_details})
```

- [ ] **步骤 2: 在前端重构主题下拉框，展示色彩条**

修改 `app/templates/index.html`，将原本的 `<select>` 改为更直观的带有色彩预览的选项，或者保留 select 并在旁边动态显示。为了最简单的跨浏览器兼容，我们使用带颜色小方块的自绘列表，或在旁边加上一段文字提示（注：标准的 select option 无法直接改背景色）。我们将改用一个带有 HTMX 绑定的主题卡片网格或隐藏/显示逻辑。

```html
<!-- 在 app/templates/index.html 中的主题选择部分修改为： -->
<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">主题方案 (自带调色板预览)</label>
    <select name="theme" id="theme-select" class="w-full border rounded px-3 py-2" onchange="document.querySelectorAll('.theme-preview').forEach(el => el.classList.add('hidden')); document.getElementById('preview-' + this.value).classList.remove('hidden');">
        {% for t in theme_details %}
        <option value="{{ t.id }}">{{ t.name }}</option>
        {% endfor %}
    </select>
    
    <div class="mt-2 h-6 rounded overflow-hidden flex border">
        {% for t in theme_details %}
        <div id="preview-{{ t.id }}" class="theme-preview w-full flex {% if not loop.first %}hidden{% endif %}">
            <div class="flex-1" style="background-color: {{ t.colors[0] }};"></div>
            <div class="flex-1" style="background-color: {{ t.colors[1] }};"></div>
            <div class="flex-1" style="background-color: {{ t.colors[2] }};"></div>
            <div class="flex-1" style="background-color: {{ t.colors[3] }};"></div>
        </div>
        {% endfor %}
    </div>
</div>
```

- [ ] **步骤 3: 运行验证并提交**
  运行应用并在浏览器查看主题下拉框下方是否出现了随着选择切换的颜色预览条。
  ```bash
  git add app/main.py app/templates/index.html
  git commit -m "feat: add visual color palette preview for themes"
  ```

---

### 任务 2: 城市搜索与显示的解耦及中文字体自动适配

**文件：**
- 修改：`app/main.py`
- 修改：`app/templates/index.html`

- [ ] **步骤 1: 在前端分离搜索字段与显示字段，并增加中文搜索提示**
修改 `index.html`，明确告知用户搜索框支持中文，同时增加“海报显示文字”的覆盖选项。

```html
<!-- 城市搜索 (后台地理编码用) -->
<div class="bg-blue-50 p-4 rounded-lg mb-4">
    <h3 class="text-sm font-semibold text-blue-800 mb-2">1. 搜索目标城市 (支持中文)</h3>
    <div class="grid grid-cols-2 gap-4">
        <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">城市名称</label>
            <input type="text" name="city" placeholder="如: 上海 或 Shanghai" class="w-full border rounded px-3 py-2" required>
        </div>
        <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">国家/地区</label>
            <input type="text" name="country" placeholder="如: 中国 或 China" class="w-full border rounded px-3 py-2" required>
        </div>
    </div>
</div>

<!-- 海报文字覆盖 (显示用) -->
<div class="bg-gray-50 p-4 rounded-lg mb-4 border">
    <h3 class="text-sm font-semibold text-gray-700 mb-2">2. 海报文字覆盖 (选填)</h3>
    <p class="text-xs text-gray-500 mb-3">如果留空，海报上将直接打印上方搜索用的名称。填写此处可实现“搜中文，印英文”或“搜标准名，印别称”。</p>
    <div class="grid grid-cols-2 gap-4">
        <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">海报大标题 (城市)</label>
            <input type="text" name="display_city" placeholder="如: 魔都" class="w-full border rounded px-3 py-2">
        </div>
        <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">海报小标题 (国家)</label>
            <input type="text" name="display_country" placeholder="如: 中国" class="w-full border rounded px-3 py-2">
        </div>
    </div>
</div>
```

- [ ] **步骤 2: 引入中文字体检测逻辑并在后端接收新参数**
  在 `app/main.py` 顶部添加检测函数。在 `generate_poster` 中接收 `display_city` 和 `display_country`，并检测最终要显示的文字是否包含中文，如果包含则自动下载并应用 `Noto Sans SC`。

```python
# 在 app/main.py 顶部添加
import re
from font_management import load_fonts

def has_chinese(text: str) -> bool:
    if not text: return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))

# 在 generate_poster 路由参数中增加：
# display_city: str = Form(""), display_country: str = Form("")

# 在 generate_poster 内部生成前：
final_city = display_city if display_city else city
final_country = display_country if display_country else country

active_fonts = None
if has_chinese(final_city + final_country):
    active_fonts = load_fonts("Noto Sans SC")

# 调用 create_poster 时传入：
# display_city=display_city if display_city else None,
# display_country=display_country if display_country else None,
# fonts=active_fonts
```

- [ ] **步骤 3: 提交代码**
  ```bash
  git add app/main.py app/templates/index.html
  git commit -m "feat: decouple search and display names, auto-detect chinese input for fonts"
  ```

---

### 任务 3: 数据缓存机制的 UI 可见性

**文件：**
- 修改：`app/templates/index.html`

- [ ] **步骤 1: 在界面增加缓存提示**

```html
<!-- 在高级设置或提交按钮附近添加提示： -->
<div class="bg-blue-50 border-l-4 border-blue-400 p-3 mt-4">
    <p class="text-xs text-blue-700">
        <strong>💡 智能缓存机制：</strong> 本工具已开启 OSM 地理数据本地缓存。相同城市的首次下载可能需要 1-2 分钟，之后的任意主题生成将触发<strong>秒开极速渲染</strong>。
    </p>
</div>
```

- [ ] **步骤 2: 提交代码**
  ```bash
  git add app/templates/index.html
  git commit -m "docs: add visibility for the existing caching mechanism in UI"
  ```

---

### 任务 4: 实现实时生成进度轮询 (HTMX Polling)

由于 `OSMnx` 的下载和 `Matplotlib` 的渲染非常耗时，我们将原本同步阻塞的 `/generate` 改为异步任务，并通过拦截 `sys.stdout` 和 `sys.stderr` 将实时的终端日志展现给用户。

**文件：**
- 修改：`app/main.py`
- 修改：`app/templates/index.html`

- [ ] **步骤 1: 创建日志拦截器和全局状态存储**

```python
# app/main.py
import sys
import io
import uuid
from threading import Lock

TASKS_STATE = {}
tasks_lock = Lock()

class LogCapture(io.StringIO):
    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__()
    
    def write(self, s):
        if s.strip():
            with tasks_lock:
                # 仅保留最近的有效日志行
                TASKS_STATE[self.task_id]["log"] = s.strip()
        super().write(s)
        sys.__stdout__.write(s)

# 为了捕获 tqdm，也需要重写 stderr
class ErrorCapture(io.StringIO):
    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__()
    def write(self, s):
        if s.strip() and "%|" in s: # 捕获 tqdm 进度条特征
            with tasks_lock:
                TASKS_STATE[self.task_id]["log"] = s.strip()
        super().write(s)
        sys.__stderr__.write(s)
```

- [ ] **步骤 2: 拆分生成逻辑为后台任务**

```python
# app/main.py
from contextlib import redirect_stdout, redirect_stderr
from fastapi import BackgroundTasks

def run_poster_task(task_id, city, country, point, dist, output_path, map_x_offset, map_y_offset, active_fonts, theme):
    try:
        f_out = LogCapture(task_id)
        f_err = ErrorCapture(task_id)
        with redirect_stdout(f_out), redirect_stderr(f_err):
            create_map_poster.THEME = load_theme(theme)
            create_poster(
                city=city, country=country, point=point, dist=dist,
                output_file=output_path, output_format="png",
                map_x_offset=map_x_offset, map_y_offset=map_y_offset,
                fonts=active_fonts
            )
        with tasks_lock:
            TASKS_STATE[task_id]["status"] = "done"
            TASKS_STATE[task_id]["filename"] = os.path.basename(output_path)
    except Exception as e:
        with tasks_lock:
            TASKS_STATE[task_id]["status"] = "error"
            TASKS_STATE[task_id]["log"] = str(e)

@app.post("/generate")
async def generate_poster(
    request: Request,
    background_tasks: BackgroundTasks,
    city: str = Form(...), country: str = Form(...),
    theme: str = Form("terracotta"), dist: int = Form(4000), dpi: int = Form(300),
    map_x_offset: float = Form(0.0), map_y_offset: float = Form(0.0)
):
    # 保持原有的 Photon 地理编码部分...
    
    task_id = str(uuid.uuid4())
    with tasks_lock:
        TASKS_STATE[task_id] = {"status": "running", "log": "准备启动...", "filename": ""}
    
    background_tasks.add_task(run_poster_task, task_id, city, country, point, dist, output_path, map_x_offset, map_y_offset, active_fonts, theme)
    
    return HTMLResponse(content=f"""
        <div id="progress-container" hx-get="/status/{task_id}" hx-trigger="every 1s" class="text-center p-6 border rounded-lg bg-gray-50">
            <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <h3 class="text-lg font-semibold text-gray-800">正在生成，请耐心等待...</h3>
            <p class="text-sm font-mono text-gray-500 mt-2 bg-black text-green-400 p-2 rounded">_</p>
        </div>
    """)
```

- [ ] **步骤 3: 编写轮询状态查询接口**

```python
# app/main.py
@app.get("/status/{task_id}")
async def get_status(task_id: str):
    with tasks_lock:
        state = TASKS_STATE.get(task_id, {"status": "error", "log": "Task not found"})
    
    if state["status"] == "done":
        filename = state["filename"]
        return HTMLResponse(content=f"""
        <div class="text-center animate-fade-in" hx-trigger="load" hx-get="/history" hx-target="#history-list" hx-swap="innerHTML">
            <img src="/posters/{filename}" class="max-w-full rounded shadow-lg mb-4">
            <div class="flex gap-4 justify-center">
                <a href="/posters/{filename}" download class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">下载 PNG</a>
            </div>
        </div>
        """)
    elif state["status"] == "error":
        return HTMLResponse(content=f"<div class='text-red-500'>生成失败：{state['log']}</div>")
    else:
        # Running state
        return HTMLResponse(content=f"""
        <div id="progress-container" hx-get="/status/{task_id}" hx-trigger="every 1s" class="text-center p-6 border rounded-lg bg-gray-50">
            <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <h3 class="text-lg font-semibold text-gray-800">正在生成，请耐心等待...</h3>
            <p class="text-xs font-mono text-gray-500 mt-2 bg-black text-green-400 p-2 rounded text-left truncate">{state['log']}</p>
        </div>
        """)
```

- [ ] **步骤 4: 移除原有的 htmx-indicator 并清理 HTML**
  在 `index.html` 的 form 中，可以移除 `hx-indicator="#loading-indicator"` 及其对应的 div，因为轮询机制现在完全接管了加载状态的显示。

- [ ] **步骤 5: 验证并提交代码**
  ```bash
  git add app/main.py app/templates/index.html
  git commit -m "feat: implement real-time progress bar with htmx polling and stdout capture"
  ```
