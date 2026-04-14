from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
import asyncio
import sys
import io
import uuid
import logging
from threading import Lock
from typing import List
from create_map_poster import get_available_themes, create_poster, load_theme
from font_management import load_fonts
import create_map_poster
from geopy.geocoders import Nominatim
import osmnx as ox
from app.poster_copy import choose_poster_labels, has_chinese

# 配置 OSMnx：开启控制台日志并使用默认设置
ox.settings.log_console = True
ox.settings.use_cache = True
# 伪装一个更真实的浏览器/应用 User-Agent，避免被 nginx 403 直接拦截
ox.settings.http_user_agent = "MapToPoster-Web/1.0 (Mozilla/5.0; compatible)"
# 强制 OSMnx 不使用代理（绕过环境中的被拉黑代理 IP），走本地直连网络
ox.settings.requests_kwargs = {"proxies": {"http": None, "https": None}}

app = FastAPI(title="MapToPoster Web")

# 确保必要的目录存在
POSTERS_DIR = "posters"
os.makedirs(POSTERS_DIR, exist_ok=True)

# 挂载静态文件和海报目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/posters", StaticFiles(directory="posters"), name="posters")

templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# --- 任务状态管理与日志拦截 ---
TASKS_STATE = {}
tasks_lock = Lock()

class LogCapture(io.StringIO):
    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__()
    
    def write(self, s):
        if s.strip():
            with tasks_lock:
                TASKS_STATE[self.task_id]["log"] = s.strip()
        super().write(s)
        sys.__stdout__.write(s)

class ErrorCapture(io.StringIO):
    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__()
    def write(self, s):
        if s.strip() and "%|" in s: # 捕获 tqdm 进度条
            with tasks_lock:
                TASKS_STATE[self.task_id]["log"] = s.strip()
        super().write(s)
        sys.__stderr__.write(s)

from contextlib import redirect_stdout, redirect_stderr

def run_poster_task(task_id, city, country, point, dist, output_path, map_x_offset, map_y_offset, active_fonts, theme, road_width_scale, original_city, original_country, width, height, dpi, output_format):
    try:
        f_out = LogCapture(task_id)
        f_err = ErrorCapture(task_id)
        with redirect_stdout(f_out), redirect_stderr(f_err):
            # 1. 加载并设置全局主题
            create_map_poster.THEME = load_theme(theme)
            
            # 2. 如果提供了自定义道路缩放，则与主题自带的缩放叠加
            current_scale = create_map_poster.THEME.get("road_width_scale", 1.0)
            create_map_poster.THEME["road_width_scale"] = current_scale * road_width_scale
            
            # 3. 生成海报
            create_poster(
                city=city if city else original_city,
                country=country if country else original_country,
                point=point,
                dist=dist,
                output_file=output_path,
                output_format=output_format,
                width=width,
                height=height,
                dpi=dpi,
                map_x_offset=map_x_offset,
                map_y_offset=map_y_offset,
                fonts=active_fonts
            )
        with tasks_lock:
            TASKS_STATE[task_id]["status"] = "done"
            TASKS_STATE[task_id]["filename"] = os.path.basename(output_path)
    except Exception as e:
        with tasks_lock:
            TASKS_STATE[task_id]["status"] = "error"
            TASKS_STATE[task_id]["log"] = str(e)

# --- 主题中文翻译 ---
THEME_TRANSLATIONS = {
    "gradient_roads": "渐变公路",
    "contrast_zones": "高对比度",
    "noir": "黑白电影",
    "midnight_blue": "午夜深蓝",
    "blueprint": "建筑蓝图",
    "japanese_ink": "日式水墨",
    "emerald": "翡翠绿",
    "forest": "幽邃森林",
    "ocean": "深海蓝",
    "terracotta": "地中海陶红",
    "sunset": "晚霞日落",
    "autumn": "深秋落叶",
    "copper_patina": "青铜氧化",
    "monochrome_blue": "单色纯蓝",
    "pastel_dream": "马卡龙梦境",
    "warm_beige": "复古米黄",
    "tibetan_sky": "藏地天空",
    "lhasa_crimson": "拉萨暗红",
    "gongga_glacial": "贡嘎冰川",
    "peach_spring": "世外桃源",
    "steppe_sky": "草原长空",
    "datong_coal": "大同煤黑",
    "loess_jin": "晋商黄土",
    "loess_gobi": "西北戈壁",
    "jinshan_gold": "金山璀璨",
    "guandi_red": "关帝赤红",
    "tang_dynasty": "大唐长安",
    "ming_purple": "大明紫金",
    "sichuan_spice": "蜀地麻辣",
    "mountain_city": "雾都山城",
    "shenzhen_tech": "深圳科技",
    "victoria_harbour": "维港之夜",
    "taihu_ink": "太湖水墨",
    "min_river": "闽江之波",
    "xiamen_sea": "厦门海韵",
    "lushan_mist": "庐山云雾",
    "qinhuangdao_coast": "夏日海岸",
    "chengde_forest": "避暑山庄",
    "haihe_night": "海河夜色",
    "tengger_sand": "腾格里沙漠",
    "spring_youth": "青春初春",
    "grassland_blueprint": "草原蓝图",
    "zhao_bronze": "赵国青铜",
    "putuo_zen": "普陀禅意",
    "winter_peaks": "凛冬雪峰",
    "steppe_silver": "草原晨银",
}

