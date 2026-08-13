<template>
  <div class="play-page">
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

    <header class="play-header">
      <div class="header-left">
        <h2>🧂 盐湖岸边的化石</h2>
        <el-tag :type="phaseTagType" effect="dark" size="small" class="phase-chip">{{ phaseLabel }}</el-tag>
      </div>
      <div class="header-right">
        <transition name="turn-fade">
          <div v-if="players.length >= 2" class="turn-indicator" :class="{ my: isMyTurn }">
            <span class="turn-icon">{{ isMyTurn ? '👉' : '⏳' }}</span>
            <span v-if="currentPlayer">轮到 <strong>{{ currentPlayer.user_name }}</strong> {{ isMyTurn ? '（你）' : '' }}</span>
          </div>
        </transition>
        <div class="room-id">房间：<code>{{ roomIdParam }}</code></div>
        <span class="ws-dot" :class="{ on: wsConnected }" :title="wsConnected ? '实时同步已连接' : '实时同步断开'">●</span>
        <el-button size="small" plain @click="goHome">返回首页</el-button>
      </div>
    </header>

    <!-- intro 阶段不需顶部提示，中栏的 hero 区已包含完整汤面 -->

    <div v-if="phase === 'reveal'" class="phase-hint">
      <el-alert
        title="阶段5：终极揭晓"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <div>全部 4 层汤底已解锁，点击下方查看完整汤面。进入复盘后会有全面复盘报告。</div>
        </template>
      </el-alert>
    </div>

    <div v-if="phase === 'debrief'" class="phase-hint">
      <el-alert
        title="阶段6：复盘阶段"
        type="info"
        description="你已进入复盘页，点击右下角进入或者返回首页进行下一轮。"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 通关挑战入近（4 层全解锁后高亮提示） -->
    <transition name="challenge-arise">
      <div v-if="allLayersUnlocked && !hasSeenChallengeBanner" class="phase-hint">
        <el-alert
          title="🎓 4 层全部解锁！准备好接受通关挑战了吗？"
          type="warning"
          :closable="true"
          show-icon
          @close="hasSeenChallengeBanner = true"
        >
          <template #default>
            <div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">
              <span>点击右下角 <strong>🎓 通关挑战</strong> 按钮，进入 6 题掌握程度检验。  </span>
              <el-button @click="goChallenge" type="warning" size="small" round>
                🚀 立即挑战
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>
    </transition>

    <div v-if="loading" class="loading-box">
      <el-alert title="加载中..." type="info" :closable="false" show-icon>
        正在拉取 7 张武将卡和 20 道提问，请稍候...
      </el-alert>
    </div>

    <div v-else-if="loadError" class="loading-box">
      <el-alert :title="loadError" type="error" :closable="false" show-icon>
        <template #default>
          <div>请检查后端是否在 <code>http://localhost:8000</code> 运行</div>
          <div v-if="loadError.includes('404') || loadError.includes('不存在')" style="margin-top:6px">
            该房间已被回收（后端重启 / 超时清理），请"返回首页"重开。
          </div>
          <el-button @click="loadAll" type="primary" size="small" style="margin-top:8px">🔄 重试</el-button>
          <el-button @click="goHome" size="small" style="margin-top:8px">返回首页</el-button>
        </template>
      </el-alert>
    </div>

    <div v-else class="play-grid" :class="`phase-${phase}`">
      <!-- 左栏 -->
      <aside class="play-col left">
        <layer-progress
          :layers="layers"
          :unlocked-layers="unlockedLayers"
          :active-layer="lastUnlockedLayer"
        />
        <clue-summary
          :cards="cards"
          :card-usage="cardUsage"
          :unlocked-layers="unlockedLayers"
          :layers="layers"
          @open-combo="openComboDialog"
        />
        <negation-board v-if="phase !== 'intro' || negationBoard.length > 0" :negations="negationBoard" />
      </aside>

      <!-- 中栏 -->
      <main class="play-col center">
        <!-- 汤面贴边卡：intro 全展开，其余阶段折叠，点击右上角可展开/收起，跨 phase 持续存在 -->
        <div v-if="scriptInfo && phase !== 'intro'" class="card-block tang-mian-compact">
          <div class="tm-head" @click="tangMianOpen = !tangMianOpen">
            <span class="tm-icon">📖</span>
            <span class="tm-title">汤面 · {{ scriptInfo.title }}</span>
            <el-tag size="small" type="warning">{{ scriptInfo.grade_level }}</el-tag>
            <el-tag size="small" type="success">提问 {{ scriptInfo.max_questions }} 次</el-tag>
            <button class="tm-toggle" :class="{ open: tangMianOpen }">
              {{ tangMianOpen ? '▲ 收起' : '▼ 展开' }}
            </button>
          </div>
          <pre class="tm-subtitle" v-if="tangMianOpen && scriptInfo.subtitle">{{ scriptInfo.subtitle }}</pre>
          <details v-if="tangMianOpen && scriptInfo.scene" class="tm-details">
            <summary>📜 4 层推演提示</summary>
            <pre class="tm-scene">{{ scriptInfo.scene }}</pre>
          </details>
          <details v-if="tangMianOpen && scriptInfo.knowledge_points_summary" class="tm-details">
            <summary>🎯 14 个高考考点预览</summary>
            <div class="tm-knowledge">{{ scriptInfo.knowledge_points_summary }}</div>
          </details>
        </div>

        <!-- intro 阶段：完整展示汤面作为中心焦点 -->
        <div v-if="phase === 'intro' && scriptInfo" class="card-block intro-hero">
          <div class="hero-head">
            <h3>📖 汤面 — {{ scriptInfo.title || '本局情境' }}</h3>
            <div class="hero-tags">
              <el-tag v-if="scriptInfo.category" size="small">{{ scriptInfo.category }}</el-tag>
              <el-tag v-if="scriptInfo.grade_level" type="warning" size="small">{{ scriptInfo.grade_level }}</el-tag>
              <el-tag v-if="scriptInfo.max_questions" type="success" size="small">提问 {{ scriptInfo.max_questions }} 次</el-tag>
            </div>
          </div>
          <pre v-if="scriptInfo.subtitle" class="hero-subtitle">{{ scriptInfo.subtitle }}</pre>
          <details v-if="scriptInfo.scene" class="hero-scene-wrap">
            <summary class="hero-info-toggle">📜 查看完整说明与汤底提示 (含 4 层推演要点)</summary>
            <pre class="hero-scene">{{ scriptInfo.scene }}</pre>
          </details>
          <details v-if="scriptInfo.knowledge_points_summary" class="hero-knowledge-wrap">
            <summary class="hero-info-toggle">🎯 查看考察的 14 个高考考点 (含学科分布)</summary>
            <div class="hero-knowledge">{{ scriptInfo.knowledge_points_summary }}</div>
          </details>
          <div class="hero-tip">
            💡 <strong>提示：</strong>先在底部点击「💬 开始提问」进入提问阶段。建议先用 1–2 次提问验证初始猜想，再用武将卡定向探查。
          </div>
        </div>

        <div v-if="phase !== 'intro'" class="card-block">
          <question-panel
            :questions="questions"
            :remaining="questionsRemaining"
            :total="scriptInfo?.max_questions || 9"
            :phase="phase"
            @ask="onAsk"
          />
        </div>

        <div class="card-block" v-if="questionsLog.length > 0">
          <h4>🗨 提问与回答历史</h4>
          <div v-for="q in questionsLog" :key="q.id" class="dialog-item">
            <div class="q-row">
              <el-tag size="small" :type="categoryTag(q.category)">{{ q.category }}</el-tag>
              <strong>Q：</strong> {{ q.text }}
            </div>
            <div class="a-row">
              <strong>A：</strong>
              <el-tag :type="answerTag(q.answer)" size="small">{{ q.answer }}</el-tag>
              <span class="hint">📚 {{ q.knowledge_point }}</span>
            </div>
          </div>
        </div>
      </main>

      <!-- 右栏 -->
      <aside class="play-col right">
        <clue-area :clues="cluesLog" :cards="cards" @card-focus="onFocusCard" />
      </aside>
    </div>

    <!-- 武将手牌：仅在出牌/揭晓阶段显示，提问阶段隐藏避免信息过载 -->
    <transition name="card-hand-rise">
      <div v-if="phase === 'card_play' || phase === 'reveal'" class="card-hand-stage" :class="{ 'is-reveal': phase === 'reveal' }">
        <!-- 📦 手牌收起时的「↪一键展开」留出口按钮【始终可点】 -->
        <transition name="card-hand-expand">
          <button
            v-if="cardHandCollapsed"
            class="card-hand-restore-btn"
            @click="cardHandCollapsed = false"
            title="点击重新展开武将手牌"
          >
            🎴 展开武将手牌 ▼
          </button>
        </transition>

        <transition name="card-hand-collapse">
          <div v-show="!cardHandCollapsed">
            <div class="stage-banner">
              <el-icon class="banner-icon"><MagicStick /></el-icon>
              <span v-if="phase === 'card_play'">🎴 武将手牌已开放 — 点击武将出牌，或选 2 张配对武将进行合技</span>
              <span v-else>🏆 终极层已揭晓 — 武将手牌供参考，不再影响你的查看</span>
              <span class="banner-sub">💡 配对关系见左上「🎯 汤底解锁进度」 · 点线索上的「↓ 跳到卡」定位武将</span>
            </div>
            <card-hand
              :cards="cards"
              :card-usage="cardUsage"
              :highlight-card-id="suggestedCardId"
              :flash-card-id="flashCardId"
              :card-bar-collapsed="cardHandCollapsed"
              @select-card="onSelectCard"
              @open-combo="openComboDialog"
              @toggle-collapse="cardHandCollapsed = !cardHandCollapsed"
            />
          </div>
        </transition>
      </div>
    </transition>

    <div class="footer-actions">
      <el-button
        v-if="phase === 'intro'"
        type="primary"
        size="large"
        @click="goPhase('questioning')"
      >
        💬 开始提问 →
      </el-button>
      <el-button
        v-if="phase === 'questioning'"
        :type="questionsRemaining <= 0 ? 'primary' : 'warning'"
        size="large"
        :disabled="questionsRemaining > 0"
        @click="goPhase('card_play')"
      >
        🃏 进入出牌（剩 {{ questionsRemaining }} 次提问可用）
      </el-button>
      <el-button
        v-if="phase !== 'reveal' && phase !== 'debrief' && phase !== 'extend' && unlockedLayers.includes('ultimate')"
        type="warning"
        size="large"
        @click="onReveal"
      >
        🎉 揭示汤底 →
      </el-button>
      <el-button
        v-if="phase === 'reveal'"
        type="primary"
        size="large"
        @click="onDebrief"
      >
        📊 进入复盘 →
      </el-button>
      <el-button
        v-if="phase === 'debrief'"
        size="large"
        @click="onExtend"
      >
        🌱 拓展知识 →
      </el-button>
      <el-button @click="goDebrief" :disabled="unlockedLayers.length === 0" plain>
        查看复盘报告 →
      </el-button>
      <el-button
        v-if="allLayersUnlocked"
        @click="goChallenge"
        type="warning"
        plain
        class="challenge-cta"
      >
        🎓 通关挑战 →
      </el-button>
      <el-button
        v-if="isDev"
        type="danger"
        plain
        size="small"
        @click="devResetCards"
        title="仅 dev 模式可见：清零所有武将卡使用计数"
      >
        🔄 重置武将卡 (dev)
      </el-button>
    </div>

    <!-- 出卡线索弹窗 -->
    <el-dialog v-model="cardDialog.visible" :title="cardDialog.title" width="500px">
      <div v-if="cardDialog.clue">
        <div class="clue-label">{{ cardDialog.clue.label }}</div>
        <p class="clue-content">{{ cardDialog.clue.content }}</p>
        <el-tag type="success">{{ cardDialog.clue.knowledge_point }}</el-tag>
      </div>
      <template #footer>
        <el-button
          v-if="cardDialog.clue?.knowledge_point"
          type="warning"
          @click="goLearnFromDialog"
        >
          📖 深入学习此知识点
        </el-button>
        <el-button type="primary" @click="cardDialog.visible = false">已了解</el-button>
      </template>
    </el-dialog>

    <!-- 合技选择弹窗 -->
    <el-dialog v-model="comboDialog.visible" title="⚡ 双将合技" width="760px">
      <p>请选 2 张武将卡组成合技。每张武将最多使用 2 次，配对的两位必须达到所属汤底层级的需求，才能开启该层的终极真相。</p>
      <!-- 未解锁的合技配方提示 -->
      <div class="combo-recipe-hint">
        <div class="recipe-title">💡 未解锁的合技配方：</div>
        <div
          v-for="r in allComboRecipes"
          :key="r.layerKey"
          class="recipe-item"
          :style="{ borderLeftColor: r.layerColor }"
        >
          <span class="recipe-icon">{{ r.layerIcon }}</span>
          <strong>{{ r.layerName }}</strong>
          <span class="recipe-name">（{{ r.comboName }}）</span>
          <span class="recipe-text">{{ r.hint }}</span>
        </div>
      </div>
      <!-- 选中一张后的提示 -->
      <transition name="combo-hint-fade">
        <div
          v-if="comboDialog.selected.length === 1"
          class="combo-selected-hint"
          :style="{ background: cardComboTargets(comboDialog.selected[0])[0]?.layerColor || '#67c23a' }"
        >
          <el-icon><Aim /></el-icon>
          <span v-if="cardComboTargets(comboDialog.selected[0]).length === 0">
            ⚠️ 这张卡暂无合技配方，请选择其他武将
          </span>
          <span v-else>
            ✓ 已选第一张，待选可解锁
            <strong v-for="(t, i) in cardComboTargets(comboDialog.selected[0])" :key="i">
              {{ i > 0 ? ' / ' : '' }}{{ t.layerIcon }} {{ t.layerName }}
            </strong>
            （候选武将已高亮 ✨）
          </span>
        </div>
      </transition>
      <!-- 已选两张后的确认提示 -->
      <transition name="combo-hint-fade">
        <div
          v-if="comboSelectionLayerHint()"
          class="combo-ready-hint"
          :style="{ background: comboSelectionLayerHint()!.color, borderColor: comboSelectionLayerHint()!.color }"
        >
          🎯 这对组合可解锁 <strong>{{ comboSelectionLayerHint()!.icon }} {{ comboSelectionLayerHint()!.name }}</strong>
        </div>
      </transition>
      <div class="combo-grid">
        <div
          v-for="card in cards"
          :key="card.id"
          class="combo-card"
          :class="{
            selected: comboDialog.selected.includes(card.id),
            disabled: !cardEligibleForCombo(card.id),
            'by-opponent': cardOwnedByOpponent(card.id),
            'can-pair': comboDialog.selected.length === 1 && isValidPairWithSelected(card.id) && !comboDialog.selected.includes(card.id)
          }"
          @click="toggleComboSelect(card.id)"
        >
          <div class="combo-card-icon">{{ card.badge_icon }}</div>
          <div class="combo-card-name">{{ card.name }}</div>
          <small>{{ cardUsage[card.id] || 0 }}/{{ card.max_use }}</small>
          <el-tag v-if="cardOwnedByOpponent(card.id)" size="small" type="primary" effect="plain">对手的</el-tag>
          <!-- 合技提示标签 -->
          <div v-if="comboDialog.selected.length === 0 && cardComboTargets(card.id).length > 0" class="combo-card-pair-hint">
            <span
              v-for="(t, i) in cardComboTargets(card.id)"
              :key="i"
              :style="{ background: t.layerColor }"
              class="pair-hint-dot"
              :title="'配对可解锁 ' + t.layerName"
            >{{ t.layerIcon }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="comboDialog.visible = false">取消</el-button>
        <el-button type="primary" :disabled="comboDialog.selected.length !== 2" @click="confirmCombo">
          触发合技
        </el-button>
      </template>
    </el-dialog>

    <!-- 解锁层揭示弹窗 -->
    <el-dialog v-model="revealDialog.visible" :title="revealDialog.title" width="600px">
      <pre class="reveal-text">{{ revealDialog.text }}</pre>
      <template #footer>
        <el-button type="primary" @click="revealDialog.visible = false">已了解</el-button>
      </template>
    </el-dialog>

    <!-- 阶段5：终极揭晓弹窗 -->
    <el-dialog v-model="finalRevealDialog.visible" :title="finalRevealDialog.title" width="720px">
      <div v-if="finalRevealDialog.layers" class="final-reveal">
        <div v-for="(layer, key) in finalRevealDialog.layers" :key="key" class="final-layer">
          <div class="final-layer-head">
            <span class="final-layer-icon">{{ layer.icon }}</span>
            <strong>{{ layer.name }}</strong>
          </div>
          <pre class="final-layer-text">{{ layer.reveal_text }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="finalRevealDialog.visible = false">关上</el-button>
        <el-button type="primary" @click="onDebrief">📊 去复盘 →</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

import { useFireworks } from '../composables/useFireworks'
import { useRoomStore } from '../stores/room'
import { useRoomWS } from '../ws/socket'
import LayerProgress from '../components/LayerProgress.vue'
import ClueSummary from '../components/ClueSummary.vue'
import NegationBoard from '../components/NegationBoard.vue'
import QuestionPanel from '../components/QuestionPanel.vue'
import ClueArea from '../components/ClueArea.vue'
import CardHand from '../components/CardHand.vue'
import { MagicStick, Aim } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isDev = import.meta.env.DEV

const roomIdParam = computed(() => route.params.roomId as string)
const store = useRoomStore()

// ============ P1 #7: WebSocket 实时同步 ============
const ws = useRoomWS(() => roomIdParam.value)
const wsConnected = ws.connected

ws.on(msg => {
  // 后端在每个动作后广播 state_update
  if (msg.action === 'state_update' && msg.state) {
    store.applyState(msg.state)
  }
})

onMounted(() => {
  ws.connect()
})
onUnmounted(() => {
  ws.close()
})

// ============ 派生 ============
const layers = ref<Record<string, any>>({})
const scriptInfo = ref<any>(null)
const playerId = computed(() => store.playerId)
const players = computed(() => store.players)
const turnPlayerId = computed(() => store.turnPlayerId)
const currentPlayer = computed(() => store.currentPlayer)
const isMyTurn = computed(() => store.isMyTurn)
const phase = computed(() => store.phase)
const questionsRemaining = computed(() => store.questionsRemaining)
const cardUsage = computed(() => store.cardUsage)
const unlockedLayers = computed(() => store.unlockedLayers)
const negationBoard = computed(() => store.negationBoard)
const questionsLog = computed(() => store.questionsLog)
const cluesLog = computed(() => store.cluesLog)
const cards = computed(() => store.cards)
const questions = computed(() => store.questions)

const loading = ref(true)
const loadError = ref('')
const suggestedCardId = ref<string>('')
const hasSeenChallengeBanner = ref(false)
// 汤面贴边卡默认收起，跨 phase 记住玩家偏好
const tangMianOpen = ref(localStorage.getItem('tangtanju.tangmian.open') === '1')
watch(tangMianOpen, v => localStorage.setItem('tangtanju.tangmian.open', v ? '1' : '0'))

// 线索页 → 武将卡跳转：点线索上的【↓ 跳到卡】，传入卡 id，这里负责传给 CardHand 闪烁
const flashCardId = ref('')
function onFocusCard(cardId: string) {
  flashCardId.value = cardId
  // 2.4s 后清空，避免动画永远保持高亮
  setTimeout(() => {
    if (flashCardId.value === cardId) flashCardId.value = ''
  }, 2400)
}

// 武将手牌默认状态：进入 reveal 阶段默认收起，手动点击可展开 / 收起（玩家偏好记忆）
const cardHandCollapsed = ref(localStorage.getItem('tangtanju.cardhand.collapsed') === '1')
watch(cardHandCollapsed, v => localStorage.setItem('tangtanju.cardhand.collapsed', v ? '1' : '0'))
watch(
  () => phase.value,
  p => {
    // 只有在 reveal 阶段首次进入才默认收起（玩家手动后可自由切换）
    if (p === 'reveal') cardHandCollapsed.value = true
  }
)

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
const phaseLabel = computed(() => PHASE_LABELS[phase.value] || phase.value)
const phaseTagType = computed<'success' | 'warning' | 'primary' | 'info' | 'danger'>(() => {
  if (phase.value === 'intro' || phase.value === 'questioning') return 'success'
  if (phase.value === 'card_play') return 'warning'
  if (phase.value === 'reveal') return 'danger'
  if (phase.value === 'debrief') return 'info'
  return 'primary'
})

const cardDialog = ref({ visible: false, title: '', clue: null as any })
const comboDialog = ref({ visible: false, selected: [] as string[] })
const revealDialog = ref({ visible: false, title: '', text: '' })
const finalRevealDialog = ref({ visible: false, title: '🎉 汤底全貌', layers: null as any })

const { particles, shapePath, burst, celebrate } = useFireworks()

const lastUnlockedLayer = computed(() => unlockedLayers.value[unlockedLayers.value.length - 1])

// ============ 通关挑战触发逻辑 ============
// 4 层全部解锁（现象+条件+微观+终极）才显示通关挑战入口
const allLayersUnlocked = computed(() => {
  const required = ['phenomenon', 'condition', 'microscopic', 'ultimate']
  return required.every(k => unlockedLayers.value.includes(k))
})

function goChallenge() {
  if (!allLayersUnlocked.value) {
    ElMessage.warning('4 个层全部解锁后才能挑战（还差 ' + (4 - unlockedLayers.value.length) + ' 层）')
    return
  }
  router.push(`/challenge/${roomIdParam.value}`)
}

// ============ P2 #14: 合并接口一次拿齐 ============
async function loadAll() {
  loading.value = true
  loadError.value = ''
  try {
    // 合并调用：room + cards + questions 三合一
    const res = await axios.get(`/api/room/state/${roomIdParam.value}?include_static=true`)
    if (!res.data.room) {
      throw new Error('房间不存在')
    }
    store.applyState(res.data.room)
    store.applyStatic({
      cards: res.data.cards,
      questions: res.data.questions,
    })
    // Backfill layers + scriptInfo from script endpoint
    try {
      const s = await axios.get('/api/script')
      scriptInfo.value = s.data
      layers.value = s.data.layers || {}
    } catch {
      layers.value = {}
    }
    if (!store.playerId) {
      store.playerId = sessionStorage.getItem(`room:${roomIdParam.value}:player_id`) || ''
    }
    console.log('[汤探局] 数据加载完成:', {
      cards: cards.value.length,
      questions: questions.value.length,
      phase: phase.value,
    })
  } catch (e: any) {
    const code = e?.response?.status
    loadError.value = `加载失败 (${code ?? '?'}): ${e?.message || '后端未启动'}`
    console.error('[汤探局] 加载失败', e)
  } finally {
    loading.value = false
  }
}

async function refreshState() {
  try {
    const res = await axios.get(`/api/room/state/${roomIdParam.value}`)
    store.applyState(res.data.room)
  } catch (e) {
    console.warn('[refreshState] failed', e)
  }
}

// ============ P1 #11: 合技卡牌可选性 ============
function cardOwnedByMe(cardId: string): boolean {
  if (!store.isMultiplayer) return true
  for (let i = store.cluesLog.length - 1; i >= 0; i--) {
    if (store.cluesLog[i].card_id === cardId) {
      return store.cluesLog[i].player_id === store.playerId
    }
  }
  return false
}

function cardOwnedByOpponent(cardId: string): boolean {
  if (!store.isMultiplayer) return false
  for (let i = store.cluesLog.length - 1; i >= 0; i--) {
    if (store.cluesLog[i].card_id === cardId) {
      return store.cluesLog[i].player_id !== store.playerId
    }
  }
  return false
}

function cardEligibleForCombo(cardId: string): boolean {
  // 该卡必须被至少一人用过（出过线索）
  return store.cluesLog.some(c => c.card_id === cardId)
}

// ============ 合技配对查询 ============
// 根据剧本 layers 计算：每张卡可能配对解锁哪些层
// 返回：[{layerKey, layerName, layerIcon, layerColor, partnerIds: string[], isUltimate: boolean}]
function cardComboTargets(cardId: string): {
  layerKey: string
  layerName: string
  layerIcon: string
  layerColor: string
  partnerIds: string[]
  isUltimate: boolean
}[] {
  const out: any[] = []
  const ls = layers.value || {}
  for (const [key, cfg] of Object.entries(ls) as [string, any][]) {
    if (unlockedLayers.value.includes(key)) continue // 已解锁的不再提示
    const pairs: string[] = Array.isArray(cfg.unlock_cards) ? cfg.unlock_cards : []
    const anySpec: string = cfg.unlock_cards_any || ''
    if (pairs.length === 2 && pairs.includes(cardId)) {
      const partner = pairs.find(p => p !== cardId)!
      out.push({
        layerKey: key,
        layerName: cfg.name,
        layerIcon: cfg.icon,
        layerColor: cfg.color,
        partnerIds: [partner],
        isUltimate: false,
      })
    } else if (anySpec && key === 'ultimate') {
      // 终极层：cardId 是「任意已用1」的那张
      out.push({
        layerKey: key,
        layerName: cfg.name,
        layerIcon: cfg.icon,
        layerColor: cfg.color,
        partnerIds: anySpec.split('+').map(s => s.trim()).filter(Boolean),
        isUltimate: true,
      })
    }
  }
  return out
}

// 某张卡能配对的「候选伙伴」集合（根据剧本推算），供高亮使用
function cardComboPartners(cardId: string): string[] {
  const flat: string[] = []
  cardComboTargets(cardId).forEach(t => flat.push(...t.partnerIds))
  return flat
}

// 当已选一张卡后，判断第二张可选卡能否与之配对
function isValidPairWithSelected(cardId: string): boolean {
  const sel = comboDialog.value.selected
  if (sel.length === 0) return true
  const firstId = sel[0]
  const partners = cardComboPartners(firstId)
  return partners.includes(cardId)
}

// 当已选两张后，返回这对组合可解锁的层（用于提示）
function comboSelectionLayerHint(): { name: string; icon: string; color: string } | null {
  const sel = comboDialog.value.selected
  if (sel.length !== 2) return null
  const ls = layers.value || {}
  for (const [key, cfg] of Object.entries(ls) as [string, any][]) {
    if (unlockedLayers.value.includes(key)) continue
    const pairs: string[] = Array.isArray(cfg.unlock_cards) ? cfg.unlock_cards : []
    if (pairs.length === 2) {
      const set = new Set(sel)
      const want = new Set(pairs)
      if (set.size === want.size && [...set].every(x => want.has(x))) {
        return { name: cfg.name, icon: cfg.icon, color: cfg.color }
      }
    } else if (key === 'ultimate' && cfg.unlock_cards_any) {
      // 终极层：只要包含 G7 任意一张 + 任一张已用卡即可
      const hasG7 = sel.some(id => cardComboPartners(id).length > 0 && id.startsWith('G7'))
      // 通用规则：选定 2 张且其中任意一张被 partner_ids 引用
      // 简化：只要选了 G7（被标记为终极同伴）+ 另一张任意
      const g7Cards = cards.value.filter((c: any) => c.id.toLowerCase().startsWith('g7')).map((c: any) => c.id)
      if (sel.some(id => g7Cards.includes(id))) {
        return { name: cfg.name, icon: cfg.icon, color: cfg.color }
      }
    }
  }
  return null
}

// 所有未解锁的合技配方列表（用于在卡牌上方悬浮提示）
const allComboRecipes = computed(() => {
  const ls = layers.value || {}
  const recipes: any[] = []
  for (const [key, cfg] of Object.entries(ls) as [string, any][]) {
    if (unlockedLayers.value.includes(key)) continue
    const pairs: string[] = Array.isArray(cfg.unlock_cards) ? cfg.unlock_cards : []
    const anySpec: string = cfg.unlock_cards_any || ''
    if (pairs.length === 2) {
      recipes.push({
        layerKey: key,
        layerName: cfg.name,
        layerIcon: cfg.icon,
        layerColor: cfg.color,
        comboName: cfg.unlock_combo || '',
        partnerIds: pairs,
        hint: `配对：${pairs.map(p => cardNameById(p)).join(' + ')}`,
      })
    } else if (anySpec && key === 'ultimate') {
      recipes.push({
        layerKey: 'ultimate',
        layerName: cfg.name,
        layerIcon: cfg.icon,
        layerColor: cfg.color,
        comboName: cfg.unlock_combo || '链结合技',
        partnerIds: [],
        hint: `终极合技：G7 任意已用 + 任一张已用武将`,
      })
    }
  }
  return recipes
})

// 查 ID 拿卡名
function cardNameById(id: string): string {
  const c = cards.value.find((x: any) => x.id === id)
  return c ? `${c.badge_icon} ${c.name}` : id
}

// ============ 玩家动作 ============
async function onAsk(qid: string) {
  if (players.value.length >= 2 && !isMyTurn.value) {
    ElMessage.warning('还没轮到你，请等待对手操作')
    return
  }
  if (questionsRemaining.value <= 0) {
    ElMessage.warning('提问次数已用尽，请用武将合技推进推理')
    return
  }
  // 优先 WS（省一 RTT），失败回落 HTTP
  let res: any = null
  if (ws.connected.value) {
    const ok = ws.send('ask', { qid, player_id: playerId.value || undefined })
    if (!ok) {
      // 退回 HTTP
      res = await axios.post('/api/ask', {
        room_id: roomIdParam.value, qid,
        player_id: playerId.value || undefined,
      })
    }
  } else {
    res = await axios.post('/api/ask', {
      room_id: roomIdParam.value, qid,
      player_id: playerId.value || undefined,
    })
  }
  if (res && !res.data.ok) {
    ElMessage.error(res.data.error || '提问失败')
    return
  }
  // WS 路径会通过 state_update 推送本地状态，这里直接用 res.data 处理推荐提示
  if (res && res.data.qa) {
    const qa = res.data.qa
    if (qa.is_negation) {
      suggestedCardId.value = qa.suggested_card || ''
      const cn = cardName(qa.suggested_card)
      ElMessageBox.alert(
        `❌ 错误猜想已记入否决板！\n💡 提示：建议使用 ${cn} 卡牌定向探查`,
        '智能推荐',
        { confirmButtonText: '已了解', type: 'warning' }
      )
    } else {
      ElMessage.success(`回答：${qa.answer}｜${qa.knowledge_point}`)
    }
  }
  if (res) await refreshState()
}

async function onSelectCard(card: any) {
  if (players.value.length >= 2 && !isMyTurn.value) {
    ElMessage.warning('还没轮到你')
    return
  }
  const used = cardUsage.value[card.id] || 0
  if (used >= card.max_use) {
    ElMessage.warning(`${card.name} 已用尽（${card.max_use} 次）`)
    return
  }

  try {
    await ElMessageBox.confirm(
      `${card.name} 已准备好。\n\n请选择出牌方式：\n  •【单卡出牌】拿 1 条线索\n  •【选合技】从下方选 2 张卡组合\n   （解锁整层/终极层）`,
      '出牌方式',
      {
        confirmButtonText: '单卡出牌',
        cancelButtonText: '⚡ 选合技',
        type: 'info',
        confirmButtonClass: 'el-button--primary',
        cancelButtonClass: 'el-button--warning',
        distinguishCancelAndClose: true,
      }
    )
    // 单卡出牌
    let res: any = null
    if (ws.connected.value) {
      // 只走 WS，不走 HTTP（避免双发 → 间隔 1 次点击消耗 2 次使用）
      ws.send('use_card', { card_id: card.id, player_id: playerId.value || undefined })
      res = { data: { ok: true, clue: '' } }
    } else {
      res = await axios.post('/api/card/use', {
        room_id: roomIdParam.value,
        card_id: card.id,
        player_id: playerId.value || undefined,
      })
    }
    if (!res.data.ok) { ElMessage.error(res.data.error); return }
    if (suggestedCardId.value && card.id === suggestedCardId.value) {
      suggestedCardId.value = ''
    }
    ElMessage.success(`🎴 ${card.name} 出了！`)
    await refreshState()
    // 走 WS 时，线索揭示后服务端会广播 state_update，从 cluesLog 末尾取最新一条
    if (ws.connected.value) {
      const latest = cluesLog.value[cluesLog.value.length - 1]
      if (latest && latest.card_id === card.id) {
        cardDialog.value = {
          visible: true,
          title: `${card.badge_icon} ${card.name} 的发现`,
          clue: latest  // cluesLog 中的 Clue 对象含 label/content/knowledge_point
        }
      }
    } else if (res.data.clue) {
      cardDialog.value = {
        visible: true,
        title: `${card.badge_icon} ${card.name} 的发现`,
        clue: res.data.clue
      }
    }
  } catch {
    comboDialog.value = { visible: true, selected: [] }
  }
}

function openComboDialog() {
  // 判断是否有足够可合技的卡（至少 2 张已出过线索的卡）
  const eligibleCount = cards.value.filter((c: any) => cardEligibleForCombo(c.id)).length
  if (eligibleCount < 2) {
    ElMessage.warning(`需要至少 2 张已出过线索的卡才能合技（当前 ${eligibleCount} 张）`)
    return
  }
  comboDialog.value = { visible: true, selected: [] }
}

function toggleComboSelect(id: string) {
  if (!cardEligibleForCombo(id)) {
    ElMessage.warning('这张卡还没出过线索，不能参与合技')
    return
  }
  const arr = comboDialog.value.selected
  if (arr.includes(id)) {
    comboDialog.value.selected = arr.filter(x => x !== id)
  } else if (arr.length < 2) {
    comboDialog.value.selected = [...arr, id]
  } else {
    comboDialog.value.selected = [arr[1], id]
  }
}

async function confirmCombo() {
  try {
    let res: any = null
    if (ws.connected.value) {
      // WS 路径：异步等后端响应（之前的同步桩会丢错误，导致 UI 无反应）
      res = await new Promise((resolve) => {
        let resolved = false
        const off = ws.on((msg) => {
          // 后端响应是 {ok, action:'combo', ...}（不是 state_update）
          if (msg.action === 'combo') {
            if (!resolved) { resolved = true; off(); resolve({ data: msg }) }
          }
        })
        const sent = ws.send('combo', {
          cards: comboDialog.value.selected,
          player_id: playerId.value || undefined,
        })
        if (!sent) {
          // WS 没连上 → 回落 HTTP
          axios.post('/api/card/combo', {
            room_id: roomIdParam.value,
            cards: comboDialog.value.selected,
            player_id: playerId.value || undefined,
          }).then(r => { if (!resolved) { resolved = true; off(); resolve({ data: r.data }) } })
            .catch(e => { if (!resolved) { resolved = true; off(); resolve({ data: { ok: false, error: e.message } }) } })
        }
        // 超时保护 5s
        setTimeout(() => { if (!resolved) { resolved = true; off(); resolve({ data: { ok: false, error: '合技超时（未收到服务端响应）' } }) } }, 5000)
      })
    } else {
      res = await axios.post('/api/card/combo', {
        room_id: roomIdParam.value,
        cards: comboDialog.value.selected,
        player_id: playerId.value || undefined,
      })
    }
    comboDialog.value.visible = false
    if (!res.data.ok) {
      ElMessage.error('❌ ' + (res.data.error || res.data.detail || '合技失败'))
      return
    }
    if (res.data.unlock_layer) {
      const layer = res.data.layer_data
      revealDialog.value = {
        visible: true,
        title: `⚡ ${res.data.combo_name} → ${layer.name}`,
        text: layer.reveal_text
      }
      burst(40)
      if (res.data.unlock_layer === 'ultimate') {
        setTimeout(() => celebrate(), 200)
        ElMessage.success({
          message: '🏆 终极层解锁！点击底部"揭示汤底"按钮查看完整 4 层真相',
          duration: 4000,
        })
      } else {
        ElMessage.success(`⚡ ${res.data.combo_name} → 解锁 ${layer.name}`)
      }
    }
    await refreshState()
  } catch (e: any) {
    // FastAPI HTTPException 把 message 放在 response.data.detail
    const detail = e?.response?.data?.detail || e?.response?.data?.error || e?.message
    ElMessage.error('合技失败：' + detail)
  }
}

async function goPhase(target: string) {
  try {
    let res: any = null
    if (ws.connected.value) {
      ws.send('set_phase', { target })
      res = { data: { ok: true } }
    } else {
      res = await axios.post('/api/room/phase', { room_id: roomIdParam.value, target })
    }
    if (!res.data.ok) {
      ElMessage.error(res.data.error || '阶段切换失败')
      return
    }
    ElMessage.success(`已切换到「${PHASE_LABELS[target] || target}」阶段`)
    await refreshState()
  } catch (e: any) {
    ElMessage.error('阶段切换失败：' + (e.message || e))
  }
}

async function onReveal() {
  try {
    let res: any = null
    if (ws.connected.value) {
      // WS 路径：异步等后端 action='reveal' 回包（包含 4 层汤底数据）
      res = await new Promise((resolve) => {
        let resolved = false
        const off = ws.on((msg) => {
          if (msg.action === 'reveal') {
            if (!resolved) { resolved = true; off(); resolve({ data: msg }) }
          }
        })
        const sent = ws.send('reveal')
        if (!sent) {
          axios.post('/api/room/reveal', { room_id: roomIdParam.value })
            .then(r => { if (!resolved) { resolved = true; off(); resolve({ data: r.data }) } })
            .catch(e => { if (!resolved) { resolved = true; off(); resolve({ data: { ok: false, error: e.message } }) } })
        }
        setTimeout(() => { if (!resolved) { resolved = true; off(); resolve({ data: { ok: false, error: '揭晓超时（5s 未收到响应）' } }) } }, 5000)
      })
    } else {
      res = await axios.post('/api/room/reveal', { room_id: roomIdParam.value })
    }
    if (!res.data.ok) {
      ElMessage.error(res.data.error || '揭晓失败')
      return
    }
    if (res.data.layers) {
      finalRevealDialog.value = {
        visible: true,
        title: `🎉 ${res.data.title || '汤底全貌'}`,
        layers: res.data.layers
      }
    }
    setTimeout(() => celebrate(), 250)
    await refreshState()
  } catch (e: any) {
    ElMessage.error('揭晓失败：' + e.message)
  }
}

async function onDebrief() {
  try {
    finalRevealDialog.value.visible = false
    let res: any = null
    if (ws.connected.value) {
      ws.send('debrief')
      res = { data: { ok: true } }
    } else {
      res = await axios.post('/api/room/debrief', { room_id: roomIdParam.value })
    }
    if (!res.data.ok) { ElMessage.error(res.data.error || '进入复盘失败'); return }
    ElMessage.info('进入复盘阶段')
    await refreshState()
    router.push(`/debrief/${roomIdParam.value}`)
  } catch (e: any) {
    ElMessage.error('进入复盘失败：' + e.message)
  }
}

async function onExtend() {
  try {
    let res: any = null
    if (ws.connected.value) {
      ws.send('extend')
      res = { data: { ok: true } }
    } else {
      res = await axios.post('/api/room/extend', { room_id: roomIdParam.value })
    }
    if (!res.data.ok) { ElMessage.error(res.data.error || '进入拓展失败'); return }
    ElMessage.success('🌱 进入拓展阶段')
    await refreshState()
  } catch (e: any) {
    ElMessage.error('进入拓展失败：' + e.message)
  }
}

async function devResetCards() {
  try {
    await ElMessageBox.confirm(
      '调试功能：将当前房间所有武将卡使用计数清零。仅在 dev 模式可见。',
      '重置武将卡',
      { confirmButtonText: '确认重置', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await axios.post('/api/dev/reset_cards', { room_id: roomIdParam.value })
    if (!res.data.ok) { ElMessage.error(res.data.error || '重置失败'); return }
    ElMessage.success('🔄 武将卡已重置，可以重新出牌 / 合技')
    await refreshState()
  } catch (e: any) {
    if (e === 'cancel') return
    ElMessage.error('重置失败：' + (e?.message || e))
  }
}

function cardName(id: string): string {
  const c = cards.value.find(c => c.id === id)
  return c ? `${c.badge_icon}${c.name}` : id
}

function categoryTag(cat: string): 'success' | 'warning' | 'primary' {
  if (cat === '物质类') return 'success'
  if (cat === '环境变量类') return 'warning'
  return 'primary'
}

function answerTag(ans: string): 'success' | 'danger' | 'info' {
  if (ans === '是') return 'success'
  if (ans === '否') return 'danger'
  return 'info'
}

function goDebrief() {
  if (unlockedLayers.value.length === 0) {
    ElMessage.warning('还未解锁任何层，无法查看复盘')
    return
  }
  router.push(`/debrief/${roomIdParam.value}`)
}
function goHome() { router.push('/') }
function goLearnFromDialog() {
  const kp = cardDialog.value.clue?.knowledge_point
  if (!kp) return
  cardDialog.value.visible = false
  router.push(`/learn/${encodeURIComponent(kp)}`)
}

onMounted(loadAll)
</script>

<style scoped>
.play-page {
  padding: 14px 18px 32px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #ebe6da 100%);
}
.play-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px 18px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
.play-header h2 {
  margin: 0;
  color: #5d4037;
  font-size: 20px;
  display: inline-block;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}
.phase-chip {
  font-weight: bold;
}
.room-id {
  font-size: 12px;
  color: #8d6e63;
  background: #faf6ef;
  padding: 3px 10px;
  border-radius: 10px;
}
.room-id code {
  font-family: 'Cascadia Mono', Consolas, monospace;
  color: #5d4037;
  font-weight: bold;
}
.ws-dot {
  font-size: 12px;
  color: #c0c4cc;
  cursor: default;
}
.ws-dot.on { color: #67c23a; }
.phase-hint { margin-bottom: 10px; }
.play-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 320px;
  gap: 14px;
  align-items: start;
}
/* intro 阶段：两栏布局，中心放大 */
.play-grid.phase-intro {
  grid-template-columns: 300px minmax(0, 1fr) 320px;
}
.play-grid.phase-debrief,
.play-grid.phase-extend {
  grid-template-columns: 300px minmax(0, 1fr) 320px;
}
.play-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.card-block {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
.card-block + .card-block {
  margin-top: 0;
}
.card-block h4 { margin: 0 0 10px; color: #5d4037; }

/* intro 阶段中央英雄区 */
.intro-hero {
  border: 2px solid #d4a574;
  background: linear-gradient(180deg, #fffaf2 0%, #fff 100%);
  padding: 20px 22px;
}
.hero-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}
.hero-head h3 {
  margin: 0;
  color: #5d4037;
  font-size: 18px;
}
.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.hero-subtitle {
  background: #fff8e1;
  border-left: 4px solid #d4a574;
  border-radius: 4px;
  padding: 10px 14px;
  margin: 0 0 12px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.8;
  color: #5d4037;
  white-space: pre-wrap;
  max-height: 140px;
  overflow-y: auto;
}
.hero-scene {
  background: #faf6ef;
  border-left: 4px solid #d4a574;
  border-radius: 4px;
  padding: 12px 14px;
  margin: 0 0 12px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.85;
  color: #303133;
  white-space: pre-wrap;
  max-height: 380px;
  overflow-y: auto;
}
.hero-knowledge {
  background: #ecf5ff;
  border-left: 4px solid #409eff;
  border-radius: 4px;
  padding: 10px 14px;
  font-size: 13px;
  color: #303133;
  margin-bottom: 12px;
  line-height: 1.7;
}
.hero-tip {
  background: #fdf6ec;
  border: 1px dashed #e6a23c;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 13px;
  color: #6b4a17;
  line-height: 1.7;
}
.hero-info-toggle {
  cursor: pointer;
  display: inline-block;
  padding: 6px 12px;
  margin: 0 0 6px;
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 13px;
  color: #409eff;
  user-select: none;
  list-style: none;
  transition: background 0.2s;
}
.hero-info-toggle:hover {
  background: #d9ecff;
}
.hero-info-toggle::-webkit-details-marker {
  display: none;
}
.hero-scene-wrap,
.hero-knowledge-wrap {
  margin-bottom: 10px;
}
details[open] .hero-info-toggle {
  background: #d9ecff;
  border-color: #409eff;
  margin-bottom: 8px;
}

/* ====== 汤面贴边卡【提问阶段可见】====== */
.tang-mian-compact {
  background: linear-gradient(135deg, #fff8e1 0%, #fdf6ec 100%);
  border: 1px solid #f0d8b0;
  border-left: 4px solid #d4a574;
}
.tang-mian-compact .tm-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  cursor: pointer;
  user-select: none;
}
.tang-mian-compact .tm-icon { font-size: 18px; }
.tang-mian-compact .tm-title {
  font-weight: 800;
  color: #5d4037;
  font-size: 15px;
  letter-spacing: 0.5px;
}
.tang-mian-compact .tm-toggle {
  margin-left: auto;
  background: #fff;
  border: 1px solid #d4a574;
  border-radius: 999px;
  padding: 4px 14px;
  font-size: 12px;
  color: #b8875a;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s;
}
.tang-mian-compact .tm-toggle:hover {
  background: #fff8e1;
  transform: translateY(-1px);
}
.tang-mian-compact .tm-toggle.open {
  background: #d4a574;
  color: #fff;
  border-color: #b8875a;
}
.tm-subtitle {
  margin: 12px 0 0;
  padding: 10px 14px;
  background: rgba(255,255,255,0.7);
  border-left: 3px solid #d4a574;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.75;
  color: #5d4037;
  white-space: pre-wrap;
}
.tm-details {
  margin-top: 10px;
}
.tm-details summary {
  cursor: pointer;
  display: inline-block;
  padding: 6px 12px;
  background: rgba(255,255,255,0.85);
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 13px;
  color: #409eff;
  user-select: none;
  list-style: none;
  transition: background 0.2s;
  font-weight: 600;
}
.tm-details summary:hover { background: #d9ecff; }
.tm-details summary::-webkit-details-marker { display: none; }
.tm-scene {
  background: #faf6ef;
  border-left: 4px solid #d4a574;
  border-radius: 4px;
  padding: 12px 14px;
  margin: 8px 0 4px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.85;
  color: #303133;
  white-space: pre-wrap;
  max-height: 280px;
  overflow-y: auto;
}
.tm-knowledge {
  background: #fef9f3;
  border-radius: 4px;
  padding: 10px 14px;
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.7;
  color: #5d4037;
}

@media (max-width: 1180px) {
  .play-grid,
  .play-grid.phase-intro {
    grid-template-columns: 1fr;
  }
  .play-col { order: 1; }
  .play-col.center { order: 0; }
  .play-col.right { order: 2; }
}
.dialog-item {
  background: #faf6ef;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
  font-size: 13px;
}
.q-row { margin-bottom: 6px; }
.a-row .hint {
  font-style: italic;
  color: #8d6e63;
  margin-left: 6px;
  font-size: 12px;
}
.combo-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 12px 0;
}
.combo-card {
  border: 2px solid #d4a574;
  border-radius: 8px;
  padding: 10px 6px;
  text-align: center;
  cursor: pointer;
  background: #fff8e1;
  transition: all 0.15s;
  position: relative;
}
.combo-card:hover { transform: translateY(-2px); }
.combo-card.selected {
  background: #e6a23c;
  color: #fff;
  border-color: #b8821e;
}
.combo-card.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.combo-card.by-opponent {
  border-color: #409eff;
  background: #ecf5ff;
}
.combo-card-icon { font-size: 28px; margin-bottom: 4px; }
.combo-card-name { font-size: 13px; font-weight: bold; }
.footer-actions {
  text-align: center;
  margin-top: 24px;
  padding-bottom: 24px;
}
.clue-label {
  font-weight: bold;
  font-size: 16px;
  color: #5d4037;
  margin-bottom: 8px;
}
.clue-content {
  background: #faf6ef;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
  border-left: 4px solid #67c23a;
}
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
@keyframes fireworks-fade {
  to { opacity: 0; }
}

.reveal-text {
  white-space: pre-wrap;
  font-family: inherit;
  background: #faf6ef;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.8;
  color: #303133;
  max-height: 60vh;
  overflow-y: auto;
}
.final-reveal { max-height: 60vh; overflow-y: auto; padding-right: 4px; }
.final-layer {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #faf6ef;
  border-left: 4px solid #d4a574;
}
.final-layer-head {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 16px;
  color: #5d4037;
  margin-bottom: 8px;
}
.final-layer-icon { font-size: 20px; }
.final-layer-text {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.8;
  color: #303133;
  margin: 0;
}
.turn-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  background: #f5f7fa;
  border: 1px solid #c0c4cc;
  font-size: 12px;
  color: #606266;
  transition: all 0.4s;
}
.turn-indicator.my {
  background: linear-gradient(90deg, #67c23a, #409eff);
  color: white;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.4);
  animation: turn-pulse 2s ease-in-out infinite;
}
.turn-icon { font-size: 14px; }
.turn-fade-enter-active, .turn-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.turn-fade-enter-from, .turn-fade-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
@keyframes turn-pulse {
  0%, 100% { box-shadow: 0 2px 8px rgba(103, 194, 58, 0.4); }
  50% { box-shadow: 0 2px 14px rgba(103, 194, 58, 0.8); }
}

/* ===== 武将手牌出场动画（提问阶段隐藏 / 出牌阶段才出现） ===== */
.card-hand-stage {
  position: sticky;
  bottom: 12px;
  z-index: 30;
  background: linear-gradient(180deg,
    rgba(255,255,255,0) 0%,
    rgba(255,255,255,0.96) 30%,
    #fff 100%);
  padding-top: 14px;
  margin-top: 14px;
  /* 💡 说明：武将手牌会贴到视口下方，方便处理长 Q&A 历史时跳转跳查看武将卡 */
}
.card-hand-stage.is-reveal {
  /* 终极层揭晓后变为控件状态：默认收起，顶上有一栏小访问口 */
  position: sticky;
  bottom: 12px;
}
.card-hand-dock-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 16px;
  margin: 0 12px;
  width: calc(100% - 24px);
  background: linear-gradient(135deg, #fdf6ec 0%, #ffe0b2 100%);
  color: #b8875a;
  border: 1px dashed #d4a574;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  transition: all 0.2s;
}
.card-hand-dock-toggle:hover {
  background: linear-gradient(135deg, #fff8e1 0%, #ffd591 100%);
  border-style: solid;
  transform: translateY(-1px);
}
.card-hand-dock-toggle em {
  font-style: normal;
  font-weight: 500;
  font-size: 11px;
  color: #909399;
  letter-spacing: 0;
}
/* 📦 收起状态下独立出在顶部的「一键展开」按钮【保证总能点开】 */
.card-hand-restore-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 18px;
  margin: 0;
  background: linear-gradient(135deg, #ffd591 0%, #ffba5c 100%);
  color: #5d4037;
  border: none;
  border-top: 3px solid #d4a574;
  border-radius: 0;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 2px;
  box-shadow: 0 -4px 12px rgba(212, 165, 116, 0.3);
  transition: all 0.25s;
  position: relative;
  z-index: 5;
}
.card-hand-restore-btn:hover {
  background: linear-gradient(135deg, #ffe0b2 0%, #ffb84d 100%);
  letter-spacing: 3px;
  color: #3e2723;
}
.card-hand-restore-btn:active {
  transform: translateY(1px);
}
.card-hand-restore-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: restore-shine 2.5s linear infinite;
}
@keyframes restore-shine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.card-hand-expand-enter-active,
.card-hand-expand-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.card-hand-expand-enter-from,
.card-hand-expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.card-hand-collapse-enter-active,
.card-hand-collapse-leave-active {
  transition: opacity 0.3s ease, max-height 0.4s ease, transform 0.3s ease;
  overflow: hidden;
}
.card-hand-collapse-enter-from,
.card-hand-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-6px);
}
.card-hand-collapse-enter-to,
.card-hand-collapse-leave-from {
  opacity: 1;
  max-height: 600px;
  transform: translateY(0);
}
.stage-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(90deg, #fff7e6 0%, #ffe7ba 100%);
  border-left: 4px solid #e6a23c;
  padding: 10px 16px;
  margin: 12px 12px 0;
  border-radius: 8px;
  font-size: 13px;
  color: #b8875a;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(230, 162, 60, 0.15);
}
.stage-banner .banner-icon {
  font-size: 16px;
  color: #e6a23c;
  animation: banner-shimmer 1.6s ease-in-out infinite;
}
.stage-banner .banner-sub {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  color: #909399;
  font-style: italic;
}
@keyframes banner-shimmer {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

.card-hand-rise-enter-active,
.card-hand-rise-leave-active {
  transition: opacity 0.45s ease, transform 0.55s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.card-hand-rise-enter-from,
.card-hand-rise-leave-to {
  opacity: 0;
  transform: translateY(28px) scale(0.96);
}

/* ===== 合技弹窗内的配方表 ===== */
.combo-recipe-hint {
  background: #faf6ef;
  border-radius: 6px;
  padding: 10px 12px;
  margin: 8px 0 12px;
  border: 1px dashed #d4a574;
}
.recipe-title {
  font-size: 12px;
  color: #b8875a;
  font-weight: 700;
  margin-bottom: 6px;
}
.recipe-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-left: 3px solid;
  background: #fff;
  margin-bottom: 4px;
  font-size: 12px;
  border-radius: 4px;
}
.recipe-item:last-child { margin-bottom: 0; }
.recipe-item .recipe-icon { font-size: 14px; }
.recipe-item .recipe-name { color: #909399; font-size: 11px; }
.recipe-item .recipe-text { color: #5d4037; flex: 1; text-align: right; font-size: 11px; }

/* ===== 选中第一张后的动态提示 ===== */
.combo-selected-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  margin: 8px 0 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.combo-hint-fade-enter-active,
.combo-hint-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.combo-hint-fade-enter-from,
.combo-hint-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ===== 选中两张后的预备提示 ===== */
.combo-ready-hint {
  padding: 10px 14px;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  margin: 8px 0 12px;
  border: 2px solid;
  text-align: center;
  font-weight: 600;
  animation: combo-ready-pulse 1s ease-in-out infinite;
}
@keyframes combo-ready-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* ===== 可配对高亮 ===== */
.combo-card.can-pair {
  border: 2px dashed #e6a23c;
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
  animation: can-pair-shimmer 1.2s ease-in-out infinite;
}
.combo-card.can-pair:hover {
  transform: translateY(-4px) scale(1.05);
  border-style: solid;
  border-color: #e6a23c;
  box-shadow: 0 6px 16px rgba(230, 162, 60, 0.4);
}
@keyframes can-pair-shimmer {
  0%, 100% { box-shadow: 0 0 0 0 rgba(230, 162, 60, 0); }
  50% { box-shadow: 0 0 0 6px rgba(230, 162, 60, 0.25); }
}

/* ===== 武将卡上的配对标签 ===== */
.combo-card-pair-hint {
  position: absolute;
  bottom: 4px;
  right: 4px;
  display: flex;
  gap: 2px;
}
.pair-hint-dot {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 6px;
  color: #fff;
  font-weight: bold;
  cursor: help;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* ===== 通关挑战 CTA ===== */
.challenge-cta {
  animation: challenge-pulse 2s ease-in-out infinite;
  font-weight: bold;
  background: linear-gradient(90deg, #fff7e6 0%, #ffe7ba 100%) !important;
  border-color: #e6a23c !important;
  color: #b8875a !important;
}
.challenge-cta:hover {
  background: linear-gradient(90deg, #e6a23c 0%, #d4a574 100%) !important;
  color: #fff !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(230, 162, 60, 0.4);
}
@keyframes challenge-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(230, 162, 60, 0); }
}
.challenge-arise-enter-active,
.challenge-arise-leave-active {
  transition: opacity 0.4s, transform 0.4s;
}
.challenge-arise-enter-from,
.challenge-arise-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
