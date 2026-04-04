from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
import asyncio
from typing import List
from create_map_poster import get_available_themes, create_poster, load_theme
import create_map_poster
from geopy.geocoders import Nominatim
import osmnx as ox

# 配置 OSMnx：开启控制台日志并使用默认设置
ox.settings.log_console = True
ox.settings.use_cache = True
# 移除 hardcoded overpass_url，以便在云端使用默认节点

app = FastAPI(title="MapToPoster Web")

# 确保必要的目录存在
POSTERS_DIR = "posters"
os.makedirs(POSTERS_DIR, exist_ok=True)

# 挂载静态文件和海报目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/posters", StaticFiles(directory="posters"), name="posters")

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def index(request: Request):
    themes = get_available_themes()
    return templates.TemplateResponse("index.html", {"request": request, "themes": themes})

@app.post("/generate")
async def generate_poster(
    request: Request,
    city: str = Form(...),
    country: str = Form(...),
    theme: str = Form("terracotta"),
    dist: int = Form(4000),
    dpi: int = Form(300),
    map_x_offset: float = Form(0.0),
    map_y_offset: float = Form(0.0),
    road_width_scale: float = Form(1.0)
):
    # 地理编码：获取坐标 (增加超时时间到 10 秒)
    geolocator = Nominatim(user_agent="maptoposter-web")
    try:
        location = geolocator.geocode(f"{city}, {country}", timeout=10)
    except Exception as e:
        return HTMLResponse(content=f"<div class='text-red-500'>地理编码失败（网络超时）：{str(e)}。请重试。</div>")
    
    if not location:
        return HTMLResponse(content="<div class='text-red-500'>错误：找不到该城市，请检查名称。</div>")
    
    point = (location.latitude, location.longitude)
    
    # 生成文件名
    timestamp = int(asyncio.get_event_loop().time())
    city_slug = city.lower().replace(" ", "_")
    output_filename = f"{city_slug}_{theme}_{timestamp}.png"
    output_path = os.path.join(POSTERS_DIR, output_filename)
    
    # 调用生成函数 (同步调用，HTMX 负载指示器会处理等待状态)
    try:
        # 1. 加载并设置全局主题
        create_map_poster.THEME = load_theme(theme)
        
        # 2. 如果提供了自定义道路缩放，则与主题自带的缩放叠加
        current_scale = create_map_poster.THEME.get("road_width_scale", 1.0)
        create_map_poster.THEME["road_width_scale"] = current_scale * road_width_scale
        
        # 3. 生成海报
        create_poster(
            city=city,
            country=country,
            point=point,
            dist=dist,
            output_file=output_path,
            output_format="png",
            map_x_offset=map_x_offset,
            map_y_offset=map_y_offset
        )
        
        # 返回预览 HTML 片段，并触发历史更新事件
        response_html = f"""
        <div class="text-center animate-fade-in" hx-trigger="load" hx-get="/history" hx-target="#history-list" hx-swap="innerHTML">
            <img src="/posters/{output_filename}" class="max-w-full rounded shadow-lg mb-4">
            <div class="flex gap-4 justify-center">
                <a href="/posters/{output_filename}" download class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">下载 PNG</a>
            </div>
        </div>
        """
        return HTMLResponse(content=response_html, headers={"HX-Trigger": "posterGenerated"})
        
    except Exception as e:
        return HTMLResponse(content=f"<div class='text-red-500'>生成失败：{str(e)}</div>")

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
        <div class="group relative">
            <img src="/posters/{f}" class="w-full h-32 object-cover rounded shadow-sm group-hover:opacity-75 transition">
            <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                <a href="/posters/{f}" download class="bg-white/90 p-1 rounded-full shadow text-blue-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                </a>
            </div>
        </div>
        """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
