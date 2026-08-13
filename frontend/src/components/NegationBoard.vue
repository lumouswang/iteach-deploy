<template>
  <div class="negation-board">
    <h3 class="section-title">❌ 否决板（错误猜想收集）</h3>
    <div v-if="negations.length === 0" class="empty-tip">
      暂无错误猜想。玩家目前判断尚可～
    </div>
    <div v-else>
      <div v-for="n in negations" :key="n.id" class="negation-item">
        <div class="negation-text">⨯ {{ n.text }}</div>
        <div class="negation-meta">
          <el-tag type="danger" size="small">错</el-tag>
          <span class="negation-point">{{ n.knowledge_point }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ negations: any[] }>()
</script>

<style scoped>
.negation-board { padding: 12px 14px; }
.section-title {
  margin: 0 0 10px;
  font-size: 16px;
  color: #f56c6c;
}
.empty-tip {
  text-align: center;
  color: #909399;
  padding: 14px 8px;
  font-size: 12px;
  background: #faf6ef;
  border-radius: 4px;
}
.negation-item {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
  padding: 6px 10px;
  margin-bottom: 6px;
  border-radius: 4px;
}
.negation-text {
  font-size: 12px;
  color: #303133;
  text-decoration: line-through;
  margin-bottom: 3px;
}
.negation-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 11px;
  color: #909399;
}
.negation-point { font-style: italic; }
</style>
