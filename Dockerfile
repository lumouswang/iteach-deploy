# ============ 汤探局 / ITeach - 通用 Dockerfile（Railway / Render / 任何 Docker 平台） ============
# 多阶段构建：
#   1) frontend-builder：Node 装依赖并打包 Vue
#   2) backend-runtime：Python 拷 dist 到 /app/backend/static，起 uvicorn

# ---------- 阶段 1：构建前端 ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# 先只拷 manifest，最大化层缓存
COPY frontend/package.json frontend/package-lock.json* ./frontend/
WORKDIR /build/frontend
RUN npm install --no-audit --no-fund

# 再拷源码并构建
COPY frontend/ ./
RUN npm run build

# ---------- 阶段 2：Python 后端 + 静态前端 ----------
FROM python:3.11-slim AS backend-runtime
WORKDIR /app

# 系统依赖（uvicorn[standard] 需要）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 后端代码
COPY backend/ ./backend/

# 数据文件（4 个 JSON 都在仓库 data/ 下，相对 backend/main.py 的 ../data）
COPY data/ ./data/

# 把前端构建产物放到 backend/static（与 main.py 里的 _CANDIDATE_STATIC_DIRS 第一项匹配）
COPY --from=frontend-builder /build/frontend/dist ./backend/static/

# PORT 会被部署平台注入（Railway / Render / Fly.io 都注入 PORT），兑底默认 8000
ENV PORT=8000 \
    SERVE_STATIC=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# 工作目录
WORKDIR /app/backend

# 启动命令：使用平台注入的 PORT 环境变量（默认 8000）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]