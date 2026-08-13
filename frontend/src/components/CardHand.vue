<template>
  <div class="card-hand">
    <div class="card-hand-header">
      <h3 class="section-title">
        🎴 武将手牌
        <el-tag size="small" :type="usedCount > 0 ? 'warning' : 'success'">
          可用 {{ usableCount }}/{{ cards.length }}
        </el-tag>
        <transition name="hint-fade">
          <span v-if="highlightCardId" class="hint-badge">
            💡 建议出牌：{{ highlightCardName }}
          </span>
        </transition>
      </h3>
      <div class="header-actions">
        <el-button
          v-if="!allUsedUp"
          type="warning"
          size="small"
          class="combo-launch-btn"
          @click="$emit('open-combo')"
        >
          ⚡ 选 2 张卡合技 → 解锁整层
        </el-button>
        <el-button
          size="small"
          plain
          :title="cardBarCollapsed ? '展开武将手牌' : '收起武将手牌，隐藏全部卡牌'"
          class="collapse-toggle"
          @click="$emit('toggle-collapse')"
        >
          {{ cardBarCollapsed ? '▼ 展开手牌' : '▲ 收起手牌' }}
        </el-button>
      </div>
    </div>

    <div v-if="allUsedUp" class="all-used-banner">
      ⚠️ 武将卡全部用尽。点击底部「查看复盘报告」可跳过出牌环节。
    </div>

    <div class="cards-strip">
      <article
        v-for="card in cards"
        :key="card.id"
        :id="`card-${card.id}`"
        class="general-card"
        :class="[
          `dynasty-${dynastyOf(card.id)}`,
          `subject-${subjectKey(card.subject)}`,
          {
            'used-up': (cardUsage[card.id] || 0) >= card.max_use,
            'highlighted': highlightCardId === card.id,
            'just-played': lastPlayedId === card.id,
            'unselectable': (cardUsage[card.id] || 0) >= card.max_use,
            'flash-focused': flashCardId === card.id,
            'is-flipped': flippedCards.has(card.id),
          }
        ]"
        :style="{ '--card-accent': colorOf(card) }"
        @click="(cardUsage[card.id] || 0) < card.max_use && emit('select-card', card)"
      >
        <!-- 🌀 3D 翻转包裹器 -->
        <div class="card-flip-inner">
          <!-- === 正面 === -->
          <div class="card-face card-front">
        <!-- 顶层装饰条 -->
        <div class="card-bar"></div>
        <!-- 角装饰 -->
        <span class="corner tl"></span>
        <span class="corner tr"></span>
        <span class="corner bl"></span>
        <span class="corner br"></span>

        <!-- 内框底纹 -->
        <div class="card-pattern" aria-hidden="true">
          <span class="pat-dot" v-for="i in 6" :key="i"></span>
        </div>

        <!-- 状态浮层：用尽了 -->
        <div v-if="(cardUsage[card.id] || 0) >= card.max_use" class="used-up-overlay">
          <span class="uo-mark">封</span>
          <span class="uo-text">卡已用尽</span>
        </div>

        <!-- 头像区：SVG 古人像 -->
        <div class="card-portrait">
          <div class="portrait-ring"></div>
          <div class="portrait-svg">
            <GeneralPortrait :card-id="card.id" :subject="card.subject" :accent="colorOf(card)" />
          </div>
          <div class="portrait-subject">{{ shortSubject(card.subject) }}</div>
          <button
            class="flip-toggle-btn"
            :title="flippedCards.has(card.id) ? '翻回正面' : '翻到背面看技能详情'"
            @click.stop="toggleFlip(card.id)"
          >
            🔄
          </button>
        </div>

        <!-- 姓名 + 朝代 -->
        <div class="card-name">
          <span class="cn-name">{{ card.name }}</span>
          <span class="cn-dynasty">{{ dynastyOf(card.id) }}朝</span>
        </div>

        <!-- 称号 -->
        <div class="card-title">「{{ card.skill_name || card.title }}」</div>

        <!-- 视角印章 -->
        <div class="card-seal" :title="card.thinking_view">
          <span class="seal-text">{{ (card.thinking_view || '').replace(/视角$/, '') }}</span>
        </div>

        <!-- 底部条：标签 + 使用次数 -->
        <div class="card-foot">
          <el-tag size="small" :type="categoryTag(card.category)" effect="dark" round>
            {{ card.category }}
          </el-tag>
          <div class="usage-dots">
            <span
              v-for="i in card.max_use"
              :key="i"
              class="usage-dot"
              :class="{ used: i <= (cardUsage[card.id] || 0) }"
            ></span>
          </div>
        </div>

        <!-- 高亮光圈 -->
        <div v-if="highlightCardId === card.id" class="highlight-ring" aria-hidden="true"></div>
          </div>
          <!-- === 背面：技能详情 === -->
          <div class="card-face card-back">
            <div class="card-bar back"></div>
            <span class="corner tl"></span>
            <span class="corner tr"></span>
            <span class="corner bl"></span>
            <span class="corner br"></span>
            <div class="back-inner">
              <div class="back-header">
                <span class="back-dynasty">{{ dynastyOf(card.id) }}代</span>
                <span class="back-cn-name">{{ card.name }}</span>
                <span class="back-cat">{{ card.category }}</span>
              </div>
              <div class="back-title">「{{ card.skill_name || card.title }}」</div>
              <div class="back-skill">{{ card.skill_text }}</div>
              <div class="back-divider">· 高考考点 ·</div>
              <div class="back-tags">
                <span v-for="t in (card.exam_tags || [])" :key="t" class="back-tag">{{ t }}</span>
              </div>
              <div class="back-view">{{ card.thinking_view }}</div>
              <button class="flip-toggle-btn back-btn" @click.stop="toggleFlip(card.id)">
                🔄 翻回正面
              </button>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import GeneralPortrait from './GeneralPortrait.vue'

