# 汤探局 · 部署到 Render 操作指引

> 代码已改动并推送到 GitHub（`lumouswang/iteach-deploy`，分支 `main`，commit `6c73bc0`）。
> 你只需要在 Render 网页上点几下，就能拿到一个别人也能打开的公开链接。

---

## 一、为什么换 Render

| 对比项 | Railway（原） | Render（现） |
|---|---|---|
| 免费额度 | 已改为需付费，免费试用额度易耗尽 | 有长期免费档 Web Service |
| WebSocket | 支持 | 原生支持（本项目房间/对战必需） |
| 配置方式 | 需在网页手动配 | 仓库内 `render.yaml` 自动读取 |
| 健康检查 | 手动填 | 蓝图里已写好 `/api/health` |

**无需改任何业务代码**：前端所有请求走相对路径 `/api`，WebSocket 用当前域名拼 `wss://`，
后端 `SERVE_STATIC=1` 时自己托管前端，因此换平台是零侵入的。

---

## 二、操作步骤（约 5 分钟）

### 1. 打开 Render 并登录
访问 https://dashboard.render.com/ ，用 GitHub 账号登录（右上角 **Sign in with GitHub**）。
首次使用需授权 Render 读取你的仓库。

### 2. 新建 Blueprint
- 点击右上角 **New +**
- 选择 **Blueprint**
- 在仓库列表里选中 **`iteach-deploy`**（如果没看到，点 "Configure account" 授权该仓库）
- 点击 **Connect**

### 3. 确认并部署
Render 会自动读取仓库根目录的 `render.yaml`，你应该看到：
- 服务名：`iteach-tangtanju`
- 类型：Web Service / Runtime: Docker
- 区域：Singapore
- 套餐：Free
- 环境变量：`SERVE_STATIC=1`、`PYTHONUNBUFFERED=1`

直接点 **Apply** / **Create Resources**。

### 4. 等待构建
首次构建约 **3–6 分钟**（要装 Node 依赖、构建前端、装 Python 依赖）。
页面上的 Logs 会实时滚动，看到类似
`Serving frontend from /app/backend/static (SPA fallback enabled)` 和
`Uvicorn running on http://0.0.0.0:10000` 就是成功了。

### 5. 拿到公开链接
构建完成后，页面顶部会显示服务地址，形如：

```
https://iteach-tangtanju.onrender.com
```

**把这个链接发给任何人，他们用浏览器直接打开就能玩。** 支持手机浏览器。

---

## 三、使用注意

- **免费档会休眠**：连续 15 分钟无人访问后服务会挂起，下一位访问者需要等
  **30–60 秒**唤醒（页面会转圈，稍等即可）。这是免费档特性，不是故障。
- **数据不持久**：房间数据存在内存里，服务重启或休眠后会清空。课堂现场使用没问题，
  但别指望跨天保留历史记录。
- **多人同时玩**：同一房间链接可多人访问，双人模式需两个浏览器/设备分别用玩家 A、B 加入。

---

## 四、后续如何更新

代码改动后：

```bash
git add -A
git commit -m "你的改动说明"
git push origin main
```

Render 检测到 `main` 分支有新提交会**自动重新部署**（`autoDeploy: true`），
约 3–6 分钟后新版本上线，链接不变。

---

## 五、如果构建失败

在 Render 服务的 **Logs** 标签页查看报错。常见情况：

| 现象 | 原因 | 处理 |
|---|---|---|
| 构建卡在 `npm install` | 网络抖动 | 在 Render 页面点 **Manual Deploy → Clear build cache & deploy** |
| 启动后健康检查超时 | 首次冷启动慢 | 等 1–2 分钟，Render 会重试（最多 10 次） |
| 页面空白但 200 | 前端资源没拷进去 | 检查 Dockerfile 里 `COPY --from=frontend-builder` 那行是否成功 |

---

## 六、备选方案（如果 Render 不理想）

仓库里的 `Dockerfile` 是通用的，同样可以直接部署到：

- **Zeabur**：中文界面，国内访问性更好，导入 GitHub 仓库即可识别 Dockerfile
- **Fly.io**：`fly launch` 自动识别 Dockerfile，需绑卡
- **任意 VPS**：
  ```bash
  docker build -t iteach .
  docker run -d -p 80:8000 -e SERVE_STATIC=1 -e PORT=8000 iteach
  ```

三个平台的共同前提：平台需要注入 `PORT` 环境变量并转发 HTTP/WebSocket 流量，
Dockerfile 的启动命令 `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}` 已适配。
