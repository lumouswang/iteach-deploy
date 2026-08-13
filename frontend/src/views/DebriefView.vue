<template>
  <div class="debrief-page">
    <!-- 🎉 撒花粒子层 -->
    <div class="fireworks-layer" aria-hidden="true">
      <svg
        v-for="p in particles"
        :key="p.id"
        class="particle"
        :style="{
          left: p.x + 'px',
          top: p.y + 'px',
          width: p.size + 'px',
          height: p.size + 'px',
          color: p.color,
          opacity: p.life,
          transform: `rotate(${p.rotation}deg)`,
        }"
        viewBox="0 0 20 20"
      >
        <path :d="shapePath(p.shape)" fill="currentColor" />
      </svg>
    </div>

    <!-- ========== 顶部英雄区 ========== -->
    <header class="db-hero" :class="{ 'is-clear': allCleared }">
      <div class="hero-decor" aria-hidden="true">
        <span class="deco-ring r1"></span>
        <span class="deco-ring r2"></span>
        <span class="deco-ring r3"></span>
      </div>
      <div class="hero-inner">
        <div class="hero-emoji">📊</div>
        <h1 class="hero-title">全局复盘</h1>
        <p class="hero-sub">用数据告诉你：本局你的思维路径 + 学习收获</p>

        <div class="hero-strip" v-if="!loading && !loadError">
          <div class="hs-item">
            <span class="hs-num" :class="{ gold: allCleared }">{{ unlockedLayers.length }}</span>
            <span class="hs-sep">/4</span>
            <span class="hs-label">层级通关</span>
          </div>
          <span class="hs-divider"></span>
          <div class="hs-item">
            <span class="hs-num" :class="{ warn: negationBoard.length > 0 }">{{ negationBoard.length }}</span>
            <span class="hs-label">错题</span>
          </div>
          <span class="hs-divider"></span>
          <div class="hs-item">
            <span class="hs-num">{{ cluesLog.length }}</span>
            <span class="hs-label">线索</span>
          </div>
          <span class="hs-divider"></span>
          <div class="hs-item">
            <span class="hs-num">{{ totalQuestionsAsked }}</span>
            <span class="hs-sep">/5</span>
            <span class="hs-label">提问</span>
          </div>
        </div>

        <div v-if="allCleared" class="hero-badge">
          🏆 全层通关 · {{ clearanceMessage }}
        </div>
      </div>
    </header>

    <!-- ========== 快捷导航（粘性） ========== -->
    <nav class="quick-nav" v-if="!loading && !loadError">
      <span class="nav-label">🧭 快速跳转</span>
      <a class="nav-pill pill-danger" :class="{ disabled: negationBoard.length === 0 }" @click="scrollTo('section-wrongs')">
        ❌ 错题本 <em>{{ negationBoard.length }}</em>
      </a>
      <a class="nav-pill pill-success" @click="scrollTo('section-clues')">
        💡 线索图谱 <em>{{ cluesLog.length }}</em>
      </a>
      <a class="nav-pill pill-info" @click="scrollTo('section-layers')">
        🌈 解锁的汤层 <em>{{ unlockedLayers.length }}</em>
      </a>
      <a class="nav-pill pill-warn" @click="scrollTo('section-generals')">
        🎴 武将图鉴
      </a>
      <a class="nav-pill pill-primary" @click="scrollTo('section-stats')">
        📈 战绩详情
      </a>
    </nav>

    <div v-if="loading" class="loading-box">
      <el-alert title="加载中..." type="info" :closable="false" show-icon>
        正在拉取复盘数据...
      </el-alert>
    </div>

    <div v-else-if="loadError" class="loading-box">
      <el-alert :title="loadError" type="error" :closable="false" show-icon>
        <template #default>
          <el-button @click="load" type="primary" size="small" style="margin-top:8px">🔄 重试</el-button>
          <el-button @click="$router.push('/')" size="small" style="margin-top:8px">返回首页</el-button>
        </template>
      </el-alert>
    </div>

    <div v-else class="db-body">
      <!-- ============================================== -->
      <!-- ① 战绩卡片：4 个 stat 顶部一条 -->
      <!-- ============================================== -->
      <section id="section-stats" class="card stats-card">
        <div class="card-head">
          <span class="card-num">④</span>
          <h3>战绩统计</h3>
          <span class="card-sub">本局数据一览 · {{ clearanceMessage }}</span>
        </div>
        <div class="stat-row">
          <div class="stat stat-ask">
            <div class="stat-icon">❓</div>
            <div class="stat-meta">
              <div class="stat-num">
                <span>{{ totalQuestionsAsked }}</span><small>/5</small>
              </div>
              <div class="stat-label">提问使用</div>
              <div class="stat-bar">
                <div class="stat-bar-fill" :style="{ width: questionPct + '%' }"></div>
              </div>
              <div class="stat-hint">剩余 {{ Math.max(0, 5 - totalQuestionsAsked) }} 次</div>
            </div>
          </div>
          <div class="stat stat-wrong" :class="{ active: negationBoard.length > 0 }">
            <div class="stat-icon">❌</div>
            <div class="stat-meta">
              <div class="stat-num">
                <span>{{ negationBoard.length }}</span>
              </div>
              <div class="stat-label">错题</div>
              <div class="stat-bar">
                <div class="stat-bar-fill" :style="{ width: Math.min(100, negationBoard.length * 20) + '%' }"></div>
              </div>
              <div class="stat-hint">{{ negationBoard.length === 0 ? '零失误' : `正确率 ${accuracyPct}%` }}</div>
            </div>
          </div>
          <div class="stat stat-clue">
            <div class="stat-icon">💡</div>
            <div class="stat-meta">
              <div class="stat-num">
                <span>{{ cluesLog.length }}</span>
              </div>
              <div class="stat-label">线索收集</div>
              <div class="stat-bar">
                <div class="stat-bar-fill" :style="{ width: Math.min(100, cluesLog.length * 9) + '%' }"></div>
              </div>
              <div class="stat-hint">{{ comboClueCount }} 条合技深推</div>
            </div>
          </div>
          <div class="stat stat-layer" :class="{ complete: allCleared }">
            <div class="stat-icon">🌈</div>
            <div class="stat-meta">
              <div class="stat-num">
                <span>{{ unlockedLayers.length }}</span><small>/4</small>
              </div>
              <div class="stat-label">层级通关</div>
              <div class="stat-bar">
                <div class="stat-bar-fill" :style="{ width: unlockedLayers.length * 25 + '%' }"></div>
              </div>
              <div class="stat-hint">{{ allCleared ? '完美通关 🎉' : `还差 ${4 - unlockedLayers.length} 层` }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ============================================== -->
      <!-- ② 否决板 / 错题本 -->
      <!-- ============================================== -->
      <section id="section-wrongs" class="card wrongs-card">
        <div class="card-head">
          <span class="card-num">①</span>
          <h3>否决板 <span class="card-sub-en">/ 错题本</span></h3>
          <span class="card-count">{{ negationBoard.length }} 条</span>
        </div>
        <div v-if="negationBoard.length === 0" class="empty empty-success">
          <div class="empty-icon">🎯</div>
          <div class="empty-text">这局没有错误猜想</div>
          <div class="empty-sub">继续保持 —— 你对「石头」成因的直觉非常稳</div>
        </div>
        <div v-else class="negation-list">
          <div v-for="(n, i) in negationBoard" :key="n.id" class="negation-item">
            <div class="ni-num">#{{ i + 1 }}</div>
            <div class="ni-body">
              <div class="ni-text">⨯ {{ n.text }}</div>
              <div class="ni-meta">
                <span class="ni-tag ni-tag-wrong">错</span>
                <span class="ni-answer" v-if="n.answer">
                  正确答案：<strong :class="n.answer === '是' ? 'answer-yes' : 'answer-no'">{{ n.answer }}</strong>
                </span>
                <span class="ni-kp" v-if="n.knowledge_point">📚 {{ n.knowledge_point }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ============================================== -->
      <!-- ③ 解锁层进度 -->
      <!-- ============================================== -->
      <section id="section-layers" class="card layers-card">
        <div class="card-head">
          <span class="card-num">②</span>
          <h3>解锁的汤层</h3>
          <span class="card-count">{{ unlockedLayers.length }} / 4 层</span>
        </div>
        <div class="layer-track">
          <div
            v-for="(layer, idx) in layerProgress"
            :key="layer.key"
            class="layer-slot"
            :class="[`layer-${layer.key}`, { unlocked: layer.unlocked }]"
          >
            <div class="ls-num">{{ idx + 1 }}</div>
            <div class="ls-icon">{{ layer.icon }}</div>
            <div class="ls-name">{{ layer.name }}</div>
            <div class="ls-hint">{{ layer.hint }}</div>
            <div class="ls-combo" v-if="layer.unlocked">{{ layer.combo }}</div>
            <div class="ls-combo ls-combo-locked" v-else>🔒 待解锁</div>
          </div>
        </div>
      </section>

      <!-- ============================================== -->
      <!-- ④ 线索图谱 -->
      <!-- ============================================== -->
      <section id="section-clues" class="card clues-card">
        <div class="card-head">
          <span class="card-num">③</span>
          <h3>线索图谱</h3>
          <span class="card-count">{{ cluesLog.length }} 条线索</span>
          <span v-if="comboClueCount > 0" class="card-pill card-pill-combo">
            ⚡ {{ comboClueCount }} 条合技深推
          </span>
        </div>

        <div v-if="cluesLog.length === 0" class="empty empty-info">
          <div class="empty-icon">📭</div>
          <div class="empty-text">尚未收集线索</div>
        </div>

        <div v-else class="clue-timeline">
          <div
            v-for="(c, idx) in cluesLog"
            :key="c.clue_id"
            class="clue-node"
            :class="[
              `layer-${c.layer || 'none'}`,
              { 'is-combo': c.clue_id?.startsWith('combo_') }
            ]"
          >
            <div class="cn-rail">
              <div class="cn-dot"></div>
              <div class="cn-line" v-if="idx < cluesLog.length - 1"></div>
            </div>
            <div class="cn-card">
              <div class="cn-head">
                <strong class="cn-title">{{ labelOf(c.clue_id) }}</strong>
                <span v-if="c.clue_id?.startsWith('combo_')" class="cn-tag cn-tag-combo">⚡ 合技解锁</span>
                <span v-if="c.layer" class="cn-tag" :class="`cn-tag-layer layer-tag-${c.layer}`">
                  {{ layerIcon(c.layer) }} {{ layerName(c.layer) }}
                </span>
                <span class="cn-card-tag">{{ cardName(c.card_id) }}</span>
              </div>
              <p v-if="c.content" class="cn-body">{{ c.content }}</p>
              <div class="cn-kp" v-if="c.knowledge_point">📚 {{ c.knowledge_point }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ============================================== -->
      <!-- ⑤ 武将图鉴 -->
      <!-- ============================================== -->
      <section id="section-generals" class="card generals-card">
        <div class="card-head">
          <span class="card-num">⑤</span>
          <h3>武将图鉴 <span class="card-sub-en">· 学情画像</span></h3>
          <span class="card-count">{{ litCardsCount }} / {{ cards.length }} 已点亮</span>
        </div>
        <div class="generals-grid">
          <div class="radar-block">
            <div class="radar-block-head">
              <span class="radar-icon">🛰️</span>
              <span class="radar-title">7 维能力雷达</span>
              <span class="radar-sub">反映本局点的 7 位武将「取景器」使用画像</span>
            </div>
            <AbilityRadar :cards="radarCards" />
          </div>

          <div
            v-for="card in cards"
            :key="card.id"
            class="general-mini"
            :class="{ lit: (cardUsage[card.id] || 0) > 0 }"
          >
            <div class="gm-icon">{{ card.badge_icon }}</div>
            <div class="gm-name">{{ card.name }}</div>
            <div class="gm-tags">
              <span v-for="t in card.exam_tags" :key="t" class="gm-tag">{{ t }}</span>
            </div>
            <div class="gm-usage">
              <span v-if="(cardUsage[card.id] || 0) === 0">未使用</span>
              <span v-else>已用 {{ cardUsage[card.id] }} 次</span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- ========== 底部操作 ========== -->
    <div class="footer-actions">
      <el-button @click="$router.push('/')" size="large" round>🏠 返回首页</el-button>
      <el-button @click="$router.push(`/play/${roomId}`)" size="large" round>
        ↩️ 回到汤面
      </el-button>
      <el-button
        v-if="allCleared"
        type="warning"
        size="large"
        round
        @click="$router.push(`/challenge/${roomId}`)"
      >
        🎓 去通关挑战
      </el-button>
      <el-button type="primary" size="large" round @click="exportPDF">📥 导出报告</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import AbilityRadar from '../components/AbilityRadar.vue'

import { useFireworks } from '../composables/useFireworks'
const { particles, shapePath, burst } = useFireworks()

const route = useRoute()
const roomId = computed(() => route.params.roomId as string)

const cards = ref<any[]>([])
const negationBoard = ref<any[]>([])
const cluesLog = ref<any[]>([])
const questionsLog = ref<any[]>([])
const cardUsage = ref<Record<string, number>>({})
const unlockedLayers = ref<string[]>([])
const loading = ref(true)
const loadError = ref('')

const totalQuestionsAsked = computed(() => questionsLog.value.length)
const allCleared = computed(() => unlockedLayers.value.length >= 4)
const comboClueCount = computed(() =>
  cluesLog.value.filter(c => c.clue_id?.startsWith('combo_')).length,
)

// 派生：提问占用百分比（0-100）
const questionPct = computed(() => Math.min(100, (totalQuestionsAsked.value / 5) * 100))

// 派生：准确率（答对 / 已提问）
const accuracyPct = computed(() => {
  const asked = totalQuestionsAsked.value
  if (asked === 0) return 100
  const wrong = negationBoard.value.length
  return Math.round(((asked - wrong) / asked) * 100)
})

// 已点亮的武将数
const litCardsCount = computed(() =>
  cards.value.filter(c => (cardUsage.value[c.id] || 0) > 0).length,
)

// 🛰 7 维能力雷达数据：颜色 / 图标 / 使用次数
const SUBJECT_COLORS: Record<string, string> = {
  '地理':           '#2d5a4f',
  '地理 + 历史':    '#6b4423',
  '数学 + 化学':    '#1e3a2c',
  '生物':           '#4a7c59',
  '物理':           '#1a2e5a',
  '数学':           '#5b2c5f',
  '综合':           '#8b5a1c',
}
const radarCards = computed(() =>
  cards.value.map(c => ({
    id: c.id,
    name: c.name,
    icon: c.badge_icon,
    color: SUBJECT_COLORS[c.subject] || '#5d4037',
    used: cardUsage.value[c.id] || 0,
    max_use: c.max_use || 2,
  })),
)

// 通关文案
const clearanceMessage = computed(() => {
  if (allCleared.value) {
    const rate = accuracyPct.value
    if (rate >= 90) return '完美学家 🏆'
    if (rate >= 70) return '出色探汤局 🌟'
    return '通关完成 ✅'
  }
  return '继续向 4 层汤底推进'
})

// 4 层解锁进度
const layerProgress = computed(() => [
  { key: 'phenomenon', name: '现象层', icon: '🌱', hint: '盐湖非生物结核', combo: 'G1 徐霞客 + G2 沈括' },
  { key: 'condition', name: '条件层', icon: '🌡️', hint: '多盐共饱和 + 低温析晶', combo: 'G5 墨子 + G6 宋应星' },
  { key: 'microscopic', name: '微观层', icon: '🔬', hint: '酸碱反应 + 沉淀溶解', combo: 'G3 祖冲之 + G4 李时珍' },
  { key: 'ultimate', name: '终极层', icon: '🏔️', hint: '四层证据整合', combo: 'G7 徐光启 + 任意' },
].map(l => ({ ...l, unlocked: unlockedLayers.value.includes(l.key) })))

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) {
    const offset = 90
    const top = el.getBoundingClientRect().top + window.pageYOffset - offset
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [stateRes, cardsRes] = await Promise.all([
      axios.get(`/api/room/state/${roomId.value}`),
      axios.get('/api/cards'),
    ])
    const s = stateRes.data.room
    negationBoard.value = s.negation_board
    questionsLog.value = s.questions_log
    cluesLog.value = s.clues_log
    cardUsage.value = s.card_usage
    unlockedLayers.value = s.unlocked_layers
    cards.value = cardsRes.data.cards

    if (allCleared.value) {
      setTimeout(() => burst(50), 400)
      setTimeout(() => burst(40), 900)
    }
  } catch (e: any) {
    loadError.value = `加载失败: ${e?.message || '后端未启动'}`
    console.error('[debrief] load failed', e)
  } finally {
    loading.value = false
  }
}

