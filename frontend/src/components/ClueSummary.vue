<template>
  <div class="clue-summary">
    <h3 class="section-title">
      💡 线索合计
      <span class="progress-num">{{ totalClues }} / {{ maxClues }} 条</span>
    </h3>

    <!-- 学科覆盖柱状图 -->
    <div class="subject-coverage">
      <div class="coverage-title">📊 学科覆盖：</div>
      <div
        v-for="cat in categories"
        :key="cat.name"
        class="coverage-row"
      >
        <span class="cat-name">{{ cat.name }}</span>
        <div class="cat-bar">
          <div
            class="cat-fill"
            :style="{
              width: cat.total > 0 ? (cat.used / cat.total * 100) + '%' : '0%',
              background: cat.color
            }"
          ></div>
        </div>
        <span class="cat-count">{{ cat.used }}/{{ cat.total }}</span>
      </div>
    </div>

    <!-- 合技建议 -->
    <div v-if="nextComboHint" class="combo-hint" @click="$emit('open-combo')" role="button">
      <div class="hint-title">⚡ 下一步建议：</div>
      <div class="hint-content">{{ nextComboHint }}</div>
      <div class="hint-cta">点击可跳转合技选择 →</div>
    </div>

    <!-- 完整体状态 -->
    <div v-if="unlockedLayers.length > 0" class="unlocked-section">
      <div class="hint-title">✅ 已解锁：</div>
      <div class="unlocked-tags">
        <el-tag
          v-for="k in unlockedLayers"
          :key="k"
          type="success"
          size="small"
          effect="dark"
          round
        >
          {{ layerName(k) }}
        </el-tag>
      </div>
    </div>

    <!-- 全部线索收齐，但层未解锁时的提示 -->
    <div
      v-if="totalClues >= maxClues * 0.7 && unlockedLayers.length < 4"
      class="urgent-hint"
    >
      🔔 线索已收集 <b>{{ Math.round(totalClues / maxClues * 100) }}%</b>，
      尝试把同主题的两张武将卡合技解锁完整层！
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Card {
  id: string
  name: string
  badge_icon?: string
  category?: string
  combo_partner?: string
  combo_unlock_layer?: number
  exam_tags?: string[]
  max_use?: number
}

const props = defineProps<{
  cards: Card[]
  cardUsage: Record<string, number>
  unlockedLayers: string[]
  layers?: Record<string, any>
}>()
defineEmits<{ (e: 'open-combo'): void }>()

const maxClues = computed(() =>
  props.cards.reduce((sum, c) => sum + (c.max_use || 2), 0)
)
const totalClues = computed(() =>
  Object.values(props.cardUsage).reduce((sum: number, n) => sum + (n as number), 0)
)

// 学科分类聚合
const categories = computed(() => {
  const map = new Map<string, { name: string; used: number; total: number; color: string }>()
  for (const card of props.cards) {
    const cat = card.category || '其他'
    if (!map.has(cat)) {
      map.set(cat, {
        name: cat,
        used: 0,
        total: 0,
        color: pickColor(cat),
      })
    }
    const e = map.get(cat)!
    e.total += card.max_use || 2
    e.used += props.cardUsage[card.id] || 0
  }
  return Array.from(map.values())
})

function pickColor(cat: string): string {
  if (cat.includes('物质')) return 'linear-gradient(90deg, #67c23a, #85ce61)'
  if (cat.includes('环境')) return 'linear-gradient(90deg, #e6a23c, #f0b75e)'
  if (cat.includes('力学') || cat.includes('物理')) return 'linear-gradient(90deg, #409eff, #66b1ff)'
  if (cat.includes('综合')) return 'linear-gradient(90deg, #f56c6c, #fab6b6)'
  return 'linear-gradient(90deg, #909399, #b1b3b8)'
}

