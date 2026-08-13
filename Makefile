PYTHON ?= python
NPM    ?= npm

.PHONY: help dev dev-be dev-fe build test test-be lint clean

help: ## Show this help
	@echo "汤探局 - 常用命令"
	@echo "  make dev      启动后端 + 前端（两个 shell，需同时运行）"
	@echo "  make dev-be   启动后端 (FastAPI)"
	@echo "  make dev-fe   启动前端 (Vite)"
	@echo "  make test-be  跑后端 pytest"
	@echo "  make build    打包前端"
	@echo "  make clean    清理 __pycache__ + node_modules"

dev-be: ## 后端 FastAPI dev server
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-fe: ## 前端 Vite dev server
	cd frontend && $(NPM) run dev

dev: dev-be dev-fe ## 同时启前后端（各占一个 shell）

test-be: ## 跑后端 pytest
	cd backend && $(PYTHON) -m pytest -q

build: ## 打包前端
	cd frontend && $(NPM) run build

clean:
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
