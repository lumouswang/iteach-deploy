<template>
  <div class="intro-page">
    <div class="bg-decor">
      <div class="strata s1"></div>
      <div class="strata s2"></div>
      <div class="strata s3"></div>
      <div class="strata s4"></div>
      <div class="salt-grain" v-for="i in 18" :key="i" :style="grainStyle(i)"></div>
    </div>

    <div class="hero-banner">
      <div class="hero-inner">
        <div class="brand-row">
          <div class="brand-mark">汤探局</div>
          <span class="brand-subbrand">TANG_DETECTIVE · BUREAU</span>
        </div>
        <h1 class="hero-title">
          <span class="title-line">盐湖</span>
          <span class="title-line accent">岸边</span>
          <span class="title-line">的</span>
          <span class="title-line accent">化石</span>
        </h1>
        <p class="hero-tagline">一块石头 · 三重谜面 · 四层真相</p>
        <p class="hero-subtitle">基于"武将卡分工 + 海龟汤"机制的高中理综跨学科交互课件</p>
      </div>
    </div>

    <div class="relative-layout">
      <div class="card hero" v-if="script?.intro_card">
        <div class="hero-card-header">
          <div class="hero-card-decor">📜</div>
          <div class="hero-card-title">
            <h2>{{ script.intro_card.title }}</h2>
            <p class="hero-card-subtitle">{{ script.intro_card.subtitle }}</p>
          </div>
        </div>
        <div class="badges">
          <el-tag effect="dark" round>{{ script.intro_card.case_type }}</el-tag>
          <el-tag type="warning" effect="dark" round>{{ script.intro_card.case_label }}</el-tag>
          <el-tag type="danger" effect="dark" round>{{ script.intro_card.case_class }}</el-tag>
          <el-tag type="success" effect="dark" round>{{ script.intro_card.knowledge_tag }}</el-tag>
        </div>

        <div v-if="puzzlePrompt" class="puzzle-prompt">
          <div class="puzzle-prompt-icon">🧩</div>
          <div class="puzzle-prompt-body">
            <strong>汤面：</strong>{{ puzzlePrompt }}
          </div>
        </div>

        <div class="tip-box">
          <strong>📘 {{ script.intro_card.tip }}</strong>
        </div>
        <div class="warning-box">
          ⚠ {{ script.intro_card.warning }}
        </div>

        <details class="teacher-toggle" v-if="script.knowledge_points_summary">
          <summary>🎯 查看本节课覆盖的 14 个高考考点</summary>
          <div class="knowledge-summary">
            <p>{{ script.knowledge_points_summary }}</p>
          </div>
        </details>
      </div>

      <div class="card mode-card">
        <h3>🎮 选择探汤模式</h3>
        <div class="mode-options">
          <button class="mode-option solo-only active">
            <div class="mode-icon">🧍</div>
            <div class="mode-label">单人探汤</div>
            <div class="mode-desc">单玩家独立推理</div>
          </button>
        </div>

        <div class="mode-hint">
          💡 单玩家独立推理模式：拿起武将卡，逐步解锁盐湖汤底真相。
        </div>
      </div>

      <div class="actions">
        <el-button type="primary" size="large" @click="startGame" :loading="creating" class="cta-button">
          <span class="cta-icon">🎮</span>
          <span class="cta-text">开始探汤 <span class="cta-sub">— 创建单人房间</span></span>
        </el-button>
      </div>

      <div class="actions-secondary">
        <el-button @click="loadData" plain round>
          <span style="margin-right: 6px;">🔄</span>重新加载数据
        </el-button>
        <span class="version-tag">v 0.3 · beta</span>
      </div>

      <transition name="created-room">
        <div v-if="createdRoom" class="created-room-box">
          <el-alert type="success" :closable="false" show-icon>
            <template #title>
              <span>房间已创建：<code>{{ createdRoom.room_id }}</code> <el-tag size="small" :type="createdRoom.waiting ? 'warning' : 'success'">
                {{ createdRoom.waiting ? '等待第二位玩家…' : '已开始' }}
              </el-tag></span>
            </template>
            <template #default>
              <div>你的玩家 ID：<code>{{ createdRoom.player_id }}</code></div>
              <div v-if="createdRoom.waiting">把房间号发给第二个玩家，让他在首页选择“加入房间”输入这个号</div>
              <div v-else>点击下面按钮继续</div>
            </template>
          </el-alert>
          <el-button type="primary" size="large" round @click="enterCreatedRoom" style="margin-top: 14px;">
            🚀 进入房间 →
          </el-button>
        </div>
      </transition>

      <transition name="created-room">
        <div v-if="createdRoom" class="created-room-box">
          <el-alert type="success" :closable="false" show-icon>
            <template #title>
              <span>房间已创建：<code>{{ createdRoom.room_id }}</code> <el-tag size="small" :type="createdRoom.waiting ? 'warning' : 'success'">
                {{ createdRoom.waiting ? '等待第二位玩家…' : '已开始' }}
              </el-tag></span>
            </template>
            <template #default>
              <div>你的玩家 ID：<code>{{ createdRoom.player_id }}</code></div>
              <div v-if="createdRoom.waiting">把房间号发给第二个玩家，让他在首页选择“加入房间”输入这个号</div>
              <div v-else>点击下面按钮继续</div>
            </template>
          </el-alert>
          <el-button type="primary" size="large" round @click="enterCreatedRoom" style="margin-top: 14px;">
            🚀 进入房间 →
          </el-button>
        </div>
      </transition>

      <div v-if="errorMsg" class="error-msg">
        {{ errorMsg }}<br>
        <small>提示：确保后端 FastAPI 已启动（cd backend; uvicorn main:app --reload）</small>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const script = ref<any>(null)