const props = defineProps<{
  cards: any[]
  cardUsage: Record<string, number>
  highlightCardId?: string
  flashCardId?: string
  cardBarCollapsed?: boolean
}>()
const emit = defineEmits<{
  (e: 'select-card', card: any): void
  (e: 'open-combo'): void
  (e: 'toggle-collapse'): void
}>()

// 收到外来 flashCardId 变化 → 滚动到对应武将卡 + 闪烁高亮
watch(() => props.flashCardId, async (id) => {
  if (!id) return
  await nextTick()
  const el = document.getElementById(`card-${id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' })
  }
  setTimeout(() => {
    // 闪烁超时由父级控制：2.5s 后传空值
  }, 2500)
})

// 朝代映射（G1-G7 都是历史名人，标注朝代）
const DYNASTIES: Record<string, string> = {
  G1_xuxiake: '明',
  G2_shenkuo: '宋',
  G3_zuchongzhi: '南北朝',
  G4_lishizhen: '明',
  G5_mozi: '战国',
  G6_songyingxing: '明',
  G7_xuguangqi: '明',
}

// 学科 → 颜色（主色 + 高亮）
const SUBJECT_PALETTE: Record<string, string> = {
  '地理':           '#2d5a4f',
  '地理 + 历史':    '#6b4423',
  '数学 + 化学':    '#1e3a2c',
  '生物':           '#4a7c59',
  '物理':           '#1a2e5a',
  '数学':           '#5b2c5f',
  '综合':           '#8b5a1c',
}

function dynastyOf(id: string): string {
  return DYNASTIES[id] || ''
}

function subjectKey(subject: string): string {
  // 把 "地理 + 历史" 这种命名转换成 css-safe 字符串
  return subject.replace(/\s*\+\s*/g, '_').replace(/\s/g, '_')
}

function colorOf(card: any): string {
  return SUBJECT_PALETTE[card.subject] || '#5d4037'
}

function shortSubject(subject: string): string {
  // 显示用：去掉"+"号，只显示主学科
  if (subject.includes('+')) return subject.split('+')[0].trim()
  return subject
}

const lastPlayedId = ref<string>('')
watch(() => {
  return Object.entries(props.cardUsage).map(([k, v]) => `${k}:${v}`).join('|')
}, () => {
  const entries = Object.entries(props.cardUsage)
  if (!entries.length) return
  const sorted = [...entries].sort((a, b) => b[1] - a[1])
  lastPlayedId.value = sorted[0][0]
}, { immediate: true })

// 🌀 卡牌 3D 翻转状态（localStorage 记忆）
const flippedCards = ref<Set<string>>(
  new Set(JSON.parse(localStorage.getItem('tangtanju.cards.flipped') || '[]'))
)
watch(flippedCards, v => {
  localStorage.setItem('tangtanju.cards.flipped', JSON.stringify(Array.from(v)))
}, { deep: true })
function toggleFlip(cardId: string) {
  const next = new Set(flippedCards.value)
  if (next.has(cardId)) next.delete(cardId)
  else next.add(cardId)
  flippedCards.value = next
}

const highlightCardName = computed(() => {
  const c = props.cards.find(c => c.id === props.highlightCardId)
  return c ? `${c.badge_icon} ${c.name}` : ''
})

const usedCount = computed(() =>
  props.cards.filter(c => (props.cardUsage[c.id] || 0) >= c.max_use).length
)
const usableCount = computed(() => props.cards.length - usedCount.value)
const allUsedUp = computed(() => props.cards.length > 0 && usableCount.value === 0)

function categoryTag(cat: string): 'success' | 'warning' | 'primary' | 'info' {
  if (cat === '物质类') return 'success'
  if (cat === '环境变量类') return 'warning'
  if (cat === '力学系统类') return 'primary'
  return 'info'
}
</script>

<style scoped>
.card-hand {
  padding: 16px 18px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(250,246,239,0.95) 100%),
    repeating-linear-gradient(45deg, #f5efe3 0 6px, transparent 6px 12px);
  border-radius: 14px;
  margin: 12px 12px 0;
  border: 1px solid rgba(212, 165, 116, 0.25);
  box-shadow:
    0 8px 24px rgba(141, 85, 36, 0.1),
    inset 0 1px 0 rgba(255,255,255,0.6);
}
.card-hand-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.section-title {
  margin: 0;
  font-size: 17px;
  color: #3e2723;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.combo-launch-btn {
  font-weight: bold;
  animation: combo-pulse 2s ease-in-out infinite;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.collapse-toggle {
  font-weight: 600 !important;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #faf6ef 0%, #f0e8d8 100%) !important;
  border-color: #d4a574 !important;
  color: #b8875a !important;
  transition: all 0.2s !important;
}
.collapse-toggle:hover {
  background: linear-gradient(135deg, #fff8e1 0%, #ffe0b2 100%) !important;
  border-color: #b8875a !important;
  color: #8d5524 !important;
  transform: translateY(-1px);
}
@keyframes combo-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.5); }
  50% { box-shadow: 0 0 0 8px rgba(230, 162, 60, 0); }
}
.hint-badge {
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(90deg, #ffd54f, #ff9800);
  color: #5d4037;
  padding: 4px 10px;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(255, 152, 0, 0.3);
}
.hint-fade-enter-active, .hint-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.hint-fade-enter-from, .hint-fade-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
.all-used-banner {
  background: linear-gradient(90deg, #fff7e6, #ffe7b3);
  border: 1px solid #ffc069;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 12px;
  color: #874d00;
  font-size: 13px;
}
.cards-strip {
  display: flex;
  flex-direction: row;
  gap: 14px;
  overflow-x: auto;
  padding: 8px 4px 12px;
  scrollbar-width: thin;
  -webkit-overflow-scrolling: touch;
}
.cards-strip::-webkit-scrollbar { height: 8px; }
.cards-strip::-webkit-scrollbar-thumb {
  background: #d4a574;
  border-radius: 4px;
}

/* ====================================================================== */
/* 武将卡本体 — 像古风令牌/RPG 卡牌 */
.general-card {
  flex: 0 0 200px;
  height: 300px;
  position: relative;
  border-radius: 14px;
  cursor: pointer;
  background: linear-gradient(180deg, #fffaf0 0%, #f5e6d3 100%);
  border: 2px solid var(--card-accent, #5d4037);
  box-shadow:
    0 6px 14px rgba(0,0,0,0.12),
    inset 0 0 0 1px rgba(255,255,255,0.6),
    inset 0 -3px 0 rgba(0,0,0,0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.25s, border-color 0.2s;
  transform-style: preserve-3d;
  will-change: transform;
}
.general-card:hover {
  transform: translateY(-8px) rotate(-0.8deg);
  box-shadow:
    0 16px 30px rgba(0,0,0,0.18),
    0 0 0 2px var(--card-accent, #5d4037),
    inset 0 0 0 1px rgba(255,255,255,0.7);
}
.general-card:active {
  transform: translateY(-2px) scale(0.98);
}
.general-card.used-up {
  opacity: 0.55;
  cursor: not-allowed;
  filter: grayscale(75%);
  transform: none !important;
}

/* 顶部色带 */
.card-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 8px;
  background: linear-gradient(180deg,
    var(--card-accent, #5d4037) 0%,
    color-mix(in srgb, var(--card-accent, #5d4037) 60%, #000) 100%);
  z-index: 2;
}

/* 角装饰 */
.corner {
  position: absolute;
  width: 18px; height: 18px;
  border: 2px solid var(--card-accent, #5d4037);
  z-index: 2;
  pointer-events: none;
}
.corner.tl { top: 6px; left: 6px; border-right: none; border-bottom: none; border-top-left-radius: 8px; }
.corner.tr { top: 6px; right: 6px; border-left: none; border-bottom: none; border-top-right-radius: 8px; }
.corner.bl { bottom: 6px; left: 6px; border-right: none; border-top: none; border-bottom-left-radius: 8px; }
.corner.br { bottom: 6px; right: 6px; border-left: none; border-top: none; border-bottom-right-radius: 8px; }

/* 底纹点 */
.card-pattern {
  position: absolute;
  inset: 14px 10px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 12px;
  opacity: 0.04;
  pointer-events: none;
  z-index: 0;
}
.pat-dot {
  width: 6px; height: 6px;
  background: var(--card-accent, #5d4037);
  border-radius: 50%;
  margin: auto;
}

/* 头像圆盘 */
.card-portrait {
  position: relative;
  width: 90px;
  height: 90px;
  margin-top: 8px;
  border-radius: 50%;
  background: linear-gradient(160deg, #fff8e1 0%, #f5e6d3 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 4px 10px rgba(0,0,0,0.25),
    inset 0 0 0 3px #f5e6d3,
    inset 0 0 0 5px var(--card-accent, #5d4037),
    inset 0 0 0 7px #f5e6d3;
  z-index: 1;
  overflow: hidden;
  flex-shrink: 0;
}
.portrait-ring {
  position: absolute;
  inset: -8px;
  border: 2px dashed var(--card-accent, #5d4037);
  border-radius: 50%;
  opacity: 0.5;
  animation: ring-rotate 12s linear infinite;
}
.portrait-icon {
  font-size: 40px;
  line-height: 1;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
  z-index: 2;
}
.portrait-subject {
  position: absolute;
  bottom: -10px;
  background: var(--card-accent, #5d4037);
  color: #fff;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  z-index: 3;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.portrait-svg {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  overflow: hidden;
  background: #fff8e1;
  z-index: 2;
  position: relative;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  display: block;
}

/* 🌀 3D 翻转包裹 */
.card-flip-inner {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 0.7s cubic-bezier(0.4, 0.2, 0.2, 1);
  perspective: 1200px;
}
.general-card.is-flipped .card-flip-inner {
  transform: rotateY(180deg);
}
.card-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(160deg, #fdf6ec 0%, #f5e9d4 100%);
  border: 1px solid rgba(212, 165, 116, 0.4);
  border-radius: 14px;
  box-shadow: 0 6px 16px rgba(139, 90, 28, 0.18);
  overflow: hidden;
  padding: 12px 10px 10px;
  align-items: center;
  text-align: center;
}
.card-back {
  transform: rotateY(180deg);
  background: linear-gradient(160deg, #2c3e50 0%, #1a2530 100%);
  border-color: #5d4037;
  color: #fdf6e3;
  padding: 8px 12px 12px;
  border-radius: 14px;
  align-items: stretch;
  text-align: left;
}
.card-back .card-bar.back {
  background: linear-gradient(90deg, #f4d03f 0%, #d4a574 50%, #f4d03f 100%);
  height: 4px;
  border-bottom: 1px solid #5d4037;
}
.back-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 4px;
  overflow: hidden;
}
.back-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  font-size: 10px;
  color: #f4d03f;
  letter-spacing: 1px;
}
.back-dynasty {
  background: #f4d03f;
  color: #2c3e50;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 700;
}
.back-cn-name {
  font-size: 16px;
  font-weight: 700;
  color: #fdf6e3;
  font-family: 'STKaiti', 'KaiTi', '楷体', serif;
}
.back-cat {
  margin-left: auto;
  font-size: 9px;
  padding: 1px 5px;
  border: 1px solid #d4a574;
  border-radius: 8px;
  color: #d4a574;
}
.back-title {
  font-family: 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 13px;
  color: #f4d03f;
  text-align: center;
  margin: 4px 0;
  text-shadow: 0 1px 2px rgba(0,0,0,0.4);
}
.back-skill {
  font-size: 10px;
  line-height: 1.4;
  color: #ecf0f1;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.06);
  border-left: 2px solid #f4d03f;
  border-radius: 2px;
}
.back-divider {
  text-align: center;
  font-size: 9px;
  color: #d4a574;
  letter-spacing: 2px;
  margin: 2px 0;
}
.back-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  justify-content: center;
}
.back-tag {
  font-size: 9px;
  padding: 1px 5px;
  background: rgba(244, 208, 63, 0.15);
  color: #f4d03f;
  border: 1px solid rgba(244, 208, 63, 0.3);
  border-radius: 6px;
  letter-spacing: 0.5px;
}
.back-view {
  font-size: 10px;
  color: #d4a574;
  text-align: center;
  font-style: italic;
  margin-top: auto;
  padding: 2px 0;
}
.back-btn {
  margin-top: 4px;
  align-self: center;
}

/* 🔄 翻转按钮 */
.flip-toggle-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(212, 165, 116, 0.6);
  cursor: pointer;
  font-size: 11px;
  line-height: 1;
  padding: 0;
  z-index: 4;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}
.flip-toggle-btn:hover {
  background: #f4d03f;
  border-color: #b8860b;
  transform: rotate(180deg) scale(1.1);
}
.flip-toggle-btn.back-btn {
  position: relative;
  top: auto;
  right: auto;
  width: auto;
  height: auto;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 10px;
  background: rgba(244, 208, 63, 0.2);
  color: #f4d03f;
  border-color: #f4d03f;
  font-weight: 700;
  letter-spacing: 1px;
}
.flip-toggle-btn.back-btn:hover {
  background: #f4d03f;
  color: #2c3e50;
  transform: scale(1.05);
}

/* 姓名 */
.card-name {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  z-index: 1;
}
.cn-name {
  font-family: 'STKaiti', 'KaiTi', '楷体', 'Songti SC', serif;
  font-size: 26px;
  font-weight: 700;
  color: #3e2723;
  letter-spacing: 6px;
  line-height: 1;
  text-shadow:
    1px 1px 0 rgba(255,255,255,0.7),
    0 0 8px rgba(255,255,255,0.5);
}
.cn-dynasty {
  font-size: 10px;
  color: var(--card-accent, #5d4037);
  letter-spacing: 2px;
  font-weight: 600;
  background: rgba(255,255,255,0.6);
  padding: 1px 8px;
  border-radius: 8px;
}

/* 称号 */
.card-title {
  margin-top: 8px;
  font-family: 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 13px;
  color: #5d4037;
  font-weight: 600;
  letter-spacing: 1px;
  line-height: 1.4;
  z-index: 1;
}

/* 视角印章 */
.card-seal {
  margin-top: 6px;
  display: inline-block;
  padding: 3px 10px;
  background: #c0392b;
  color: #fff;
  font-family: 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 11px;
  letter-spacing: 2px;
  font-weight: 700;
  border-radius: 4px;
  transform: rotate(-3deg);
  box-shadow: 0 2px 4px rgba(192,57,43,0.4);
  z-index: 1;
}
.seal-text { display: block; }

/* 底部条 */
.card-foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-top: 8px;
  z-index: 1;
}
.usage-dots { display: flex; gap: 3px; }
.usage-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: rgba(0,0,0,0.15);
  border: 1px solid rgba(0,0,0,0.2);
  transition: all 0.2s;
}
.usage-dot.used {
  background: var(--card-accent, #5d4037);
  border-color: color-mix(in srgb, var(--card-accent, #5d4037) 60%, #000);
  box-shadow: 0 0 4px var(--card-accent, #5d4037);
}

/* 用尽浮层 */
.used-up-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.55);
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-radius: 12px;
  backdrop-filter: blur(2px);
}
.uo-mark {
  font-family: 'STKaiti', 'KaiTi', serif;
  font-size: 60px;
  font-weight: 800;
  color: #f56c6c;
  background: #fff;
  width: 80px; height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(245,108,108,0.5);
  letter-spacing: 0;
}
.uo-text {
  margin-top: 12px;
  font-size: 14px;
  letter-spacing: 4px;
  font-weight: 600;
}

/* 高亮光圈 */
.highlighted {
  animation: hint-pulse 1.6s ease-in-out infinite;
}
.highlight-ring {
  position: absolute;
  inset: -4px;
  border: 2.5px dashed #ff5722;
  border-radius: 16px;
  pointer-events: none;
  z-index: 4;
  animation: ring-rotate 6s linear infinite;
}
@keyframes hint-pulse {
  0%, 100% {
    box-shadow:
      0 6px 14px rgba(0,0,0,0.12),
      0 0 0 0 rgba(255, 87, 34, 0.7),
      inset 0 0 0 1px rgba(255,255,255,0.6);
    transform: translateY(-8px) rotate(-0.8deg);
  }
  50% {
    box-shadow:
      0 6px 14px rgba(0,0,0,0.12),
      0 0 0 12px rgba(255, 87, 34, 0),
      inset 0 0 0 1px rgba(255,255,255,0.6);
    transform: translateY(-12px) rotate(-0.8deg);
  }
}
@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

/* ⚔️ 出牌动画 */
.general-card.just-played {
  animation: card-slam 0.55s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes card-slam {
  0%   { transform: scale(0.6) rotate(8deg); opacity: 0; }
  60%  { transform: scale(1.08) rotate(-3deg); opacity: 1; }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}

/* 🔔 来自线索页跳转的闪烁高亮【只闪 2.5s 后恢复】 */
.flash-focused {
  animation: card-flash 2.4s ease-in-out;
}
@keyframes card-flash {
  0%, 100% {
    box-shadow:
      0 6px 14px rgba(0,0,0,0.12),
      inset 0 0 0 1px rgba(255,255,255,0.6),
      inset 0 -3px 0 rgba(0,0,0,0.05);
  }
  10%, 30% {
    box-shadow:
      0 6px 14px rgba(0,0,0,0.12),
      0 0 0 6px var(--card-accent, #5d4037),
      0 0 24px var(--card-accent, #5d4037),
      inset 0 0 0 1px rgba(255,255,255,0.6),
      inset 0 -3px 0 rgba(0,0,0,0.05);
    transform: scale(1.08) translateY(-4px);
  }
  60% {
    box-shadow:
      0 6px 14px rgba(0,0,0,0.12),
      0 0 0 2px var(--card-accent, #5d4037),
      inset 0 0 0 1px rgba(255,255,255,0.6),
      inset 0 -3px 0 rgba(0,0,0,0.05);
  }
}
</style>
