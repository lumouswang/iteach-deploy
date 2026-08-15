<template>
  <!-- 全局音效开关 + BGM 控制 -->
  <div class="global-sound-bar" :class="{ collapsed }">
    <el-button-group>
      <el-tooltip content="背景音乐（汤探局氛围循环）" placement="bottom">
        <el-button
          :type="sound.bgmPlaying.value ? 'success' : 'default'"
          size="small"
          @click="onToggleBgm"
          circle
        >
          {{ sound.bgmPlaying.value ? '�' : '🔇' }}
        </el-button>
      </el-tooltip>
      <el-tooltip content="静音切换" placement="bottom">
        <el-button
          :type="sound.enabled.value ? 'primary' : 'info'"
          size="small"
          @click="onToggleSound"
          circle
        >
          {{ sound.enabled.value ? '🔊' : '�' }}
        </el-button>
      </el-tooltip>
      <el-tooltip content="折叠" placement="bottom">
        <el-button size="small" @click="collapsed = !collapsed" circle plain>
          {{ collapsed ? '◀' : '▶' }}
        </el-button>
      </el-tooltip>
    </el-button-group>
  </div>

  <router-view />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSound } from './composables/useSound'

const sound = useSound()
const collapsed = ref(false)

function onToggleBgm() {
  // 第一次切换 BGM 时确保 AudioContext 已激活
  sound.test()
  sound.bgm.toggle()
}

function onToggleSound() {
  sound.toggle()
}

onMounted(() => {
  // 不在挂载时自动播放 BGM（需要用户交互）
  // 用户首次点击任意按钮即可触发音效 + BGM
})
</script>

<style scoped>
.global-sound-bar {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 9999;
  background: rgba(255, 255, 255, 0.95);
  padding: 6px 8px;
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(64, 158, 255, 0.2);
  transition: all 0.3s;
}
.global-sound-bar.collapsed {
  padding: 4px;
}
.global-sound-bar :deep(.el-button) {
  margin: 0 2px;
}
</style>