const creating = ref(false)
const errorMsg = ref('')
const createdRoom = ref<any>(null)

const puzzlePrompt = ref<string>('')
function extractPrompt() {
  // 汤面是 script.subtitle (顶层字段) —— 实际的情景描述
  // script.scene 包含的是老师备课用的"提示句 + 4 层答案"，不应直接展示
  if (!script.value?.subtitle) return
  puzzlePrompt.value = script.value.subtitle.trim()
}
watch(() => script.value?.subtitle, extractPrompt, { immediate: true })

function grainStyle(i: number) {
  // 伪随机点位置 (实际是用固定种子保证样式一致)
  const positions = [
    { top: '12%', left: '8%', size: 6, delay: 0 },
    { top: '28%', left: '12%', size: 4, delay: 1 },
    { top: '42%', left: '6%', size: 5, delay: 2 },
    { top: '60%', left: '14%', size: 7, delay: 0.5 },
    { top: '78%', left: '8%', size: 5, delay: 1.5 },
    { top: '18%', left: '88%', size: 6, delay: 2.5 },
    { top: '34%', left: '92%', size: 5, delay: 0.8 },
    { top: '52%', left: '86%', size: 7, delay: 1.2 },
    { top: '68%', left: '94%', size: 4, delay: 2 },
    { top: '8%', left: '36%', size: 5, delay: 1.8 },
    { top: '20%', left: '52%', size: 6, delay: 0.3 },
    { top: '92%', left: '44%', size: 5, delay: 1.6 },
    { top: '46%', left: '74%', size: 4, delay: 2.2 },
    { top: '5%', left: '18%', size: 5, delay: 0.6 },
    { top: '72%', left: '30%', size: 6, delay: 1.4 },
    { top: '90%', left: '70%', size: 4, delay: 0.9 },
    { top: '38%', left: '40%', size: 5, delay: 1.9 },
    { top: '82%', left: '56%', size: 6, delay: 0.4 }
  ]
  const p = positions[(i - 1) % positions.length]
  return {
    top: p.top,
    left: p.left,
    width: `${p.size}px`,
    height: `${p.size}px`,
    animationDelay: `${p.delay}s`
  }
}

async function loadData() {
  try {
    const res = await axios.get('/api/script')
    script.value = res.data
    errorMsg.value = ''
  } catch (e: any) {
    errorMsg.value = '❌ 加载失败：' + (e?.message || '未知错误')
  }
}

async function startGame() {
  creating.value = true
  try {
    const res = await axios.post('/api/room/create', { user_name: '玩家1' })
    // 存到 sessionStorage 让 PlayView 拿到 player_id
    sessionStorage.setItem(`room:${res.data.room_id}:player_id`, res.data.player_id || '')
    router.push(`/play/${res.data.room_id}`)
  } catch (e: any) {
    errorMsg.value = '❌ 创建房间失败：' + (e?.message || '未知错误')
  } finally {
    creating.value = false
  }
}

// 进入已创建好的房间（“进入房间”按钮复用 startGame 的跳转逻辑）
function enterCreatedRoom() {
  if (!createdRoom.value) return
  const roomId = createdRoom.value.room_id
  const playerId = createdRoom.value.player_id || ''
  sessionStorage.setItem(`room:${roomId}:player_id`, playerId)
  router.push(`/play/${roomId}`)
}

onMounted(loadData)
</script>

