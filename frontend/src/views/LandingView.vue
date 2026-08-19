<template>
  <div class="landing-container">
    <!-- 动态背景 -->
    <div class="bg-stars"></div>
    <div class="bg-fog"></div>

    <!-- 顶部标题区 -->
    <header class="landing-header">
      <div class="logo-section">
        <div class="logo-emblem">
          <svg viewBox="0 0 80 80" class="emblem-svg">
            <circle cx="40" cy="40" r="38" fill="none" stroke="currentColor" stroke-width="0.5" />
            <circle
              cx="40"
              cy="40"
              r="32"
              fill="none"
              stroke="currentColor"
              stroke-width="0.3"
              stroke-dasharray="2,2"
            />
            <path
              d="M40 8 L42 40 L40 72 L38 40 Z"
              fill="currentColor"
              class="compass-needle"
            />
            <circle cx="40" cy="40" r="2" fill="currentColor" />
          </svg>
        </div>
        <div class="title-stack">
          <h1 class="main-title">汤探局</h1>
          <p class="subtitle-en">SaltLake Detective Bureau</p>
        </div>
      </div>
      <div class="version-tag">v1.0 · 2026 IT COMPETITION</div>
    </header>

    <!-- 主内容区 -->
    <main class="landing-main">
      <!-- 动态打字机副标题 -->
      <div class="hero-tagline">
        <span class="bracket-left">「</span>
        <span class="tagline-text">{{ displayText }}</span>
        <span class="cursor" :class="{ blink: !typingDone }">|</span>
        <span class="bracket-right">」</span>
      </div>

      <!-- 双角色卡片 -->
      <div class="role-grid">
        <!-- 教师端 -->
        <article
          class="role-card teacher-card"
          :class="{ 'is-hovered': hoveredRole === 'teacher' }"
          @mouseenter="hoveredRole = 'teacher'"
          @mouseleave="hoveredRole = null"
          @click="enterAs('teacher')"
        >
          <div class="card-inner">
            <div class="card-icon">
              <svg viewBox="0 0 64 64">
                <path d="M8 24 L32 14 L56 24 L32 34 Z" fill="currentColor" />
                <path
                  d="M16 30 L16 42 Q32 50 48 42 L48 30"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <circle cx="32" cy="56" r="3" fill="currentColor" />
              </svg>
            </div>
            <h2 class="card-title">教师端</h2>
            <p class="card-subtitle">Teacher Dashboard</p>
            <ul class="feature-list">
              <li><span class="dot"></span>班级进度总览</li>
              <li><span class="dot"></span>学情画像分析</li>
              <li><span class="dot"></span>答题热力图</li>
              <li><span class="dot"></span>课堂实时控制</li>
            </ul>
            <button class="enter-btn teacher-btn">
              <span class="btn-text">进入教师端</span>
              <span class="btn-arrow">→</span>
            </button>
          </div>
          <!-- 装饰边角 -->
          <div class="card-corner corner-tl"></div>
          <div class="card-corner corner-tr"></div>
          <div class="card-corner corner-bl"></div>
          <div class="card-corner corner-br"></div>
        </article>

        <!-- 学生端 -->
        <article
          class="role-card student-card"
          :class="{ 'is-hovered': hoveredRole === 'student' }"
          @mouseenter="hoveredRole = 'student'"
          @mouseleave="hoveredRole = null"
          @click="enterAs('student')"
        >
          <div class="card-inner">
            <div class="card-icon">
              <svg viewBox="0 0 64 64">
                <circle
                  cx="24"
                  cy="24"
                  r="14"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="3"
                />
                <line
                  x1="34"
                  y1="34"
                  x2="50"
                  y2="50"
                  stroke="currentColor"
                  stroke-width="4"
                  stroke-linecap="round"
                />
                <rect x="10" y="10" width="20" height="3" fill="currentColor" />
                <rect
                  x="10"
                  y="16"
                  width="14"
                  height="2"
                  fill="currentColor"
                  opacity="0.6"
                />
              </svg>
            </div>
            <h2 class="card-title">学生端</h2>
            <p class="card-subtitle">Student Detective</p>
            <ul class="feature-list">
              <li><span class="dot"></span>角色扮演探案</li>
              <li><span class="dot"></span>武将卡牌解锁</li>
              <li><span class="dot"></span>14 考点闯关</li>
              <li><span class="dot"></span>复盘学习反馈</li>
            </ul>
            <button class="enter-btn student-btn">
              <span class="btn-text">进入学生端</span>
              <span class="btn-arrow">→</span>
            </button>
          </div>
          <!-- 装饰边角 -->
          <div class="card-corner corner-tl"></div>
          <div class="card-corner corner-tr"></div>
          <div class="card-corner corner-bl"></div>
          <div class="card-corner corner-br"></div>
        </article>
      </div>
    </main>

    <!-- 底部 -->
    <footer class="landing-footer">
      <div class="footer-divider"></div>
      <p class="footer-text">
        © 2026 汤探局团队 · 大学生 IT 竞赛参赛作品 · 用探索重构学习
      </p>
    </footer>

    <!-- 鼠标涟漪容器 -->
    <div ref="rippleContainer" class="ripple-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const hoveredRole = ref<null | 'teacher' | 'student'>(null)

