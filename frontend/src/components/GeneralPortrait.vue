<template>
  <!--
    武将人物立绘（真实资产 + SVG 兜底）
    - 优先用 /generals/<id>.jpg（用户提供的豆包 AI 生成图）
    - 图片加载失败时 → 回退到纯 SVG 古人像
    - ViewBox 100x100，圆形裁剪（CSS overflow:hidden on parent）
  -->
  <div class="portrait-wrap">
    <!-- 真实图片 -->
    <img
      v-if="imgPath"
      :src="imgPath"
      :alt="cardId"
      class="portrait-img"
      :class="{ 'is-loaded': imgLoaded }"
      @load="onImgLoad"
      @error="onImgError"
    />
    <!-- SVG 兜底：有图片时隐藏，图片失败时显示 -->
    <svg
      v-if="!imgPath || imgError"
      class="general-portrait"
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <radialGradient :id="`bg-${portraitId}`" cx="50%" cy="35%" r="70%">
          <stop offset="0%" :stop-color="palette.bgInner" />
          <stop offset="100%" :stop-color="palette.bgOuter" />
        </radialGradient>
        <linearGradient :id="`cloak-${portraitId}`" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" :stop-color="palette.cloakTop" />
          <stop offset="100%" :stop-color="palette.cloakBot" />
        </linearGradient>
        <clipPath :id="`clip-${portraitId}`">
          <circle cx="50" cy="50" r="48" />
        </clipPath>
      </defs>

      <g :clip-path="`url(#clip-${portraitId})`">
        <circle cx="50" cy="50" r="48" :fill="`url(#bg-${portraitId})`" />
        <g v-if="scenery !== 'none'" :opacity="0.55">
          <template v-if="scenery === 'mountain'">
            <path d="M 5 78 L 25 50 L 38 65 L 52 42 L 66 58 L 78 48 L 95 78 Z" :fill="palette.mountain" />
            <path d="M 5 78 L 18 62 L 32 70 L 45 55 L 60 68 L 75 60 L 95 78 Z" :fill="palette.mountain2" opacity="0.6" />
          </template>
          <template v-else-if="scenery === 'sea'">
            <path d="M 0 65 Q 15 60 30 65 T 60 65 T 90 65 T 100 65 L 100 100 L 0 100 Z" :fill="palette.sea" />
            <path d="M 0 72 Q 12 68 25 72 T 50 72 T 75 72 T 100 72 L 100 100 L 0 100 Z" :fill="palette.sea" opacity="0.7" />
          </template>
          <template v-else-if="scenery === 'field'">
            <rect x="0" y="68" width="100" height="32" :fill="palette.field" />
            <line v-for="i in 5" :key="`fr-${i}`" x1="0" :y1="72 + i * 4" x2="100" :y2="72 + i * 4" :stroke="palette.furrow" stroke-width="0.4" opacity="0.6" />
          </template>
        </g>
        <line x1="2" y1="68" x2="98" y2="68" :stroke="palette.ground" stroke-width="0.6" />

        <path d="M 18 100 L 18 78 Q 22 65 32 60 L 40 56 L 50 54 L 60 56 L 68 60 Q 78 65 82 78 L 82 100 Z" :fill="`url(#cloak-${portraitId})`" />
        <path d="M 40 56 L 50 70 L 60 56 L 56 54 L 50 60 L 44 54 Z" :fill="palette.collar" />
        <rect x="32" y="82" width="36" height="3" :fill="palette.belt" />
        <circle cx="50" cy="83.5" r="2.2" :fill="palette.buckle" />
        <path d="M 32 60 L 38 100 M 68 60 L 62 100" :stroke="palette.cloakBot" stroke-width="0.4" opacity="0.4" fill="none" />

        <ellipse cx="50" cy="38" rx="14" ry="17" :fill="palette.face" />
        <rect x="46" y="52" width="8" height="6" :fill="palette.neck" />
        <path d="M 36 32 Q 33 42 38 54 L 42 54 Q 40 44 40 36 Z" :fill="palette.hair" />
        <path d="M 64 32 Q 67 42 62 54 L 58 54 Q 60 44 60 36 Z" :fill="palette.hair" />

        <ellipse cx="44" cy="38" rx="1.4" ry="1.6" :fill="palette.eye" />
        <ellipse cx="56" cy="38" rx="1.4" ry="1.6" :fill="palette.eye" />
        <path d="M 41 33 Q 44 32 47 33" :stroke="palette.eye" stroke-width="0.8" fill="none" stroke-linecap="round" />
        <path d="M 53 33 Q 56 32 59 33" :stroke="palette.eye" stroke-width="0.8" fill="none" stroke-linecap="round" />
        <path d="M 50 39 L 49 44 L 51 44 Z" :fill="palette.faceShadow" opacity="0.5" />
        <path d="M 47 47 Q 50 48.5 53 47" :stroke="palette.eye" stroke-width="0.7" fill="none" stroke-linecap="round" />
        <g v-if="hasBeard">
          <path d="M 42 47 Q 50 58 58 47 L 56 50 Q 50 56 44 50 Z" :fill="palette.hair" />
        </g>

        <g v-html="headgear"></g>
        <g v-html="tool"></g>
      </g>

      <g>
        <circle cx="20" cy="80" r="10" :fill="palette.sealBg" :stroke="palette.sealStroke" stroke-width="1.2" />
        <text x="20" y="83.5" text-anchor="middle" font-size="9" :fill="palette.sealText" font-weight="bold" font-family="'STKaiti','KaiTi',serif">{{ sealLetter }}</text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  cardId: string
  subject?: string
  accent?: string
  size?: number
}>()

