# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

# 安装系统编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libgdal-dev \
    libproj-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# 安装运行时必需的最小依赖 (GDAL 等)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 \
    libproj25 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的库
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码和资源
COPY . .

# 暴露端口
EXPOSE 8000

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV CACHE_DIR=/app/cache

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