<style scoped>
.intro-page {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  background: linear-gradient(180deg, #fdf6ec 0%, #f8e8d0 30%, #f4d7b6 60%, #e9c5a3 100%);
}

/* 背景装饰层 — 盐湖地层 + 盐粒 */
.bg-decor {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
.strata {
  position: absolute;
  left: 0;
  right: 0;
  height: 60px;
  border-radius: 50%;
  filter: blur(2px);
  opacity: 0.4;
}
.strata.s1 { top: 8%; background: rgba(255, 222, 173, 0.6); }
.strata.s2 { top: 18%; background: rgba(244, 215, 182, 0.5); height: 80px; }
.strata.s3 { top: 28%; background: rgba(212, 165, 116, 0.4); height: 70px; }
.strata.s4 { top: 38%; background: rgba(141, 85, 36, 0.3); height: 90px; }
.salt-grain {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.3) 70%, transparent 100%);
  box-shadow: 0 0 4px rgba(255,255,255,0.6);
  animation: twinkle 3s ease-in-out infinite;
}
@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}

/* 封面英雄区 */
.hero-banner {
  position: relative;
  z-index: 1;
  max-width: 960px;
  margin: 0 auto;
  padding: 60px 24px 50px;
  text-align: center;
}
.hero-inner { position: relative; }
.brand-row {
  display: inline-flex;
  align-items: baseline;
  gap: 10px;
  padding: 6px 16px;
  background: rgba(93, 64, 55, 0.85);
  color: #fff;
  border-radius: 100px;
  font-size: 12px;
  letter-spacing: 2px;
  margin-bottom: 26px;
  box-shadow: 0 4px 12px rgba(93, 64, 55, 0.2);
}
.brand-mark {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
}
.brand-subbrand {
  font-family: 'Courier New', monospace;
  font-size: 10px;
  opacity: 0.7;
}