// 打字机效果
const fullText = '成为探员，破解盐湖之谜'
const displayText = ref('')
const typingDone = ref(false)

function typeEffect() {
  let i = 0
  const timer = setInterval(() => {
    if (i <= fullText.length) {
      displayText.value = fullText.slice(0, i)
      i++
    } else {
      clearInterval(timer)
      typingDone.value = true
    }
  }, 120)
}

function enterAs(role: 'teacher' | 'student') {
  // 记录身份
  sessionStorage.setItem('user_role', role)

  // 路由跳转
  if (role === 'teacher') {
    router.push('/teacher')
  } else {
    router.push('/intro') // 学生端先去介绍页
  }
}

// 点击涟漪效果
const rippleContainer = ref<HTMLElement | null>(null)

function handleRipple(e: MouseEvent) {
  if (!rippleContainer.value) return
  const ripple = document.createElement('span')
  ripple.className = 'ripple'
  ripple.style.left = `${e.clientX}px`
  ripple.style.top = `${e.clientY}px`
  rippleContainer.value.appendChild(ripple)
  setTimeout(() => ripple.remove(), 1000)
}

onMounted(() => {
  typeEffect()
  document.addEventListener('click', handleRipple)
})
</script>

<style scoped>
.landing-container {
  --bg-deep: #0f1b2d;
  --bg-mid: #1a2b45;
  --bg-soft: #243958;
  --teacher-gold: #d4a574;
  --teacher-gold-bright: #e8c290;
  --student-teal: #5ba88a;
  --student-teal-bright: #7cc9a8;
  --text-primary: #f5f1e8;
  --text-secondary: #a8b5c4;
  --accent-red: #c73e3a;

  min-height: 100vh;
  background: radial-gradient(ellipse at top, var(--bg-mid) 0%, var(--bg-deep) 70%);
  color: var(--text-primary);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ====== 背景动效 ====== */
.bg-stars {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 20% 30%, rgba(212, 165, 116, 0.5), transparent),
    radial-gradient(1px 1px at 60% 70%, rgba(91, 168, 138, 0.4), transparent),
    radial-gradient(2px 2px at 80% 20%, rgba(245, 241, 232, 0.3), transparent),
    radial-gradient(1px 1px at 30% 80%, rgba(212, 165, 116, 0.4), transparent),
    radial-gradient(1px 1px at 90% 60%, rgba(91, 168, 138, 0.3), transparent);
  background-size: 200px 200px;
  animation: drift 60s linear infinite;
  pointer-events: none;
  opacity: 0.7;
}

@keyframes drift {
  from {
    background-position: 0 0;
  }
  to {
    background-position: 200px 200px;
  }
}

.bg-fog {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 30% 40%, rgba(91, 168, 138, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 70% 60%, rgba(212, 165, 116, 0.05) 0%, transparent 50%);
  filter: blur(40px);
  pointer-events: none;
}

/* ====== 顶部 ====== */
.landing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px 64px;
  position: relative;
  z-index: 2;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-emblem {
  width: 56px;
  height: 56px;
  color: var(--teacher-gold);
  animation: gentle-rotate 30s linear infinite;
}

.compass-needle {
  transform-origin: 40px 40px;
}

@keyframes gentle-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.title-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.main-title {
  font-size: 28px;
  font-weight: 500;
  letter-spacing: 8px;
  margin: 0;
  font-family: 'Source Han Serif', 'Noto Serif SC', serif;
}

.subtitle-en {
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 3px;
  margin: 0;
  text-transform: uppercase;
  font-family: 'Cormorant Garamond', serif;
}

.version-tag {
  font-size: 11px;
  color: var(--text-secondary);
  letter-spacing: 2px;
  border: 1px solid rgba(168, 181, 196, 0.3);
  padding: 6px 14px;
  border-radius: 20px;
}

/* ====== 主内容 ====== */
.landing-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0 64px;
  position: relative;
  z-index: 2;
}

