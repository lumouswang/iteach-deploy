<template>
  <!--
    7 维能力雷达：极坐标 SVG，0 依赖
    轴 = 7 张武将卡；值 = (当前使用次数 / max_use) 归一化到 0~1
  -->
  <div class="ability-radar">
    <svg :viewBox="`0 0 ${VB} ${VB}`" xmlns="http://www.w3.org/2000/svg" class="radar-svg">
      <!-- 极坐标网格 -->
      <g class="radar-grid">
        <polygon
          v-for="(_, ring) in gridRings"
          :key="`ring-${ring}`"
          :points="ringPoints(ring)"
          fill="none"
          :stroke="ring === 0 ? '#8b5a1c' : '#d4a574'"
          :stroke-width="ring === 0 ? 1.5 : 0.6"
          :stroke-dasharray="ring === 0 ? '' : '2 3'"
          :opacity="ring === 0 ? 1 : 0.5"
        />
        <!-- 轴线 -->
        <line
          v-for="(c, i) in cards"
          :key="`axis-${i}`"
          :x1="cx" :y1="cy"
          :x2="axisX(i, 1)" :y2="axisY(i, 1)"
          stroke="#d4a574"
          stroke-width="0.6"
          opacity="0.6"
        />
      </g>

      <!-- 数据多边形 -->
      <polygon
        :points="dataPoints"
        fill="url(#radar-fill)"
        fill-opacity="0.45"
        stroke="#8b5a1c"
        stroke-width="2"
        stroke-linejoin="round"
        class="radar-data"
      />

      <!-- 数据点 -->
      <g>
        <template v-for="(c, i) in cards" :key="`pt-${i}`">
          <circle
            :cx="axisX(i, valueOf(c))"
            :cy="axisY(i, valueOf(c))"
            r="4"
            :fill="c.color || '#8b5a1c'"
            stroke="#fff8e1"
            stroke-width="1.5"
            class="radar-point"
          >
            <title>{{ c.name }}：已用 {{ c.used }}/{{ c.max_use }}</title>
          </circle>
        </template>
      </g>

      <!-- 轴标签 -->
      <g>
        <template v-for="(c, i) in cards" :key="`lbl-${i}`">
          <text
            :x="labelX(i)"
            :y="labelY(i)"
            :text-anchor="labelAnchor(i)"
            dominant-baseline="middle"
            font-size="11"
            font-weight="700"
            :fill="c.color || '#5d4037'"
            font-family="'STKaiti', 'KaiTi', '楷体', serif"
          >
            {{ c.icon }} {{ c.name }}
          </text>
          <text
            :x="labelX(i)"
            :y="labelY(i) + 14"
            :text-anchor="labelAnchor(i)"
            dominant-baseline="middle"
            font-size="9"
            fill="#8b5a1c"
            font-weight="bold"
          >
            {{ c.used }}/{{ c.max_use }}
          </text>
        </template>
      </g>

      <defs>
        <radialGradient id="radar-fill" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stop-color="#f4d03f" stop-opacity="0.7" />
          <stop offset="100%" stop-color="#8b5a1c" stop-opacity="0.4" />
        </radialGradient>
      </defs>
    </svg>

    <div class="radar-summary">
      <div class="rs-item">
        <span class="rs-num">{{ litCount }}</span>
        <span class="rs-label">已点亮</span>
      </div>
      <div class="rs-divider" />
      <div class="rs-item">
        <span class="rs-num">{{ avgPct }}%</span>
        <span class="rs-label">平均使用率</span>
      </div>
      <div class="rs-divider" />
      <div class="rs-item">
        <span class="rs-num max">{{ maxCard.icon }} {{ maxCard.name }}</span>
        <span class="rs-label">使用最多</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  cards: { id: string; name: string; icon: string; color: string; used: number; max_use: number }[]
}>()

const VB = 320
const cx = VB / 2
const cy = VB / 2
const R = 110             // 雷达半径
const labelR = 140         // 标签半径

const gridRings = [0, 0.25, 0.5, 0.75, 1]

function valueOf(c: { used: number; max_use: number }) {
  if (c.max_use <= 0) return 0
  return Math.min(1, c.used / c.max_use)
}

function angle(i: number) {
  // 从顶部开始 -π/2 起，顺时针
  return -Math.PI / 2 + (i * 2 * Math.PI) / props.cards.length
}

function axisX(i: number, ratio: number) { return cx + Math.cos(angle(i)) * R * ratio }
function axisY(i: number, ratio: number) { return cy + Math.sin(angle(i)) * R * ratio }

function ringPoints(ratio: number) {
  return props.cards.map((_, i) => `${axisX(i, ratio)},${axisY(i, ratio)}`).join(' ')
}

const dataPoints = computed(() => props.cards.map((c, i) => {
  const v = valueOf(c)
  return `${axisX(i, v)},${axisY(i, v)}`
}).join(' '))

function labelX(i: number) { return cx + Math.cos(angle(i)) * labelR }
function labelY(i: number) { return cy + Math.sin(angle(i)) * labelR }
function labelAnchor(i: number) {
  const cos = Math.cos(angle(i))
  if (cos > 0.3) return 'start'
  if (cos < -0.3) return 'end'
  return 'middle'
}

const litCount = computed(() => props.cards.filter(c => c.used > 0).length)
const avgPct = computed(() => {
  if (!props.cards.length) return 0
  const total = props.cards.reduce((s, c) => s + valueOf(c), 0) / props.cards.length
  return Math.round(total * 100)
})
const maxCard = computed(() => {
  if (!props.cards.length) return { name: '—', icon: '' }
  return [...props.cards].sort((a, b) => b.used - a.used)[0] || { name: '—', icon: '' }
})
</script>

<style scoped>
.ability-radar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0 4px;
}
.radar-svg {
  width: 100%;
  max-width: 360px;
  height: auto;
  filter: drop-shadow(0 4px 8px rgba(139, 90, 28, 0.12));
}
.radar-data {
  animation: radar-grow 0.8s ease-out;
  transform-origin: center;
}
@keyframes radar-grow {
  from { transform: scale(0.3); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.radar-point {
  animation: radar-pulse 2s ease-in-out infinite;
  cursor: Help;
}
@keyframes radar-pulse {
  0%, 100% { r: 4; }
  50% { r: 5.5; }
}
.radar-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 8px;
}
.rs-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.rs-num {
  font-size: 18px;
  font-weight: 800;
  color: #8b5a1c;
  font-family: 'STKaiti', 'KaiTi', '楷体', serif;
}
.rs-num.max {
  font-size: 14px;
}
.rs-label {
  font-size: 10px;
  color: #5d4037;
  letter-spacing: 1px;
}
.rs-divider {
  width: 1px;
  height: 24px;
  background: rgba(139, 90, 28, 0.3);
}
</style>