.hero-title {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin: 0 0 18px;
  line-height: 1.1;
}
.title-line {
  font-size: 56px;
  font-weight: 800;
  color: #3e2723;
  letter-spacing: 6px;
  text-shadow: 0 2px 0 rgba(255,255,255,0.4);
  position: relative;
}
.title-line.accent {
  background: linear-gradient(135deg, #bf6b30 0%, #d4a574 50%, #8d5524 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-tagline {
  font-size: 18px;
  color: #5d4037;
  margin: 0 0 10px;
  letter-spacing: 2px;
  font-weight: 500;
}
.hero-subtitle {
  font-size: 13px;
  color: #8d6e63;
  margin: 0;
  letter-spacing: 1px;
}

/* 主体内容布局 */
.relative-layout {
  position: relative;
  z-index: 1;
  max-width: 760px;
  margin: 0 auto;
  padding: 0 20px 60px;
}

.card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 6px 24px rgba(141, 85, 36, 0.12);
  margin-bottom: 22px;
  border: 1px solid rgba(212, 165, 116, 0.2);
}
.hero {
  background: linear-gradient(180deg, #ffffff 0%, #faf6ef 100%);
  border: 2px solid #d4a574;
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(188, 108, 37, 0.15);
}
.hero-card-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding-bottom: 16px;
  margin-bottom: 18px;
  border-bottom: 1px dashed #d4a574;
}
.hero-card-decor {
  font-size: 36px;
  line-height: 1;
  background: linear-gradient(135deg, #fdf6ec 0%, #ffe0b2 100%);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 2px 8px rgba(212, 165, 116, 0.2);
  flex-shrink: 0;
}
.hero-card-title h2 {
  margin: 0 0 4px;
  font-size: 22px;
  color: #3e2723;
  font-weight: 700;
}
.hero-card-subtitle {
  margin: 0;
  font-size: 13px;
  color: #8d6e63;
}
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 18px;
}
.scene-text {
  background: #faf6ef;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #d4a574;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  font-family: inherit;
  margin: 16px 0;
}
.puzzle-prompt {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: linear-gradient(135deg, #fff8e1 0%, #ffe0b2 100%);
  border: 2px solid #d4a574;
  border-radius: 12px;
  padding: 18px 20px;
  margin: 18px 0;
  font-size: 15px;
  line-height: 1.85;
  color: #5d4037;
  box-shadow: 0 4px 12px rgba(212, 165, 116, 0.15);
}
.puzzle-prompt-icon {
  font-size: 32px;
  line-height: 1;
  flex-shrink: 0;
}
.puzzle-prompt-body { flex: 1; }
.puzzle-prompt-body strong {
  display: block;
  margin-bottom: 4px;
  color: #bf6b30;
  font-size: 14px;
  letter-spacing: 2px;
}
.teacher-toggle { margin: 16px 0; }
.teacher-toggle summary {
  cursor: pointer;
  padding: 10px 14px;
  background: #f4f4f5;
  border: 1px dashed #d4a574;
  border-radius: 8px;
  font-size: 13px;
  color: #6b6b6b;
  user-select: none;
  list-style: none;
  transition: all 0.2s;
}
.teacher-toggle summary:hover {
  background: #ecf5ff;
  color: #409eff;
  border-color: #409eff;
}
.teacher-toggle summary::-webkit-details-marker { display: none; }
.teacher-toggle[open] summary {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
  margin-bottom: 8px;
}
.tip-box, .warning-box {
  padding: 14px 16px;
  border-radius: 8px;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.7;
}
.tip-box {
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
  color: #6b4a17;
}
.warning-box {
  background: #fef0f0;
  border-left: 4px solid #f56c6c;
  color: #7a2424;
}
.knowledge-summary {
  margin-top: 12px;
  padding: 14px;
  background: #ecf5ff;
  border-radius: 8px;
}
.knowledge-summary h4 { margin: 0 0 6px; color: #409eff; }
.knowledge-summary p { margin: 0; font-size: 13px; color: #303133; line-height: 1.7; }

/* 模式选择卡片 */
.mode-card { padding: 24px; }
.mode-card h3 {
  margin: 0 0 18px;
  color: #3e2723;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
}
.mode-options {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 16px;
  max-width: 280px;
  margin-left: auto;
  margin-right: auto;
}
.mode-option {
  background: #fff;
  border: 2px solid #ebeef5;
  border-radius: 12px;
  padding: 18px 12px;
  cursor: pointer;
  transition: all 0.25s;
  text-align: center;
  font-family: inherit;
}
.mode-option:hover {
  border-color: #d4a574;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(212, 165, 116, 0.2);
}
.mode-option.active,
.mode-option.solo-only {
  border-color: #bf6b30;
  background: linear-gradient(135deg, #fff8e1 0%, #ffe0b2 100%);
  box-shadow: 0 4px 12px rgba(191, 107, 48, 0.25);
  cursor: default;
}
.mode-icon {
  font-size: 32px;
  margin-bottom: 8px;
  line-height: 1;
}
.mode-label {
  font-size: 15px;
  font-weight: 600;
  color: #3e2723;
  margin-bottom: 4px;
}
.mode-desc {
  font-size: 12px;
  color: #8d6e63;
}
.mode-hint {
  font-size: 13px;
  color: #8d6e63;
  margin-top: 12px;
  padding: 12px 14px;
  background: #faf6ef;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-left: 3px solid #d4a574;
}

/* CTA 按钮 */
.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 14px;
}
.cta-button {
  height: 64px !important;
  font-size: 16px !important;
  padding: 0 32px !important;
  border-radius: 14px !important;
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.25);
  transition: all 0.25s !important;
}
.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.35);
}
.cta-icon {
  font-size: 24px;
  margin-right: 10px;
}
.cta-text { display: flex; flex-direction: column; align-items: flex-start; line-height: 1.2; }
.cta-sub {
  font-size: 11px;
  opacity: 0.85;
  font-weight: 400;
  margin-top: 2px;
  letter-spacing: 0.5px;
}

.actions-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-bottom: 8px;
}
.version-tag {
  font-size: 11px;
  font-family: 'Courier New', monospace;
  color: #8d6e63;
  opacity: 0.7;
  padding: 4px 8px;
  background: rgba(255,255,255,0.5);
  border-radius: 4px;
}

.created-room-box {
  display: none;
}
.created-room-box {
  margin-top: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  border: 2px solid #67c23a;
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.15);
}
.created-room-box code {
  background: rgba(255,255,255,0.7);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #5d4037;
}
.created-room-enter-active,
.created-room-leave-active {
  transition: all 0.4s ease;
}
.created-room-enter-from,
.created-room-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.error-msg {
  margin-top: 20px;
  padding: 14px;
  background: #fef0f0;
  border-radius: 8px;
  color: #f56c6c;
  text-align: center;
  font-size: 13px;
  border-left: 4px solid #f56c6c;
}

/* 响应式 */
@media (max-width: 720px) {
  .hero-title { gap: 8px; }
  .title-line { font-size: 40px; letter-spacing: 4px; }
  .hero-tagline { font-size: 15px; }
  .mode-options { grid-template-columns: 1fr; }
  .actions { flex-direction: column; }
  .cta-button { width: 100%; }
  .cta-text { align-items: center; }
}
</style>
