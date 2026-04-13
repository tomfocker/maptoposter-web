# MapToPoster Web 🌍🎨

> 本项目是基于 [originalankur/maptoposter](https://github.com/originalankur/maptoposter) 核心渲染引擎开发的 **Web 可视化面板及 Docker 镜像增强版**。

Generate beautiful, minimalist map posters for any city in the world. Now with a modern **Web UI, Docker support, and deep Chinese localization**!

<img src="posters/singapore_neon_cyberpunk_20260118_153328.png" width="250">
<img src="posters/dubai_midnight_blue_20260118_140807.png" width="250">

## ✨ 核心增强功能 (Web UI Features)

相比原版的纯 CLI 工具，本增强版提供了极致的“开箱即用”体验：

- 🚀 **开箱即用的 Docker 支持**：无需再痛苦地在本地编译安装 `GDAL`、`GEOS` 等复杂的地理库，一个命令即可运行。
- 🖥️ **现代化的 Web 仪表盘**：告别黑框框，通过直观的浏览器界面配置你的海报。
- 🇨🇳 **深度中文本地化**：
  - **搜索解耦**：底层支持通过中文搜索全球城市，并自动提取标准英文名进行极具设计感的排版渲染。
  - **中文字体支持**：支持手动覆盖海报文字为中文，并自动加载思源黑体，解决乱码问题。
  - **主题翻译**：内置 47 款绝美主题（含 30+ 中国特色主题）全部经过中文意译。
- 🎨 **色彩预览与构图微调**：实时预览主题色调，支持 X/Y 轴偏移、道路缩放及多种画布尺寸（如手机壁纸）。
- ⏱️ **实时进度反馈**：采用 HTMX 轮询技术，在网页上实时展示下载、渲染日志，生成过程不再是黑盒。

---

## 🚀 快速开始 (Quick Start)

### 方案 A：使用 Docker Compose (强烈推荐)

这是最简单、最稳健的运行方式。

1. **下载或创建 `docker-compose.yml`**：
   ```yaml
   services:
     maptoposter:
       image: tomfocker/maptoposter-web:latest
       container_name: maptoposter-web
       ports:
         - "8000:8000"
       volumes:
         - ./posters:/app/posters  # 海报输出目录
         - ./cache:/app/cache      # 地图数据缓存目录
       restart: always
   ```

2. **启动服务**：
   ```bash
   docker-compose up -d
   ```

3. **访问**：
   打开浏览器访问 `http://localhost:8000` 即可开始创作。

---

### 方案 A-1：使用中国主要城市离线缓存模式

如果你希望首次启动就内置中国主要城市的常用地图缓存，同时继续保留在线补全能力，可以使用：

```bash
docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml up -d
```

此模式会通过命名卷初始化离线缓存数据。后续如果你请求了离线包之外的城市或更大的地图范围，程序仍会继续在线下载并把新数据写回缓存卷。

这里的 `distance`/`dist` 表示海报的地图范围参数，而不是严格的真实半径。推荐区间与原项目保持一致：

- `4000-6000`：小而密的城市中心
- `8000-12000`：中等城市或聚焦 downtown
- `15000-20000`：大都市更完整的城市视图

---

### 方案 B：本地 Python 环境 (开发模式)

如果你想在本地开发或不想使用 Docker：

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
2. **运行应用**：
   ```bash
   python app/main.py
   ```

---

## 📐 高级设置指南

- **精准定位**：中文搜索强烈建议加上“市”、“县”或“区”后缀（如：`黄骅市`），以获得最精准的行政中心坐标。
- **构图微调**：利用水平/垂直偏移功能，可以完美避开水印或让特定的河流、地标处于视觉中心。
- **导出格式**：除了 PNG，本工具还支持 **PDF** 和 **SVG** 矢量格式，方便后期进行大幅面印刷或专业设计修改。

---

## 🛠️ 关于原项目 (Original Project)

本项目深度集成了 [originalankur/maptoposter](https://github.com/originalankur/maptoposter) 的渲染逻辑。

<details>
<summary>点击展开 CLI 原始参数参考 (For Advanced CLI Users)</summary>

### Required Options
| Option | Short | Description |
|--------|-------|-------------|
| `--city` | `-c` | City name (used for geocoding) |
| `--country` | `-C` | Country name (used for geocoding) |

### Optional Flags
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--latitude` | `-lat` | Override latitude center point | |
| `--longitude` | `-long` | Override longitude center point | |
| `--theme` | `-t` | Theme name | `terracotta` |
| `--distance` | `-d` | Poster map range parameter | `18000` |
| `--width` | `-W` | Image width in inches | `12` |
| `--height` | `-H` | Image height in inches | `16` |

更多高级 CLI 操作请参考原仓库文档。
</details>

---

## 🤝 贡献与维护

如果你在使用过程中发现任何 Bug，或有新的主题建议，欢迎在 GitHub 上提交 Issue 或 Pull Request。

- **Author**: tomfocker
- **Core Engine**: originalankur
- **License**: MIT