.hero-tagline {
  font-size: 36px;
  margin-bottom: 80px;
  letter-spacing: 4px;
  font-family: 'Source Han Serif', 'Noto Serif SC', serif;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bracket-left,
.bracket-right {
  color: var(--accent-red);
  font-size: 48px;
  opacity: 0.8;
}

.tagline-text {
  min-height: 1.2em;
}

.cursor {
  font-weight: 100;
  color: var(--teacher-gold);
  margin-left: 4px;
  font-size: 32px;
}

.cursor.blink {
  animation: blink 1s steps(2) infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

/* ====== 双卡片 ====== */
.role-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  max-width: 980px;
  width: 100%;
}

.role-card {
  position: relative;
  background: rgba(36, 57, 88, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(168, 181, 196, 0.15);
  border-radius: 4px;
  padding: 48px 40px;
  cursor: pointer;
  transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
  overflow: hidden;
}

.role-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    transparent 0%,
    rgba(255, 255, 255, 0.03) 50%,
    transparent 100%
  );
  pointer-events: none;
  transition: opacity 0.5s;
  opacity: 0;
}

.role-card:hover::before {
  opacity: 1;
}

.teacher-card {
  --role-color: var(--teacher-gold);
}

.student-card {
  --role-color: var(--student-teal);
}

.role-card:hover {
  transform: translateY(-8px) scale(1.02);
  border-color: var(--role-color);
  box-shadow:
    0 24px 48px rgba(0, 0, 0, 0.3),
    0 0 32px rgba(212, 165, 116, 0.15);
}

.student-card:hover {
  box-shadow:
    0 24px 48px rgba(0, 0, 0, 0.3),
    0 0 32px rgba(91, 168, 138, 0.15);
}

.card-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid var(--role-color);
  opacity: 0;
  transition: opacity 0.4s;
}

.role-card:hover .card-corner {
  opacity: 1;
}

.corner-tl {
  top: 12px;
  left: 12px;
  border-right: 0;
  border-bottom: 0;
}
.corner-tr {
  top: 12px;
  right: 12px;
  border-left: 0;
  border-bottom: 0;
}
.corner-bl {
  bottom: 12px;
  left: 12px;
  border-right: 0;
  border-top: 0;
}
.corner-br {
  bottom: 12px;
  right: 12px;
  border-left: 0;
  border-top: 0;
}

.card-inner {
  position: relative;
  z-index: 2;
  text-align: center;
}

.card-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: var(--role-color);
  transition: transform 0.4s;
}

.role-card:hover .card-icon {
  transform: scale(1.1) rotate(-5deg);
}

.card-title {
  font-size: 32px;
  font-weight: 500;
  letter-spacing: 6px;
  margin: 0 0 8px;
  font-family: 'Source Han Serif', 'Noto Serif SC', serif;
}

.card-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 3px;
  text-transform: uppercase;
  margin: 0 0 32px;
  font-family: 'Cormorant Garamond', serif;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 40px;
  text-align: left;
}

.feature-list li {
  padding: 10px 0;
  font-size: 14px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(168, 181, 196, 0.08);
  letter-spacing: 1px;
}

.feature-list li:last-child {
  border-bottom: 0;
}

.dot {
  width: 4px;
  height: 4px;
  background: var(--role-color);
  border-radius: 50%;
  flex-shrink: 0;
}

.enter-btn {
  width: 100%;
  padding: 14px 24px;
  background: transparent;
  border: 1px solid var(--role-color);
  color: var(--role-color);
  font-size: 14px;
  letter-spacing: 4px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  transition: all 0.4s;
}

.enter-btn:hover {
  background: var(--role-color);
  color: var(--bg-deep);
  letter-spacing: 6px;
}

.btn-arrow {
  transition: transform 0.3s;
}

.enter-btn:hover .btn-arrow {
  transform: translateX(4px);
}

/* ====== 底部 ====== */
.landing-footer {
  padding: 32px 64px;
  text-align: center;
  position: relative;
  z-index: 2;
}

.footer-divider {
  width: 80px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--text-secondary), transparent);
  margin: 0 auto 16px;
}

.footer-text {
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 2px;
  margin: 0;
}

/* ====== 涟漪 ====== */
.ripple-container {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 100;
}

.ripple {
  position: absolute;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(212, 165, 116, 0.4) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  animation: ripple-expand 1s ease-out forwards;
}

@keyframes ripple-expand {
  from {
    width: 0;
    height: 0;
    opacity: 1;
  }
  to {
    width: 200px;
    height: 200px;
    opacity: 0;
  }
}

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .landing-header,
  .landing-main,
  .landing-footer {
    padding-left: 24px;
    padding-right: 24px;
  }

  .role-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .hero-tagline {
    font-size: 24px;
    margin-bottom: 48px;
  }

  .main-title {
    font-size: 22px;
    letter-spacing: 4px;
  }
}
</style>