function cardName(id: string): string {
  const c = cards.value.find(c => c.id === id)
  return c ? `${c.badge_icon}${c.name}` : id
}

function labelOf(clueId: string): string {
  for (const c of cards.value) {
    const clue = (c.clues || []).find((cl: any) => cl.id === clueId)
    if (clue) return clue.label
  }
  return clueId
}

const LAYER_NAMES: Record<string, string> = {
  phenomenon: '现象层',
  condition: '条件层',
  microscopic: '微观层',
  ultimate: '终极层',
}
const LAYER_ICONS: Record<string, string> = {
  phenomenon: '🌱',
  condition: '🌡️',
  microscopic: '🔬',
  ultimate: '🏔️',
}
function layerName(k: string) { return LAYER_NAMES[k] || k }
function layerIcon(k: string) { return LAYER_ICONS[k] || '📘' }

function exportPDF() {
  document.body.classList.add('printing-debrief')
  setTimeout(() => {
    window.print()
    setTimeout(() => document.body.classList.remove('printing-debrief'), 500)
  }, 100)
}

onMounted(load)
</script>

<style scoped>
/* ============ 基础 ============ */
.debrief-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 10% 0%, #fff8e1 0%, transparent 40%),
    radial-gradient(circle at 90% 100%, #f3e5f5 0%, transparent 45%),
    linear-gradient(180deg, #faf6ef 0%, #f5efe3 100%);
  padding-bottom: 60px;
}

/* ============ 顶部英雄区 ============ */
.db-hero {
  position: relative;
  padding: 56px 20px 40px;
  text-align: center;
  overflow: hidden;
  background: linear-gradient(135deg, #5d4037 0%, #795548 50%, #a1887f 100%);
  color: #fff;
  margin-bottom: 28px;
  border-bottom: 4px solid #b8875a;
}
.db-hero.is-clear {
  background: linear-gradient(135deg, #b8875a 0%, #d4a574 50%, #efb87e 100%);
  border-bottom-color: #f56c6c;
}
.hero-decor { position: absolute; inset: 0; pointer-events: none; }
.deco-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.12);
}
.deco-ring.r1 { width: 320px; height: 320px; top: -120px; right: -80px; }
.deco-ring.r2 { width: 220px; height: 220px; bottom: -100px; left: -60px; }
.deco-ring.r3 { width: 140px; height: 140px; top: 40%; left: 18%; border-color: rgba(255,255,255,0.08); }

.hero-inner { position: relative; max-width: 1100px; margin: 0 auto; }
.hero-emoji {
  font-size: 48px;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,0.2));
  margin-bottom: 8px;
}
.hero-title {
  margin: 0 0 8px;
  font-size: 38px;
  font-weight: 800;
  letter-spacing: 2px;
  text-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.hero-sub {
  margin: 0 0 24px;
  font-size: 14px;
  opacity: 0.9;
}

.hero-strip {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  padding: 14px 28px;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 999px;
  backdrop-filter: blur(8px);
  font-size: 14px;
}
.hs-item { display: inline-flex; align-items: baseline; gap: 6px; color: rgba(255,255,255,0.85); }
.hs-num { font-size: 22px; font-weight: 800; color: #fff; }
.hs-num.gold { color: #ffe066; }
.hs-num.warn { color: #ff7878; }
.hs-sep { opacity: 0.6; font-size: 14px; }
.hs-label { font-size: 12px; opacity: 0.85; }
.hs-divider {
  width: 1px;
  height: 18px;
  background: rgba(255,255,255,0.3);
}

.hero-badge {
  margin-top: 22px;
  display: inline-block;
  padding: 8px 18px;
  background: rgba(0,0,0,0.25);
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1px;
}

/* ============ 快捷导航（粘性） ============ */
.quick-nav {
  position: sticky;
  top: 12px;
  z-index: 50;
  max-width: 1100px;
  margin: 0 auto 24px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(10px);
  border-radius: 999px;
  box-shadow: 0 4px 20px rgba(93,64,55,0.12);
  border: 1px solid rgba(184,135,90,0.15);
}
.nav-label {
  font-size: 13px;
  font-weight: 700;
  color: #5d4037;
  margin-right: 4px;
  padding-left: 8px;
}
.nav-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  background: #faf6ef;
  color: #5d4037;
  font-weight: 600;
  border: 1px solid transparent;
}
.nav-pill:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.nav-pill em {
  font-style: normal;
  background: rgba(0,0,0,0.08);
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 11px;
  font-weight: 700;
}
.nav-pill.disabled { opacity: 0.4; pointer-events: none; }
.nav-pill.pill-danger   { color: #c45656; background: #fff0f0; }
.nav-pill.pill-success  { color: #5a8c4f; background: #f0f9eb; }
.nav-pill.pill-warn     { color: #b8851c; background: #fdf6ec; }
.nav-pill.pill-info     { color: #4f7eb8; background: #ecf5ff; }
.nav-pill.pill-primary  { color: #6a4f3e; background: #f5ebe0; }

/* ============ 主体 & 卡片通用 ============ */
.db-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.card {
  background: #fff;
  border-radius: 14px;
  padding: 22px 26px;
  box-shadow: 0 4px 18px rgba(93,64,55,0.06);
  border: 1px solid rgba(184,135,90,0.1);
  scroll-margin-top: 100px;
}
.card-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px dashed #f0e8d8;
}
.card-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  background: linear-gradient(135deg, #d4a574, #b8875a);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
}
.card h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #5d4037;
  display: inline;
  letter-spacing: 0.5px;
}
.card-sub-en {
  font-size: 14px;
  font-weight: 500;
  color: #b8875a;
  margin-left: 4px;
}
.card-sub {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}
.card-count {
  background: linear-gradient(135deg, #fde6c8, #fcd9a1);
  color: #8d6e63;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.card-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.card-pill-combo {
  background: linear-gradient(135deg, #fff7e6, #ffe7ba);
  color: #b88700;
  border: 1px solid #ffd591;
}

.empty {
  text-align: center;
  padding: 36px 20px;
  border-radius: 10px;
  background: #faf6ef;
  color: #8d6e63;
}
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.empty-text { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.empty-sub { font-size: 12px; color: #b8a594; }
.empty-success { background: #f0f9eb; color: #5a8c4f; }
.empty-info { background: #ecf5ff; color: #4f7eb8; }

/* ============ Stats 卡片 ============ */
.stats-card {
  background: linear-gradient(135deg, #fff 0%, #fdf8f0 100%);
  border: 1px solid #f0d8b0;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px 18px;
  border-radius: 12px;
  background: #faf6ef;
  border: 1px solid #f0e8d8;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s;
}
.stat::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--accent, transparent);
  opacity: 0.06;
  pointer-events: none;
}
.stat:hover { transform: translateY(-2px); }
.stat-icon {
  font-size: 28px;
  width: 44px; height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  flex-shrink: 0;
}
.stat-meta { flex: 1; min-width: 0; }
.stat-num {
  font-size: 26px;
  font-weight: 800;
  color: #5d4037;
  line-height: 1.1;
  letter-spacing: -0.5px;
}
.stat-num small { font-size: 14px; opacity: 0.6; margin-left: 2px; font-weight: 700; }
.stat-label { font-size: 12px; color: #8d6e63; margin-top: 2px; font-weight: 600; }
.stat-bar {
  height: 5px;
  background: rgba(0,0,0,0.06);
  border-radius: 999px;
  margin-top: 8px;
  overflow: hidden;
}
.stat-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #d4a574, #b8875a);
  border-radius: 999px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.stat-hint { font-size: 11px; color: #909399; margin-top: 5px; }

/* 各 stat 个性化色调 */
.stat-ask   { --accent: #409eff; }
.stat-ask .stat-bar-fill { background: linear-gradient(90deg, #79bbff, #409eff); }

.stat-wrong { --accent: #f56c6c; }
.stat-wrong.active { background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%); border-color: #fab6b6; }
.stat-wrong .stat-bar-fill { background: linear-gradient(90deg, #fab6b6, #f56c6c); }

.stat-clue  { --accent: #67c23a; }
.stat-clue .stat-bar-fill  { background: linear-gradient(90deg, #95d475, #67c23a); }

.stat-layer { --accent: #b8875a; }
.stat-layer.complete {
  background: linear-gradient(135deg, #fff8e1 0%, #fde6c8 100%);
  border-color: #ffd591;
}
.stat-layer .stat-bar-fill { background: linear-gradient(90deg, #efb87e, #d4a574); }
.stat-layer.complete .stat-bar-fill { background: linear-gradient(90deg, #ffd591, #d4a574); }

/* ============ 否决板 ============ */
.wrongs-card {
  border-left: 5px solid #f56c6c;
  background: linear-gradient(180deg, #fff 0%, #fffaf9 100%);
}
.negation-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.negation-item {
  display: flex;
  gap: 14px;
  align-items: stretch;
  padding: 14px 16px;
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  border: 1px solid #fab6b6;
  border-radius: 10px;
}
.ni-num {
  flex-shrink: 0;
  width: 36px; height: 36px;
  background: #f56c6c;
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 2px 6px rgba(245,108,108,0.3);
}
.ni-body { flex: 1; min-width: 0; }
.ni-text {
  font-size: 14px;
  color: #4a3530;
  text-decoration: line-through;
  text-decoration-color: rgba(245,108,108,0.6);
  line-height: 1.6;
  margin-bottom: 6px;
}
.ni-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
}
.ni-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.5px;
}
.ni-tag-wrong { background: #f56c6c; color: #fff; }
.ni-answer { color: #8d6e63; }
.ni-answer strong {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 6px;
  font-weight: 800;
  margin-left: 4px;
}
.answer-yes { background: #67c23a; color: #fff; }
.answer-no { background: #909399; color: #fff; }
.ni-kp { color: #b8a594; font-style: italic; }

/* ============ 层进度 ============ */
.layers-card {
  border-left: 5px solid #b8875a;
  background: linear-gradient(180deg, #fff 0%, #fef9f3 100%);
}
.layer-track {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.layer-slot {
  position: relative;
  padding: 18px 14px;
  border-radius: 12px;
  border: 2px solid #f0e8d8;
  background: #faf6ef;
  text-align: center;
  transition: all 0.3s;
  opacity: 0.5;
  filter: grayscale(0.6);
}
.layer-slot.unlocked {
  opacity: 1;
  filter: none;
  background: linear-gradient(180deg, #fff 0%, #fdf8f0 100%);
  border-color: var(--layer-color, #b8875a);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.ls-num {
  position: absolute;
  top: 8px; left: 10px;
  font-size: 11px;
  font-weight: 800;
  color: #b8a594;
  opacity: 0.7;
}
.layer-slot.unlocked .ls-num { opacity: 1; }
.ls-icon { font-size: 32px; margin-bottom: 6px; }
.ls-name {
  font-size: 15px;
  font-weight: 800;
  color: #5d4037;
  margin-bottom: 4px;
}
.ls-hint {
  font-size: 11px;
  color: #8d6e63;
  line-height: 1.5;
  margin-bottom: 8px;
}
.ls-combo {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: var(--layer-color, #b8875a);
  color: #fff;
}
.ls-combo-locked {
  background: #e0e0e0;
  color: #909399;
}
.layer-slot.layer-phenomenon { --layer-color: #67c23a; }
.layer-slot.layer-condition { --layer-color: #409eff; }
.layer-slot.layer-microscopic { --layer-color: #e6a23c; }
.layer-slot.layer-ultimate { --layer-color: #f56c6c; }

/* ============ 线索图谱（时间轴） ============ */
.clues-card {
  border-left: 5px solid #67c23a;
  background: linear-gradient(180deg, #fff 0%, #f8fcf6 100%);
}
.clue-timeline {
  position: relative;
  padding-left: 32px;
}
.clue-node { position: relative; padding-bottom: 18px; }
.clue-node:last-child { padding-bottom: 0; }
.cn-rail {
  position: absolute;
  left: -28px;
  top: 8px;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.cn-dot {
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid #d4a574;
  box-shadow: 0 0 0 3px rgba(212,165,116,0.18);
  z-index: 1;
}
.layer-phenomenon .cn-dot { border-color: #67c23a; box-shadow: 0 0 0 3px rgba(103,194,58,0.18); }
.layer-condition .cn-dot { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.18); }
.layer-microscopic .cn-dot { border-color: #e6a23c; box-shadow: 0 0 0 3px rgba(230,162,60,0.18); }
.layer-ultimate .cn-dot { border-color: #f56c6c; box-shadow: 0 0 0 3px rgba(245,108,108,0.18); }
.cn-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(180deg, #e8e0d0, transparent);
  margin-top: 4px;
}
.cn-card {
  background: #fff;
  border-radius: 10px;
  padding: 14px 18px;
  border: 1px solid #f0e8d8;
  border-left: 4px solid #d4a574;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  transition: transform 0.2s;
}
.cn-card:hover { transform: translateX(2px); }
.layer-phenomenon .cn-card { border-left-color: #67c23a; }
.layer-condition .cn-card { border-left-color: #409eff; }
.layer-microscopic .cn-card { border-left-color: #e6a23c; }
.layer-ultimate .cn-card { border-left-color: #f56c6c; }

.clue-node.is-combo .cn-card {
  background: linear-gradient(135deg, #fff7e6 0%, #fff1cf 100%);
  border: 2px solid #ffd591;
  border-left-width: 6px;
  box-shadow: 0 4px 14px rgba(230,162,60,0.18);
}
.clue-node.is-combo .cn-dot {
  border-color: #e6a23c;
  background: linear-gradient(135deg, #ffd591, #ffba5c);
}

.cn-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.cn-title { font-size: 14px; font-weight: 700; color: #5d4037; }
.cn-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}
.cn-tag-combo {
  background: linear-gradient(135deg, #ffd591, #ffba5c);
  color: #8b5a00;
}
.cn-tag-layer {
  background: #f5f5f5;
  color: #5d4037;
  border: 1px solid #e8e0d0;
}
.layer-tag-phenomenon { background: #f0f9eb !important; color: #5a8c4f !important; border-color: #c2e7b0 !important; }
.layer-tag-condition { background: #ecf5ff !important; color: #4f7eb8 !important; border-color: #b3d8ff !important; }
.layer-tag-microscopic { background: #fdf6ec !important; color: #b8851c !important; border-color: #faecd8 !important; }
.layer-tag-ultimate { background: #fef0f0 !important; color: #c45656 !important; border-color: #fbc4c4 !important; }

.cn-card-tag {
  margin-left: auto;
  background: #faf6ef;
  color: #8d6e63;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid #f0e8d8;
}
.cn-body {
  background: rgba(250,246,239,0.8);
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.7;
  color: #3d3530;
  margin: 0 0 6px;
  border-left: 3px solid rgba(184,135,90,0.3);
}
.clue-node.is-combo .cn-body {
  background: rgba(255,255,255,0.85);
  border-left-color: #ffd591;
  font-weight: 500;
}
.cn-kp {
  font-size: 11px;
  color: #909399;
  font-style: italic;
}

/* ============ 武将图鉴 ============ */
.generals-card {
  border-left: 5px solid #b8875a;
  background: linear-gradient(180deg, #fff 0%, #fef9f3 100%);
}
.generals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}
.radar-block {
  margin: 0 -8px 24px;
  padding: 18px 22px 14px;
  background: linear-gradient(160deg, #fff8e1 0%, #fdf6e3 100%);
  border-radius: 14px;
  border: 1px dashed #d4a574;
  grid-column: 1 / -1;
  position: relative;
}
.radar-block::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 14px;
  background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><filter id='n'><feTurbulence baseFrequency='0.9'/><feColorMatrix values='0 0 0 0 0.5 0 0 0 0 0.4 0 0 0 0 0.2 0 0 0 0.05 0'/></filter><rect width='100' height='100' filter='url(%23n)'/></svg>");
  opacity: 0.4;
  pointer-events: none;
}
.radar-block-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  position: relative;
  z-index: 1;
}
.radar-icon {
  font-size: 22px;
  filter: drop-shadow(0 1px 2px rgba(139, 90, 28, 0.3));
}
.radar-title {
  font-family: 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 18px;
  font-weight: 800;
  color: #5d4037;
  letter-spacing: 2px;
}
.radar-sub {
  font-size: 11px;
  color: #8b5a1c;
  opacity: 0.7;
  letter-spacing: 1px;
  margin-left: auto;
}
.general-mini {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 14px 12px 12px;
  text-align: center;
  border: 2px solid transparent;
  transition: all 0.2s;
  opacity: 0.55;
  filter: grayscale(0.5);
}
.general-mini.lit {
  background: linear-gradient(135deg, #fff8e1 0%, #ffe7ba 100%);
  border-color: #d4a574;
  opacity: 1;
  filter: none;
  box-shadow: 0 4px 12px rgba(212,165,116,0.25);
  transform: translateY(-1px);
}
.gm-icon {
  font-size: 36px;
  margin-bottom: 6px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}
.gm-name {
  font-size: 14px;
  font-weight: 800;
  color: #5d4037;
  margin-bottom: 6px;
}
.gm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
  justify-content: center;
}
.gm-tag {
  font-size: 10px;
  background: rgba(255,255,255,0.85);
  padding: 2px 8px;
  border-radius: 4px;
  color: #5d4037;
  font-weight: 600;
}
.general-mini.lit .gm-tag {
  background: rgba(255,255,255,1);
  color: #8d6e63;
}
.gm-usage {
  font-size: 11px;
  font-weight: 700;
  padding-top: 6px;
  border-top: 1px dashed rgba(184,135,90,0.3);
  color: #909399;
}
.general-mini.lit .gm-usage { color: #b8851c; }

/* ============ 底部操作 ============ */
.footer-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin: 40px auto 0;
  padding: 0 20px;
  flex-wrap: wrap;
}

/* ============ 撒花粒子 ============ */
.fireworks-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  overflow: hidden;
}
.particle {
  position: absolute;
  will-change: transform, opacity;
  filter: drop-shadow(0 0 6px currentColor);
}
.loading-box { margin-bottom: 20px; max-width: 1100px; margin: 0 auto 20px; }

/* ============ 响应式 ============ */
@media (max-width: 768px) {
  .stat-row, .layer-track { grid-template-columns: repeat(2, 1fr); }
  .hero-strip { flex-wrap: wrap; gap: 12px; }
  .hero-title { font-size: 28px; }
  .card { padding: 16px; }
}

/* ============ 打印 ============ */
@media print {
  body.printing-debrief { background: #fff !important; }
  .db-hero {
    background: #fff !important;
    color: #5d4037 !important;
    border-bottom: 2px solid #b8875a !important;
    padding: 20px 0 !important;
  }
  .db-hero h1, .db-hero p, .hero-strip, .hero-badge { color: #5d4037 !important; }
  .hero-decor { display: none; }
  .quick-nav, .footer-actions, .el-button { display: none !important; }
  .db-body { display: block !important; max-width: 100% !important; padding: 0 !important; }
  .db-body > .card {
    page-break-inside: avoid;
    break-inside: avoid;
    margin-bottom: 12px;
    box-shadow: none !important;
    border: 1px solid #d4a574 !important;
  }
  .stats-card { page-break-before: always !important; }
  .stat-num { font-size: 22px !important; }
  .general-mini { opacity: 1 !important; filter: none !important; }
}
</style>