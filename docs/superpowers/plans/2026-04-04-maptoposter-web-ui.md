# MapToPoster Web UI & Docker 实施计划

> **对于代理工人：** 必需的子技能：使用 superpowers:subagent-driven-development (推荐) 或 superpowers:executing-plans 来逐个任务实施此计划。步骤使用复选框 (`- [ ]`) 语法进行跟踪。

**目标：** 为 MapToPoster 构建一个基于 FastAPI 的 Web UI，并将其打包成轻量级、开箱即用的 Docker 镜像。

**架构：** 采用单体 FastAPI 应用，利用 Jinja2 和 HTMX 实现流畅的“单页”交互体验。后端直接调用现有的 Python 地理数据处理逻辑，并使用多阶段构建压缩 Docker 镜像。

**技术栈：** FastAPI, Jinja2, HTMX, Tailwind CSS, OSMnx, Matplotlib, Docker.

---

## 文件结构

- **`app/`**: Web 应用源代码
  - `main.py`: FastAPI 主入口，负责路由和任务调度。
  - `history.py`: 处理海报生成历史的持久化 (JSON/SQLite)。
  - `templates/`: Jinja2 HTML 模板。
    - `index.html`: 仪表盘主页面。
    - `components/`: HTMX 组件片段。
  - `static/`: 静态资源 (CSS, JS)。
- **`Dockerfile`**: 多阶段构建配置。
- **`docker-compose.yml`**: 一键启动配置。

---

## 任务列表

### 任务 1: 初始化项目结构与核心依赖

**文件：**
- 修改：`requirements.txt`
- 创建：`app/__init__.py`, `app/main.py`

- [ ] **步骤 1: 更新 `requirements.txt` 以包含 Web 依赖**
  添加 `fastapi`, `uvicorn`, `jinja2`, `python-multipart` 到依赖列表。

- [ ] **步骤 2: 编写基础 FastAPI 应用骨架**
  创建 `app/main.py`，配置静态文件路径、模板引擎和根路由。

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="MapToPoster Web")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/posters", StaticFiles(directory="posters"), name="posters")
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

- [ ] **步骤 3: 运行并验证基础应用启动**
  `uvicorn app.main:app --reload` (预期：访问 http://localhost:8000 看到模板错误或空白页)。

- [ ] **步骤 4: 提交代码**
  `git add requirements.txt app/ && git commit -m "chore: initialize fastapi structure"`

---

### 任务 2: 编写 Web UI 界面 (Dashboard)

**文件：**
- 创建：`app/templates/index.html`, `app/templates/base.html`, `app/static/css/style.css`

- [ ] **步骤 1: 创建基础模板 `base.html`**
  集成 Tailwind CSS (CDN) 和 HTMX 脚本。

- [ ] **步骤 2: 设计仪表盘布局 `index.html`**
  左侧参数区（地址、主题、高级设置），右侧预览区。

- [ ] **步骤 3: 验证界面在浏览器中正常渲染**
  (预期：看到带有侧边栏和预览区的精美 UI)。

- [ ] **步骤 4: 提交代码**
  `git add app/templates/ app/static/ && git commit -m "feat: design dashboard layout with tailwind and htmx"`

---

### 任务 3: 实现 API 路由与地图生成集成

**文件：**
- 修改：`app/main.py`
- 修改：`create_map_poster.py` (如有必要，导出核心函数)

- [ ] **步骤 1: 实现主题选择 API**
  从 `create_map_poster.py` 的 `get_available_themes()` 获取数据。

- [ ] **步骤 2: 实现城市搜索 API (Nominatim)**
  调用 `geopy` 进行地理编码，并返回坐标。

- [ ] **步骤 3: 实现异步生成任务**
  使用 FastAPI 的 `BackgroundTasks` 调用 `create_poster` 函数。
  确保生成过程不阻塞 Web 服务器。

- [ ] **步骤 4: 运行并验证生成流程**
  (预期：提交表单后，后台开始下载地图并渲染，完成后可在页面预览)。

- [ ] **步骤 5: 提交代码**
  `git add app/main.py && git commit -m "feat: integrate map generation api and search"`

---

### 任务 4: 历史记录管理与持久化

**文件：**
- 创建：`app/history.py`
- 修改：`app/main.py`

- [ ] **步骤 1: 编写历史记录管理逻辑**
  使用一个简单的 JSON 文件记录每次生成的 `city`, `theme`, `filename` 和 `timestamp`。

- [ ] **步骤 2: 实现历史列表 API**
  在页面右下方或侧边栏底部展示最近生成的 5-10 张海报缩略图。

- [ ] **步骤 3: 验证持久化功能**
  刷新页面后，之前的生成历史应依然存在。

- [ ] **步骤 4: 提交代码**
  `git add app/history.py app/main.py && git commit -m "feat: add generation history and persistence"`

---

### 任务 5: Docker 化 (多阶段构建)

**文件：**
- 创建：`Dockerfile`, `.dockerignore`, `docker-compose.yml`

- [ ] **步骤 1: 编写多阶段 Dockerfile**
  - **Stage 1 (Build):** 安装编译环境和庞大的 GIS 依赖包。
  - **Stage 2 (Runtime):** 仅保留运行时所需的 Python 环境和静态资源。

- [ ] **步骤 2: 配置 `.dockerignore`**
  排除 `cache/`, `posters/`, `.git` 等不必要文件。

- [ ] **步骤 3: 构建并测试镜像体积**
  `docker build -t maptoposter-web .` (预期：体积控制在 800MB 左右)。

- [ ] **步骤 4: 编写 `docker-compose.yml`**
  配置卷挂载，确保存储历史。

- [ ] **步骤 5: 提交代码**
  `git add Dockerfile .dockerignore docker-compose.yml && git commit -m "feat: add dockerization with multi-stage build"`

---

### 任务 6: 最终集成测试与文档更新

- [ ] **步骤 1: 进行全流程测试**
  从 `docker-compose up` 启动，到生成第一张海报并下载。

- [ ] **步骤 2: 更新 `README.md`**
  添加 Docker 启动说明和 Web UI 截图（如果有的话）。

- [ ] **步骤 3: 提交代码**
  `git add README.md && git commit -m "docs: update readme with docker instructions"`