const portraitId = computed(() => props.cardId)
const imgError = ref(false)
const imgLoaded = ref(false)

// 真实图片路径（部署在 /public/generals/）
const imgPath = computed(() => `/generals/${props.cardId}.jpg`)

function onImgLoad() { imgLoaded.value = true; imgError.value = false }
function onImgError() { imgError.value = true; imgLoaded.value = false }

function hslTone(hex: string, shift = 0) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || '#2d5a4f')
  if (!m) return { r: 45, g: 90, b: 79 }
  const n = parseInt(m[1], 16)
  const r = ((n >> 16) & 255) + shift
  const g = ((n >> 8) & 255) + shift
  const b = (n & 255) + shift
  return { r: Math.min(255, Math.max(0, r)), g: Math.min(255, Math.max(0, g)), b: Math.min(255, Math.max(0, b)) }
}
function rgb({ r, g, b }, a = 1) { return `rgba(${r},${g},${b},${a})` }
function mix(hex: string, target: string, ratio: number) {
  const a = hslTone(hex)
  const b = /^#?([0-9a-f]{6})$/i.exec(target)
  if (!b) return hex
  const n = parseInt(b[1], 16)
  const t = { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
  return rgb({
    r: Math.round(a.r * (1 - ratio) + t.r * ratio),
    g: Math.round(a.g * (1 - ratio) + t.g * ratio),
    b: Math.round(a.b * (1 - ratio) + t.b * ratio),
  })
}

const accent = computed(() => props.accent || '#2d5a4f')

const palette = computed(() => {
  const a = accent.value
  return {
    bgInner: mix(a, '#fff8e1', 0.65),
    bgOuter: mix(a, '#3e2723', 0.7),
    cloakTop: mix(a, '#000', 0.1),
    cloakBot: mix(a, '#000', 0.55),
    collar: mix(a, '#fff', 0.85),
    belt: mix(a, '#000', 0.7),
    buckle: mix(a, '#ffd700', 0.8),
    face: '#f4d8b3',
    faceShadow: '#e0bd8f',
    neck: '#e8c99a',
    hair: '#1a1a1a',
    eye: '#1a1a1a',
    mountain: mix(a, '#000', 0.35),
    mountain2: mix(a, '#000', 0.15),
    sea: mix(a, '#000', 0.25),
    field: mix(a, '#fff', 0.4),
    ground: mix(a, '#000', 0.5),
    furrow: mix(a, '#000', 0.3),
    sealBg: '#fdf6e3',
    sealStroke: '#8d5524',
    sealText: '#8d5524',
  }
})

const scenery = computed(() => {
  switch (props.cardId) {
    case 'G1_xuxiake': return 'mountain'
    case 'G2_shenkuo': return 'field'
    case 'G3_zuchongzhi': return 'none'
    case 'G4_lishizhen': return 'field'
    case 'G5_mozi': return 'none'
    case 'G6_songyingxing': return 'none'
    case 'G7_xuguangqi': return 'sea'
    default: return 'none'
  }
})

const hasBeard = computed(() => ['G1_xuxiake', 'G2_shenkuo', 'G3_zuchongzhi', 'G5_mozi', 'G6_songyingxing', 'G7_xuguangqi'].includes(props.cardId))

const sealLetter = computed(() => {
  switch (props.cardId) {
    case 'G1_xuxiake': return '地'
    case 'G2_shenkuo': return '史'
    case 'G3_zuchongzhi': return '数'
    case 'G4_lishizhen': return '生'
    case 'G5_mozi': return '理'
    case 'G6_songyingxing': return '工'
    case 'G7_xuguangqi': return '通'
    default: return '学'
  }
})

const headgear = computed(() => {
  const cx = 50, cy = 38
  switch (props.cardId) {
    case 'G1_xuxiake': return `<path d="M ${cx - 18} ${cy - 14} Q ${cx} ${cy - 24}, ${cx + 18} ${cy - 14} L ${cx + 22} ${cy - 6} Q ${cx} ${cy + 2}, ${cx - 22} ${cy - 6} Z" fill="${palette.value.belt}" /><rect x="${cx - 16}" y="${cy - 16}" width="32" height="2.5" fill="${palette.value.buckle}" /><circle cx="${cx}" cy="${cy - 22}" r="1.8" fill="${palette.value.buckle}" />`
    case 'G2_shenkuo': return `<path d="M ${cx - 16} ${cy - 10} L ${cx - 16} ${cy - 24} L ${cx + 16} ${cy - 24} L ${cx + 16} ${cy - 10} Z" fill="#1a1a1a" /><rect x="${cx - 20}" y="${cy - 12}" width="40" height="3" fill="#0d0d0d" /><rect x="${cx - 22}" y="${cy - 22}" width="6" height="2" fill="#1a1a1a" /><rect x="${cx + 16}" y="${cy - 22}" width="6" height="2" fill="#1a1a1a" /><circle cx="${cx}" cy="${cy - 28}" r="2.2" fill="#c0392b" />`
    case 'G3_zuchongzhi': return `<path d="M ${cx - 14} ${cy - 14} Q ${cx} ${cy - 26}, ${cx + 14} ${cy - 14} L ${cx + 12} ${cy - 4} L ${cx - 12} ${cy - 4} Z" fill="#2c3e50" /><rect x="${cx - 16}" y="${cy - 12}" width="32" height="2" fill="#1a1a1a" />`
    case 'G4_lishizhen': return `<path d="M ${cx - 20} ${cy - 6} Q ${cx} ${cy - 26}, ${cx + 20} ${cy - 6} Z" fill="#a0522d" /><line x1="${cx - 18}" y1="${cy - 8}" x2="${cx + 18}" y2="${cy - 8}" stroke="#5d3a1a" stroke-width="0.5" /><line x1="${cx - 14}" y1="${cy - 14}" x2="${cx + 14}" y2="${cy - 14}" stroke="#5d3a1a" stroke-width="0.5" /><line x1="${cx - 8}" y1="${cy - 20}" x2="${cx + 8}" y2="${cy - 20}" stroke="#5d3a1a" stroke-width="0.5" /><line x1="${cx - 20}" y1="${cy - 6}" x2="${cx + 20}" y2="${cy - 6}" stroke="#3e2723" stroke-width="0.8" />`
    case 'G5_mozi': return `<rect x="${cx - 16}" y="${cy - 14}" width="32" height="5" fill="#5d4037" /><circle cx="${cx - 14}" cy="${cy - 11.5}" r="1.6" fill="#3e2723" /><circle cx="${cx + 14}" cy="${cy - 11.5}" r="1.6" fill="#3e2723" /><path d="M ${cx - 8} ${cy - 14} Q ${cx} ${cy - 22}, ${cx + 8} ${cy - 14} L ${cx + 6} ${cy - 14} Z" fill="#1a1a1a" />`
    case 'G6_songyingxing': return `<rect x="${cx - 15}" y="${cy - 14}" width="30" height="10" fill="#37474f" /><rect x="${cx - 17}" y="${cy - 6}" width="34" height="3" fill="#263238" /><line x1="${cx - 8}" y1="${cy - 14}" x2="${cx - 8}" y2="${cy - 6}" stroke="#263238" stroke-width="0.5" /><line x1="${cx + 8}" y1="${cy - 14}" x2="${cx + 8}" y2="${cy - 6}" stroke="#263238" stroke-width="0.5" />`
    case 'G7_xuguangqi': return `<path d="M ${cx - 12} ${cy - 14} L ${cx - 12} ${cy - 24} L ${cx + 12} ${cy - 24} L ${cx + 12} ${cy - 14} Z" fill="#1a237e" /><rect x="${cx - 14}" y="${cy - 14}" width="28" height="3" fill="#0d1b5e" /><rect x="${cx - 3}" y="${cy - 30}" width="6" height="8" fill="#0d1b5e" /><circle cx="${cx}" cy="${cy - 32}" r="2" fill="#ffd700" />`
    default: return ''
  }
})

const tool = computed(() => {
  const cx = 50, cy = 38
  switch (props.cardId) {
    case 'G1_xuxiake': return `<circle cx="${cx - 20}" cy="${cy + 18}" r="5" fill="none" stroke="#1a1a1a" stroke-width="1.5" /><circle cx="${cx - 20}" cy="${cy + 18}" r="2.5" fill="${palette.value.cloakBot}" opacity="0.6" /><line x1="${cx + 22}" y1="${cy + 14}" x2="${cx + 28}" y2="${cy + 50}" stroke="#5d3a1a" stroke-width="1.8" stroke-linecap="round" />`
    case 'G2_shenkuo': return `<rect x="${cx - 22}" y="${cy + 12}" width="44" height="10" rx="1" fill="#fdf6e3" stroke="#5d3a1a" stroke-width="0.8" /><line x1="${cx - 18}" y1="${cy + 14}" x2="${cx + 18}" y2="${cy + 14}" stroke="#5d3a1a" stroke-width="0.4" stroke-dasharray="2 1" /><line x1="${cx - 18}" y1="${cy + 17}" x2="${cx + 18}" y2="${cy + 17}" stroke="#5d3a1a" stroke-width="0.4" stroke-dasharray="2 1" /><line x1="${cx - 18}" y1="${cy + 20}" x2="${cx + 18}" y2="${cy + 20}" stroke="#5d3a1a" stroke-width="0.4" stroke-dasharray="2 1" />`
    case 'G3_zuchongzhi': return `<g><rect x="${cx - 22}" y="${cy + 18}" width="2" height="14" fill="#5d3a1a" transform="rotate(15 ${cx - 21} ${cy + 25})" /><rect x="${cx - 16}" y="${cy + 16}" width="2" height="14" fill="#5d3a1a" transform="rotate(-15 ${cx - 15} ${cy + 23})" /><rect x="${cx + 16}" y="${cy + 16}" width="2" height="14" fill="#5d3a1a" transform="rotate(15 ${cx + 17} ${cy + 23})" /><rect x="${cx + 22}" y="${cy + 18}" width="2" height="14" fill="#5d3a1a" transform="rotate(-15 ${cx + 23} ${cy + 25})" /><text x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="11" fill="#8d5524" font-family="'STKaiti','KaiTi',serif" font-weight="bold">π</text></g>`
    case 'G4_lishizhen': return `<g><line x1="${cx + 22}" y1="${cy + 14}" x2="${cx + 30}" y2="${cy + 38}" stroke="#2d5016" stroke-width="1.5" /><ellipse cx="${cx + 26}" cy="${cy + 22}" rx="3" ry="1.4" fill="#4a7c59" transform="rotate(45 ${cx + 26} ${cy + 22})" /><ellipse cx="${cx + 28}" cy="${cy + 30}" rx="3" ry="1.4" fill="#67c23a" transform="rotate(45 ${cx + 28} ${cy + 30})" /><line x1="${cx - 22}" y1="${cy + 14}" x2="${cx - 30}" y2="${cy + 38}" stroke="#2d5016" stroke-width="1.5" /><ellipse cx="${cx - 26}" cy="${cy + 22}" rx="3" ry="1.4" fill="#4a7c59" transform="rotate(-45 ${cx - 26} ${cy + 22})" /><ellipse cx="${cx - 28}" cy="${cy + 30}" rx="3" ry="1.4" fill="#67c23a" transform="rotate(-45 ${cx - 28} ${cy + 30})" /></g>`
    case 'G5_mozi': return `<g><path d="M ${cx - 26} ${cy + 18} L ${cx - 18} ${cy + 18} A 7 7 0 0 1 ${cx - 11} ${cy + 25} L ${cx - 11} ${cy + 27} L ${cx - 26} ${cy + 27} Z" fill="none" stroke="#5d3a1a" stroke-width="1.2" /><circle cx="${cx - 18}" cy="${cy + 18}" r="1" fill="#5d3a1a" /><line x1="${cx + 18}" y1="${cy + 16}" x2="${cx + 30}" y2="${cy + 32}" stroke="#5d3a1a" stroke-width="1.4" /><line x1="${cx + 18}" y1="${cy + 32}" x2="${cx + 30}" y2="${cy + 16}" stroke="#5d3a1a" stroke-width="1.4" /></g>`
    case 'G6_songyingxing': return `<g><circle cx="${cx - 22}" cy="${cy + 22}" r="5" fill="none" stroke="#5d3a1a" stroke-width="1.2" /><line x1="${cx - 22}" y1="${cy + 27}" x2="${cx + 8}" y2="${cy + 40}" stroke="#5d3a1a" stroke-width="1.3" /><line x1="${cx + 16}" y1="${cy + 14}" x2="${cx + 30}" y2="${cy + 14}" stroke="#5d3a1a" stroke-width="1.3" /><line x1="${cx + 16}" y1="${cy + 14}" x2="${cx + 16}" y2="${cy + 26}" stroke="#5d3a1a" stroke-width="1.3" /><line x1="${cx + 16}" y1="${cy + 26}" x2="${cx + 30}" y2="${cy + 26}" stroke="#5d3a1a" stroke-width="1.3" /></g>`
    case 'G7_xuguangqi': return `<g><rect x="${cx - 26}" y="${cy + 14}" width="52" height="12" rx="1" fill="#fdf6e3" stroke="#5d3a1a" stroke-width="0.8" /><line x1="${cx - 22}" y1="${cy + 18}" x2="${cx + 22}" y2="${cy + 18}" stroke="#5d3a1a" stroke-width="0.3" stroke-dasharray="2 1.5" /><line x1="${cx - 22}" y1="${cy + 22}" x2="${cx + 22}" y2="${cy + 22}" stroke="#5d3a1a" stroke-width="0.3" stroke-dasharray="2 1.5" /><circle cx="${cx - 12}" cy="${cy + 21}" r="1.3" fill="#c0392b" /><circle cx="${cx + 6}" cy="${cy + 24}" r="1.3" fill="#c0392b" /><circle cx="${cx + 16}" cy="${cy + 18}" r="1.3" fill="#c0392b" /></g>`
    default: return ''
  }
})
</script>

<style scoped>
.portrait-wrap {
  width: 100%;
  height: 100%;
  position: relative;
  border-radius: 50%;
  overflow: hidden;
  background: #fff8e1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.portrait-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 20%;
  display: block;
  opacity: 0;
  transition: opacity 0.3s ease;
}
.portrait-img.is-loaded {
  opacity: 1;
}
.general-portrait {
  width: 100%;
  height: 100%;
  display: block;
}
</style>