const nextComboHint = computed(() => {
  // 找下一个可合技的配对
  for (const card of props.cards) {
    if (!card.combo_partner) continue
    const partner = props.cards.find(c => c.id === card.combo_partner)
    if (!partner) continue

    const usedA = props.cardUsage[card.id] || 0
    const usedB = props.cardUsage[partner.id] || 0
    const targetLayer = card.combo_unlock_layer ?? 0
    const layerKey = layerIdxToKey(targetLayer)

    // 已经解锁的不提示
    if (props.unlockedLayers.includes(layerKey)) continue

    // 两张卡都至少用过一次才有意义
    if (usedA >= 1 && usedB >= 1) {
      return `「${card.badge_icon || ''}${card.name}」 + 「${partner.badge_icon || ''}${partner.name}」可合技解锁${layerName(layerKey)}`
    }
  }
  // 终极层
  const g7 = props.cards.find(c => c.id === 'G7_xuguangqi')
  if (g7 && !props.unlockedLayers.includes('ultimate')) {
    const g7Used = props.cardUsage['G7_xuguangqi'] || 0
    if (g7Used >= 1) {
      const anyOtherUsed = props.cards.some(c =>
        c.id !== 'G7_xuguangqi' && (props.cardUsage[c.id] || 0) >= 1
      )
      if (anyOtherUsed && props.unlockedLayers.includes('microscopic')) {
        return `「🌐 徐光启」+ 任意其他武将可合技解锁终极层`
      }
    }
  }
  return null
})

function layerIdxToKey(idx: number): string {
  return ['phenomenon', 'condition', 'microscopic', 'ultimate'][idx - 1] || 'phenomenon'
}

function layerName(key: string): string {
  const map: Record<string, string> = {
    phenomenon: '现象层',
    condition: '条件层',
    microscopic: '微观层',
    ultimate: '终极层',
  }
  return map[key] || key
}
</script>

<style scoped>
.clue-summary {
  padding: 12px 14px;
  background: linear-gradient(135deg, #fff8e1 0%, #fff3d6 100%);
  border-radius: 8px;
  border: 1px solid rgba(212, 165, 116, 0.3);
}
.section-title {
  margin: 0 0 10px;
  font-size: 14px;
  color: #5d4037;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.progress-num {
  font-size: 11px;
  color: #8d6e63;
  font-weight: normal;
  background: rgba(255, 255, 255, 0.7);
  padding: 1px 8px;
  border-radius: 10px;
}
.subject-coverage { margin-bottom: 10px; }
.coverage-title {
  font-size: 12px;
  color: #8d6e63;
  margin-bottom: 6px;
}
.coverage-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 11px;
}
.cat-name {
  width: 80px;
  color: #5d4037;
  font-weight: 500;
  flex-shrink: 0;
}
.cat-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 4px;
  overflow: hidden;
}
.cat-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s;
}
.cat-count {
  width: 50px;
  text-align: right;
  color: #8d6e63;
  font-size: 10px;
}
.combo-hint {
  background: linear-gradient(135deg, #fff7e6, #ffe7b3);
  border: 1px solid #ffc069;
  border-radius: 6px;
  padding: 8px 10px;
  margin-top: 8px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.combo-hint:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 192, 105, 0.4);
}
.hint-cta {
  font-size: 11px;
  color: #e6a23c;
  margin-top: 4px;
  font-weight: bold;
  text-align: right;
}
.hint-title {
  font-size: 12px;
  font-weight: bold;
  color: #874d00;
  margin-bottom: 4px;
}
.hint-content {
  font-size: 12px;
  color: #5d4037;
  line-height: 1.5;
}
.unlocked-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #d4a574;
}
.unlocked-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.urgent-hint {
  margin-top: 8px;
  padding: 8px 10px;
  background: linear-gradient(135deg, #fef0f0, #fde2e2);
  border: 1px solid #f56c6c;
  border-radius: 6px;
  font-size: 12px;
  color: #c45656;
  line-height: 1.5;
}
</style>