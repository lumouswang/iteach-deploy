<template>
  <div class="clue-area">
    <h3 class="section-title">💡 已收集线索（{{ clues.length }} 条）</h3>
    <div v-if="clues.length === 0" class="empty-tip">
      使用武将卡可以获取卡片线索
    </div>
    <div v-else>
      <div
        v-for="c in clues"
        :key="c.clue_id"
        class="clue-item"
        :class="`layer-${c.layer || 'none'}`"
      >
        <div class="clue-label">{{ c.label }}</div>
        <div v-if="c.content" class="clue-content">{{ c.content }}</div>

        <!-- 来源武将可点击行 -->
        <button
          v-if="cardOf(c)"
          class="source-card"
          :style="{ '--accent': colorOf(c.card_id) }"
          @click="$emit('card-focus', c.card_id)"
          :title="`点击跳到【${cardOf(c)?.name}】武将卡`"
        >
          <span class="sc-icon">{{ cardOf(c)?.badge_icon }}</span>
          <span class="sc-name">{{ cardOf(c)?.name }}</span>
          <span class="sc-view">{{ shortView(c.card_id) }}</span>
          <span class="sc-arrow">↓ 跳到卡</span>
        </button>

        <div class="clue-card">
          <span class="clue-point" v-if="c.knowledge_point">📚 {{ c.knowledge_point }}</span>
          <el-tag v-if="c.layer" size="small" type="success">
            ✔ 已归属 → {{ layerName(c.layer) }}
          </el-tag>
        </div>

        <div v-if="c.knowledge_point" class="clue-actions">
          <el-button
            type="primary"
            size="small"
            round
            @click="openLearn(c.knowledge_point!)"
          >
            📖 深入学习此知识点
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

interface Clue {
  clue_id: string
  card_id: string
  label: string
  content?: string
  knowledge_point?: string
  layer?: string | null
  player_id?: string
}

const props = defineProps<{
  clues: Clue[]
  cards: any[]
}>()

defineEmits<{
  (e: 'card-focus', cardId: string): void
}>()

const router = useRouter()

const SUBJECT_COLORS: Record<string, string> = {
  '地理':           '#2d5a4f',
  '地理 + 历史':    '#6b4423',
  '数学 + 化学':    '#1e3a2c',
  '生物':           '#4a7c59',
  '物理':           '#1a2e5a',
  '数学':           '#5b2c5f',
  '综合':           '#8b5a1c',
}

function cardOf(c: Clue) {
  return props.cards.find(x => x.id === c.card_id)
}
function colorOf(cardId: string): string {
  const c = cardOf({ card_id: cardId } as Clue)
  if (!c) return '#5d4037'
  return SUBJECT_COLORS[c.subject] || '#5d4037'
}
function shortView(cardId: string): string {
  const c = cardOf({ card_id: cardId } as Clue)
  return c?.thinking_view || ''
}

const LAYER_NAMES: Record<string, string> = {
  phenomenon: '现象层',
  condition: '条件层',
  microscopic: '微观层',
  ultimate: '终极层',
}
function layerName(k: string) { return LAYER_NAMES[k] || k }

function openLearn(kp: string) {
  router.push(`/learn/${encodeURIComponent(kp)}`)
}
</script>

<style scoped>
.clue-area { padding: 12px 14px; }
.section-title {
  margin: 0 0 10px;
  font-size: 16px;
  color: #67c23a;
}
.empty-tip {
  text-align: center;
  color: #909399;
  padding: 14px 8px;
  font-size: 12px;
  background: #f0f9eb;
  border-radius: 4px;
}
.clue-item {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
  padding: 8px 10px;
  margin-bottom: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}
.clue-item:hover {
  background: #e1f3d8;
}
.clue-label {
  font-weight: bold;
  font-size: 13px;
  color: #303133;
  margin-bottom: 4px;
}
.clue-content {
  background: rgba(255,255,255,0.7);
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
  margin-bottom: 6px;
  max-height: 80px;
  overflow-y: auto;
}
.clue-card {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  align-items: center;
  font-size: 11px;
  margin-bottom: 4px;
}
.clue-point { color: #909399; font-style: italic; }

/* ===== 来源武将可点击卡 ===== */
.source-card {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 5px 8px;
  margin: 4px 0 6px;
  background: #fff;
  border: 1px solid var(--accent, #5d4037);
  border-left: 4px solid var(--accent, #5d4037);
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  text-align: left;
  transition: all 0.2s;
  color: #303133;
}
.source-card:hover {
  background: linear-gradient(135deg, #fff 0%, #faf6ef 100%);
  transform: translateX(2px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}
.sc-icon { font-size: 16px; }
.sc-name {
  font-weight: 700;
  color: var(--accent, #5d4037);
  font-family: 'STKaiti', 'KaiTi', serif;
  letter-spacing: 1px;
}
.sc-view {
  color: #909399;
  font-size: 11px;
  font-style: italic;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sc-arrow {
  font-size: 10px;
  color: var(--accent, #5d4037);
  background: rgba(0,0,0,0.04);
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  transition: all 0.2s;
}
.source-card:hover .sc-arrow {
  background: var(--accent, #5d4037);
  color: #fff;
}

.clue-actions {
  margin-top: 6px;
  display: flex;
  justify-content: flex-end;
}
.layer-condition { border-left-color: #409eff; background: #ecf5ff; }
.layer-condition:hover { background: #d9ecff; }
.layer-microscopic { border-left-color: #e6a23c; background: #fdf6ec; }
.layer-microscopic:hover { background: #faecd8; }
.layer-ultimate { border-left-color: #f56c6c; background: #fef0f0; }
.layer-ultimate:hover { background: #fde2e2; }
</style>
