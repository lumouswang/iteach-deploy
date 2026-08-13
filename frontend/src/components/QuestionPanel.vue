<template>
  <div class="question-panel" :class="{ disabled }">
    <h3 class="section-title">💬 海龟汤定向提问（剩余 {{ remaining }}/{{ total }}）</h3>

    <div v-if="disabled" class="phase-locked-tip">
      <el-alert
        :title="phase === 'card_play' ? '已进入出牌阶段' : '阶段锁定中'"
        :type="phase === 'card_play' ? 'success' : 'info'"
        :closable="false"
        show-icon
      >
        <template #default>
          <span v-if="phase === 'card_play'">请在右侧选取武将卡出牌，使用后能揭开线索。还要记得让两张不同武将合技解锁下一层。</span>
          <span v-else-if="phase === 'intro'">当前为「开局前置」阶段，请阅读汤底后点击底部“开始提问”切换到提问阶段。</span>
          <span v-else>当前为「{{ phaseLabel }}」阶段，未开放提问。</span>
        </template>
      </el-alert>
    </div>

    <div v-show="!disabled" class="categories">
      <el-radio-group v-model="selectedCategory" @change="filterByCategory">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="物质类">物质类</el-radio-button>
        <el-radio-button value="环境变量类">环境变量类</el-radio-button>
        <el-radio-button value="力学系统类">力学系统类</el-radio-button>
      </el-radio-group>
    </div>

    <div v-show="!disabled" class="question-list">
      <div
        v-for="q in filteredQuestions"
        :key="q.id"
        class="question-item"
        :class="{ disabled }"
        @click="onClick(q.id)"
      >
        <el-tag size="small" :type="categoryTag(q.category)">{{ q.category }}</el-tag>
        <span class="question-text">{{ q.text }}</span>
        <span class="question-point">{{ q.knowledge_point }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  questions: any[]
  remaining: number
  total: number
  phase?: string
}>()
const emit = defineEmits<{ (e: 'ask', qid: string): void }>()

const PHASE_LABELS: Record<string, string> = {
  lobby: '等待',
  intro: '开局前置',
  questioning: '海龟汤提问',
  card_play: '出牌 / 合技',
  reveal: '终极揭晓',
  debrief: '复盘',
  extend: '拓展',
  end: '结束',
}

const disabled = computed(() => {
  // 仅 questioning 阶段可提问；intro/lobby/card_play 都被锁
  const p = props.phase
  return p != null && p !== 'questioning'
})
const phaseLabel = computed(() => PHASE_LABELS[props.phase ?? ''] || (props.phase ?? '当前'))

const selectedCategory = ref('all')

const filteredQuestions = computed(() => {
  if (selectedCategory.value === 'all') return props.questions
  return props.questions.filter(q => q.category === selectedCategory.value)
})

function filterByCategory() {}
function onClick(qid: string) {
  if (!disabled.value) emit('ask', qid)
}
function categoryTag(cat: string): 'success' | 'warning' | 'primary' {
  if (cat === '物质类') return 'success'
  if (cat === '环境变量类') return 'warning'
  return 'primary'
}
</script>

<style scoped>
.question-panel { padding: 12px 14px; }
.phase-locked-tip { margin: 0 0 10px; }
.section-title { margin: 0 0 10px; font-size: 16px; }
.categories { margin-bottom: 10px; }
.question-list {
  max-height: 460px;
  overflow-y: auto;
  padding-right: 4px;
}
.question-item {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.question-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}
.question-item.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
.question-item.disabled:hover {
  background: #fff;
  border-color: #ebeef5;
}
.question-text {
  flex: 1;
  font-size: 13px;
  color: #303133;
}
.question-point {
  font-size: 11px;
  color: #909399;
}
</style>
