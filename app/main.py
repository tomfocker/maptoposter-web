from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
import asyncio
from typing import List
from create_map_poster import get_available_themes, create_poster, load_theme
from geopy.geocoders import Nominatim

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
    dpi: int = Form(300)
):
    # 地理编码：获取坐标
    geolocator = Nominatim(user_agent="maptoposter-web")
    location = geolocator.geocode(f"{city}, {country}")
    
    if not location:
        return HTMLResponse(content="<div class='text-red-500'>错误：找不到该城市，请检查名称。</div>")
    
    point = (location.latitude, location.longitude)
    
    # 生成文件名
    timestamp = int(asyncio.get_event_loop().time())
    city_slug = city.lower().replace(" ", "_")
    output_filename = f"{city_slug}_{theme}_{timestamp}.png"
    output_path = os.path.join(POSTERS_DIR, output_filename)
    
    # 调用生成函数 (同步调用，HTMX 负载指示器会处理等待状态)
    # 注意：在生产中建议用 BackgroundTasks 或 Celery，这里为演示简单直接运行
    try:
        # 加载主题 (create_poster 内部会调用，但我们需要确保 themes 存在)
        create_poster(
            city=city,
            country=country,
            point=point,
            dist=dist,
            output_file=output_path,
            output_format="png"
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