@app.get("/")
async def index(request: Request):
    themes = get_available_themes()
    theme_details = []
    for t in themes:
        try:
            theme_data = load_theme(t)
            # 优先使用预设的中文翻译，否则读取 JSON 内的名字，最后回退到文件名
            display_name = THEME_TRANSLATIONS.get(t, theme_data.get("_name", theme_data.get("name", t.capitalize())))
            theme_details.append({
                "id": t,
                "name": display_name,
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

@app.post("/generate")
async def generate_poster(
    request: Request,
    background_tasks: BackgroundTasks,
    city: str = Form(...),
    country: str = Form(...),
    display_city: str = Form(""),
    display_country: str = Form(""),
    copy_language: str = Form("en"),
    theme: str = Form("terracotta"),
    dist: int = Form(4000),
    dpi: int = Form(300),
    size: str = Form("12x16"),
    output_format: str = Form("png"),
    map_x_offset: float = Form(0.0),
    map_y_offset: float = Form(0.0),
    road_width_scale: float = Form(1.0)
):
    # 解析画布尺寸
    try:
        width_str, height_str = size.split('x')
        width = float(width_str)
        height = float(height_str)
    except ValueError:
        width = 12.0
        height = 16.0

    # 地理编码：获取坐标 (增加超时时间到 10 秒)
    # 恢复使用 Nominatim 并指定未被 GFW 封锁的镜像节点 (qgis.org)，确保中英文解析均精准
    geolocator = Nominatim(domain='nominatim.qgis.org', scheme='https', user_agent="maptoposter-web")
    try:
        # 强制请求英文结果，以便在海报上默认渲染极具设计感的英文字母
        location = geolocator.geocode(f"{city}, {country}", timeout=10, language="en", exactly_one=True, addressdetails=True)
    except Exception as e:
        return HTMLResponse(content=f"<div class='text-red-500'>地理编码失败（网络超时）：{str(e)}。请重试。</div>")

    if not location:
        return HTMLResponse(content="<div class='text-red-500'>错误：找不到该城市，请检查名称。</div>")

    point = (location.latitude, location.longitude)

    # 从地理编码结果中提取标准的英文名称 (如果提取不到，则回退到用户输入的名称)
    address = location.raw.get("address", {})
    en_city = address.get("city") or address.get("town") or address.get("county") or address.get("village") or location.raw.get("name") or city
    en_country = address.get("country", country)

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
            logger.warning("Chinese display lookup failed for %s, %s", city, country, exc_info=True)
            zh_city = ""
            zh_country = ""

    final_city, final_country = choose_poster_labels(
        copy_language=copy_language,
        display_city=display_city,
        display_country=display_country,
        english_city=en_city,
        english_country=en_country,
        chinese_city=zh_city,
        chinese_country=zh_country,
    )

    active_fonts = None
    if has_chinese(final_city + final_country):
        active_fonts = load_fonts("poster_zh_cn")

    # 生成文件名
    timestamp = int(asyncio.get_event_loop().time())
    city_slug = city.lower().replace(" ", "_")
    output_filename = f"{city_slug}_{theme}_{timestamp}.{output_format}"
    output_path = os.path.join(POSTERS_DIR, output_filename)

    # 初始化任务状态
    task_id = str(uuid.uuid4())
    with tasks_lock:
        TASKS_STATE[task_id] = {"status": "running", "log": "正在准备生成环境...", "filename": ""}

    # 启动后台任务
    background_tasks.add_task(
        run_poster_task,
        task_id=task_id,
        city=final_city,
        country=final_country,
        point=point,
        dist=dist,
        output_path=output_path,
        map_x_offset=map_x_offset,
        map_y_offset=map_y_offset,
        active_fonts=active_fonts,
        theme=theme,
        road_width_scale=road_width_scale,
        original_city=en_city,
        original_country=en_country,
        width=width,
        height=height,
        dpi=dpi,
        output_format=output_format
    )

    
    # 返回轮询组件
    return HTMLResponse(content=f"""
        <div id="progress-container-{task_id}" hx-get="/status/{task_id}" hx-trigger="every 1s" hx-swap="outerHTML" class="text-center p-6 border rounded-lg bg-gray-50 flex flex-col justify-center h-full">
            <svg class="animate-spin h-10 w-10 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <h3 class="text-lg font-semibold text-gray-800">正在生成，请耐心等待...</h3>
            <p class="text-xs text-gray-500 mt-1">地理数据下载及高清渲染可能需要一至两分钟</p>
            <div class="mt-4 bg-black rounded p-3 text-left overflow-hidden">
                <p class="text-xs font-mono text-green-400 truncate">> 正在准备生成环境...</p>
            </div>
        </div>
    """)

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    with tasks_lock:
        state = TASKS_STATE.get(task_id, {"status": "error", "log": "任务未找到或已过期"})
    
    if state["status"] == "done":
        filename = state["filename"]
        return HTMLResponse(content=f"""
        <div class="text-center animate-fade-in" hx-trigger="load" hx-get="/history" hx-target="#history-list" hx-swap="innerHTML">
            <img src="/posters/{filename}" class="max-w-full rounded shadow-lg mb-4 mx-auto border" style="max-height: 60vh;">
            <div class="flex gap-4 justify-center mt-4">
                <a href="/posters/{filename}" download class="bg-green-600 text-white font-bold px-6 py-2 rounded-lg hover:bg-green-700 shadow transition flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    下载高清海报 (PNG)
                </a>
            </div>
        </div>
        """)
    elif state["status"] == "error":
        return HTMLResponse(content=f"""
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg flex flex-col justify-center h-full">
            <h3 class="text-red-800 font-bold mb-2">生成失败</h3>
            <p class="text-sm text-red-600 font-mono break-all">{state['log']}</p>
            <p class="text-xs text-gray-500 mt-4">提示：如果是网络超时，请尝试减小半径或稍后再试。</p>
        </div>
        """)
    else:
        # Running state
        return HTMLResponse(content=f"""
        <div id="progress-container-{task_id}" hx-get="/status/{task_id}" hx-trigger="every 1s" hx-swap="outerHTML" class="text-center p-6 border rounded-lg bg-gray-50 flex flex-col justify-center h-full">
            <svg class="animate-spin h-10 w-10 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <h3 class="text-lg font-semibold text-gray-800">正在生成，请耐心等待...</h3>
            <p class="text-xs text-gray-500 mt-1">地理数据下载及高清渲染可能需要一至两分钟</p>
            <div class="mt-4 bg-black rounded p-3 text-left overflow-hidden">
                <p class="text-xs font-mono text-green-400 truncate">> {state['log']}</p>
            </div>
        </div>
        """)

@app.get("/history")
async def get_history(request: Request):
    # 临时实现：扫描目录获取最近的海报
    files = sorted(
        [f for f in os.listdir(POSTERS_DIR) if f.endswith(".png")],
        key=lambda x: os.path.getmtime(os.path.join(POSTERS_DIR, x)),
        reverse=True
    )[:12]
    
    if not files:
        return HTMLResponse(content="<p class='text-gray-400 italic'>暂无生成记录</p>")
        
    html = ""
    for f in files:
        html += f"""
        <div class="group relative bg-gray-50 border rounded-lg p-2 flex flex-col items-center">
            <div class="w-full h-64 overflow-hidden rounded mb-2 bg-white flex items-center justify-center">
                <img src="/posters/{f}" class="max-h-full max-w-full object-contain shadow-sm group-hover:scale-105 transition duration-300">
            </div>
            <p class="text-[10px] text-gray-500 truncate w-full text-center mb-2 px-2" title="{f}">{f}</p>
            <div class="w-full">
                <a href="/posters/{f}" download class="block w-full text-center bg-gray-200 hover:bg-blue-600 hover:text-white text-gray-700 text-xs py-2 rounded transition">
                    下载高清原图
                </a>
            </div>
        </div>
        """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
