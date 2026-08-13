<template>
  <div class="layer-progress">
    <h3 class="section-title">
      🎯 汤底解锁进度
      <span class="progress-num">{{ unlockedLayers.length }} / {{ totalLayers }}</span>
    </h3>
    <el-alert
      v-if="unlockedLayers.length === 0"
      type="info"
      :closable="false"
      show-icon
      class="layer-hint"
    >
      <template #default>
        💡 <b>单卡出牌</b>只能拿 1 条线索；<b>选两张配对武将合技</b>才能解锁整层（点击底部「⚡ 选 2 张卡合技」按钮）。
      </template>
    </el-alert>
    <div class="layers">
      <div
        v-for="(layer, key) in layers"
        :key="key"
        class="layer-bar"
        :class="{ unlocked: unlockedLayers.includes(key as string), active: activeLayer === key, clickable: unlockedLayers.includes(key as string) }"
        @click="onLayerClick(key as string, layer)"
      >
        <span class="layer-icon">{{ layer.icon }}</span>
        <span class="layer-name">{{ layer.name }}</span>
        <span class="layer-status">
          <template v-if="unlockedLayers.includes(key as string)">
            <el-icon class="learn-icon"><Reading /></el-icon>
          </template>
          <template v-else>🔒</template>
        </span>
      </div>
    </div>
    <el-tooltip
      v-if="unlockedLayers.length > 0"
      content="点击已解锁的层，可查看该层的完整知识点讲解"
      placement="bottom"
    >
      <div class="hint-line">📖 点击已解锁的层 → 查看「{{ unlockedLayers.length }}层」合技知识点</div>
    </el-tooltip>
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: progressPercent + '%' }"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Reading } from '@element-plus/icons-vue'

const props = defineProps<{
  layers: Record<string, any>
  unlockedLayers: string[]
  activeLayer?: string
}>()

const router = useRouter()

const totalLayers = computed(() => Math.max(Object.keys(props.layers || {}).length, 1))
const progressPercent = computed(() => {
  const total = totalLayers.value
  return Math.round((props.unlockedLayers.length / total) * 100)
})

function onLayerClick(key: string, layer: any) {
  if (!props.unlockedLayers.includes(key)) return
  // Navigate to the learn page for this combo layer
  router.push(`/learn/${encodeURIComponent(key)}`)
}
</script>

<style scoped>
.layer-progress { padding: 12px 14px; }
.section-title {
  margin: 0 0 10px;
  font-size: 16px;
  color: #5d4037;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.progress-num {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 10px;
}
.layer-hint { margin-bottom: 8px; padding: 6px 10px; font-size: 12px; }
.layers { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.layer-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f5f7fa;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  font-size: 13px;
  transition: all 0.3s;
}
.layer-bar.unlocked {
  background: linear-gradient(90deg, #f0f9eb 0%, #e1f3d8 100%);
  border-color: #67c23a;
  border-style: solid;
}
.layer-bar.active {
  border-color: #e6a23c;
  background: linear-gradient(90deg, #fdf6ec 0%, #faecd8 100%);
}
.layer-bar.clickable {
  cursor: pointer;
}
.layer-bar.clickable:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}
.layer-icon { font-size: 18px; }
.layer-name { flex: 1; font-weight: 600; color: #303133; }
.layer-status { font-size: 14px; display: flex; align-items: center; }
.learn-icon {
  color: #67c23a;
  font-size: 16px;
  transition: transform 0.2s;
}
.layer-bar.clickable:hover .learn-icon {
  transform: scale(1.2);
  color: #409eff;
}
.hint-line {
  font-size: 11px;
  color: #909399;
  margin-bottom: 8px;
  text-align: center;
  font-style: italic;
}
.progress-bar {
  position: relative;
  height: 8px;
  background: #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #409eff, #e6a23c, #f56c6c);
  transition: width 0.6s;
  border-radius: 4px;
}
</style>
