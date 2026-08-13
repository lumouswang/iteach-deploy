<template>
  <div class="challenge-page">
    <!-- 顶部进度条 -->
    <div class="challenge-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" :icon="ArrowLeft">返回游戏</el-button>
        <h2 class="page-title">🎓 通关挑战 · 运城盐湖</h2>
      </div>
      <div class="header-right">
        <div class="progress-info">
          <span class="progress-label">进度</span>
          <span class="progress-current">{{ currentIndex + 1 }} / {{ totalQuestions }}</span>
        </div>
        <el-progress
          :percentage="progressPercent"
          :stroke-width="8"
          :show-text="false"
          color="#ff6b35"
          style="width: 160px"
        />
      </div>
    </div>

    <!-- 欢迎卡片（起始） -->
    <div v-if="!started" class="welcome-card">
      <div class="welcome-icon">🎓</div>
      <h1>准备好检验你的学习成果了吗？</h1>
      <p class="welcome-subtitle">{{ totalQuestions }} 道题 × 5 个能力层 × 4 个合技层</p>
      <div class="welcome-info">
        <el-alert
          title="规则说明"
          type="info"
          :closable="false"
          show-icon
        >
          <ul>
            <li>每题对应 Bloom 能力金字塔的一层（识别 / 理解 / 应用 / 整合 / 反思）</li>
            <li>答错没关系——每题都有「回到相关学习内容」快捷链接</li>
            <li>4 道题答对即可解锁「🏆 化石猎人」称号</li>
            <li>完整答完即可获得「能力雷达图」+ 错题诊断报告</li>
          </ul>
        </el-alert>
      </div>
      <div class="welcome-actions">
        <el-button @click="goBack" plain size="large">取消</el-button>
        <el-button @click="startChallenge" type="primary" size="large" round>
          🚀 开始挑战
        </el-button>
      </div>
    </div>

    <!-- 答题主区 -->
    <div v-else-if="!finished" class="quiz-main">
      <transition name="slide-fade" mode="out-in">
        <div :key="currentQuestion.id" class="question-card">
          <!-- 题目标签 -->
          <div class="question-meta">
            <el-tag :type="layerTagType" effect="dark" size="small">
              {{ currentQuestion.abilityLayer }} · {{ abilityLabel(currentQuestion.abilityLayer) }}
            </el-tag>
            <el-tag :type="layerTypeTag" effect="plain" size="small">
              {{ layerIcon(currentQuestion.linkedLayer) }} {{ layerName(currentQuestion.linkedLayer) }}
            </el-tag>
            <el-tag effect="plain" size="small" type="info">
              📚 {{ currentQuestion.linkedKp }}
            </el-tag>
          </div>

          <!-- 题干 -->
          <h2 class="question-stem">{{ currentQuestion.stem }}</h2>

          <!-- 选择题 -->
          <div v-if="currentQuestion.type === 'choice' || currentQuestion.type === 'judge'" class="options-grid">
            <button
              v-for="opt in currentQuestion.options"
              :key="opt.key"
              :class="[
                'option-button',
                {
                  'selected': currentAnswer === opt.key,
                  'correct': answered && opt.key === currentQuestion.answer,
                  'wrong': answered && currentAnswer === opt.key && opt.key !== currentQuestion.answer,
                }
              ]"
              :disabled="answered"
              @click="selectOption(opt.key)"
            >
              <span class="option-key">{{ opt.key }}</span>
              <span class="option-text">{{ opt.text }}</span>
              <span v-if="answered && opt.key === currentQuestion.answer" class="option-badge">✓</span>
              <span v-if="answered && currentAnswer === opt.key && opt.key !== currentQuestion.answer" class="option-badge">✗</span>
            </button>
          </div>

          <!-- 排序题 -->
          <div v-else-if="currentQuestion.type === 'ordering'" class="ordering-area">
            <p class="ordering-tip">👆 点击卡片，按顺序排列（第一个 → 最后一个）</p>
            <div class="ordering-pool">
              <div
                v-for="item in poolItems"
                :key="item.id"
                class="order-card pool"
                :class="{ used: selectedOrder.includes(item.id) }"
                @click="addToOrder(item.id)"
              >
                <span class="order-num">{{ selectedOrder.indexOf(item.id) + 1 || '?' }}</span>
                <span class="order-text">{{ item.text }}</span>
              </div>
            </div>
            <div v-if="selectedOrder.length > 0" class="ordering-slot">
              <p class="ordering-slot-label">📋 你的排序：</p>
              <div
                v-for="(id, idx) in selectedOrder"
                :key="id + '-slot'"
                class="order-card slot"
                @click="removeFromOrder(idx)"
              >
                <span class="order-num">{{ idx + 1 }}</span>
                <span class="order-text">{{ findItemText(id) }}</span>
                <span class="order-remove">✕</span>
              </div>
            </div>
          </div>

          <!-- 填空方程式 -->
          <div v-else-if="currentQuestion.type === 'fillEquation'" class="fill-equation">
            <div class="equation-line">
              <span class="equation-part">CaCO₃ + 2CH₃COOH → </span>
              <input
                v-for="blank in currentQuestion.blanks"
                :key="blank.id"
                v-model="fillAnswers[blank.id]"
                :placeholder="blank.placeholder"
                class="equation-blank"
                :disabled="answered"
              />
              <span v-if="indexOfBlank(1) !== -1" class="equation-part">↑</span>
            </div>
          </div>

          <!-- 简答题 / 开放题 -->
          <div v-else-if="currentQuestion.type === 'shortAnswer' || currentQuestion.type === 'openEnded'" class="text-answer">
            <el-input
              v-model="textAnswer"
              type="textarea"
              :rows="currentQuestion.type === 'shortAnswer' ? 3 : 6"
              :placeholder="currentQuestion.type === 'shortAnswer' ? '请用 10-20 字简要回答' : '请详细描述你的方案（至少 10 字）'"
              :disabled="answered"
              maxlength="200"
              show-word-limit
            />
          </div>

          <!-- 答题反馈 -->
          <div v-if="answered && currentResult" class="feedback-box" :class="feedbackClass">
            <div class="feedback-icon">{{ currentResult.correct ? '✅' : currentResult.partial ? '⚠️' : '❌' }}</div>
            <div class="feedback-content">
              <p class="feedback-score">{{ currentResult.score }} / {{ currentResult.maxScore }} 分</p>
              <p class="feedback-text">{{ currentResult.feedback }}</p>
              <div class="feedback-actions">
                <el-button @click="goLearn(currentQuestion)" type="primary" plain size="small">
                  📖 回到相关学习页
                </el-button>
                <el-button @click="nextQuestion" type="primary" size="small">
                  {{ currentIndex < totalQuestions - 1 ? '下一题 →' : '查看成绩 →' }}
                </el-button>
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div v-if="!answered" class="submit-area">
            <el-button
              @click="submitAnswer"
              type="primary"
              size="large"
              round
              :disabled="!canSubmit"
            >
              提交答案
            </el-button>
            <p v-if="!canSubmit" class="submit-hint">请先回答问题</p>
          </div>

          <!-- 提示（在未答之前可查看） -->
          <div v-if="!answered" class="hint-area">
            <el-button @click="showHint = !showHint" type="warning" plain size="small">
              💡 {{ showHint ? '隐藏提示' : '需要提示' }}
            </el-button>
            <div v-if="showHint" class="hint-content">
              {{ currentQuestion.hint }}
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- 成绩展示 -->
    <div v-else class="result-card">
      <div class="result-header" :style="{ background: tier.color }">
        <div class="tier-icon">{{ tier.icon }}</div>
        <h1>{{ tier.title }}</h1>
        <p class="tier-reward">{{ tier.reward }}</p>
      </div>

      <div class="result-body">
        <div class="score-summary">
          <div class="score-big">
            <span class="score-value">{{ totalScore }}</span>
            <span class="score-max"> / {{ maxScore }}</span>
          </div>
          <p class="score-text">总得分</p>
        </div>

        <!-- 能力雷达图 -->
        <div class="radar-section">
          <h3>📊 能力雷达图</h3>
          <div class="radar-grid">
            <div v-for="r in radar" :key="r.layer" class="radar-bar">
              <span class="radar-label">{{ r.label }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: r.ability + '%' }"></div>
              </div>
              <span class="radar-value">{{ r.ability }}%</span>
            </div>
          </div>
        </div>

        <!-- 错题诊断 -->
        <div v-if="wrongResults.length > 0" class="wrong-section">
          <h3>🔍 错题诊断（建议复习）</h3>
          <div v-for="r in wrongResults" :key="r.questionId" class="wrong-item">
            <div class="wrong-head">
              <span class="wrong-icon">{{ r.correct ? '✅' : '❌' }}</span>
              <span class="wrong-kp">{{ findKp(r.questionId) }}</span>
              <span class="wrong-score">{{ r.score }}/{{ r.maxScore }}</span>
            </div>
            <p class="wrong-feedback">{{ r.feedback }}</p>
            <el-button @click="goLearnById(r.questionId)" type="primary" plain size="small">
              📖 复习此知识点
            </el-button>
          </div>
        </div>

        <!-- 行动按钮 -->
        <div class="result-actions">
          <el-button @click="goBack" plain size="large">返回游戏</el-button>
          <el-button @click="goDebrief" type="primary" size="large" round>
            📊 查看完整复盘
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useChallenge } from '../composables/useChallenge'

const route = useRoute()
const router = useRouter()
const {
  questions, totalQuestions, gradeQuestion, judgeTier, computeAbilityRadar,
} = useChallenge()

const roomId = computed(() => route.params.roomId as string)
const started = ref(false)
const finished = ref(false)
const currentIndex = ref(0)
const currentAnswer = ref<string>('') // 选择/判断
const selectedOrder = ref<string[]>([]) // 排序
const fillAnswers = ref<Record<string, string>>({}) // 填空
const textAnswer = ref('') // 简答/开放
const answered = ref(false)
const currentResult = ref<any>(null)
const showHint = ref(false)
const results = ref<any[]>([])

const currentQuestion = computed(() => questions.value[currentIndex.value])
const canSubmit = computed(() => {
  const q = currentQuestion.value
  if (q.type === 'choice' || q.type === 'judge') return !!currentAnswer.value
  if (q.type === 'ordering') return selectedOrder.value.length === (q.items?.length || 0)
  if (q.type === 'fillEquation') return (q.blanks || []).every(b => fillAnswers.value[b.id]?.trim())
  if (q.type === 'shortAnswer') return textAnswer.value.trim().length >= 5
  if (q.type === 'openEnded') return textAnswer.value.trim().length >= 10
  return false
})
const progressPercent = computed(() => Math.round((currentIndex.value / totalQuestions.value) * 100))
const poolItems = computed(() => {
  const items = currentQuestion.value.items || []
  return items.filter(it => !selectedOrder.value.includes(it.id))
})

const totalScore = computed(() => results.value.reduce((s, r) => s + r.score, 0))
const maxScore = computed(() => questions.value.reduce((s, q) => {
  return s + (q.type === 'choice' || q.type === 'judge' ? 1 : 2)
}, 0))
const tier = computed(() => judgeTier(totalScore.value))
const radar = computed(() => computeAbilityRadar(results.value))
const wrongResults = computed(() => results.value.filter(r => !r.correct))

const layerTagType = computed<'success' | 'warning' | 'primary' | 'info' | 'danger'>(() => {
  const map: any = { L1: 'success', L2: 'primary', L3: 'warning', L4: 'danger', L5: 'info' }
  return map[currentQuestion.value?.abilityLayer] || 'info'
})
const layerTypeTag = computed<'success' | 'warning' | 'primary' | 'info' | 'danger'>(() => {
  const map: any = {
    phenomenon: 'success', condition: 'warning', microscopic: 'primary', ultimate: 'danger',
  }
  return map[currentQuestion.value?.linkedLayer] || 'info'
})
const feedbackClass = computed(() => {
  if (!currentResult.value) return ''
  return currentResult.value.correct ? 'feedback-correct' : currentResult.value.partial ? 'feedback-partial' : 'feedback-wrong'
})

function abilityLabel(layer: string) {
  return ({ L1: '识别', L2: '理解', L3: '应用', L4: '整合', L5: '反思' } as any)[layer] || layer
}
function layerName(key: string) {
  return ({ phenomenon: '现象层', condition: '条件层', microscopic: '微观层', ultimate: '终极层' } as any)[key] || key
}
function layerIcon(key: string) {
  return ({ phenomenon: '🌱', condition: '🌡️', microscopic: '🔬', ultimate: '🏔️' } as any)[key] || '🎯'
}

function selectOption(key: string) {
  if (answered.value) return
  currentAnswer.value = key
}
function addToOrder(id: string) {
  if (answered.value) return
  if (!selectedOrder.value.includes(id)) selectedOrder.value.push(id)
}
function removeFromOrder(idx: number) {
  if (answered.value) return
  selectedOrder.value.splice(idx, 1)
}
function findItemText(id: string) {
  return currentQuestion.value.items?.find(it => it.id === id)?.text || id
}
function indexOfBlank(num: number) {
  return (currentQuestion.value.blanks || []).findIndex(b => b.id === 'b' + num)
}

function submitAnswer() {
  if (!canSubmit.value) return
  let userAnswer: any
  const q = currentQuestion.value
  if (q.type === 'choice' || q.type === 'judge') {
    userAnswer = currentAnswer.value
  } else if (q.type === 'ordering') {
    userAnswer = [...selectedOrder.value]
  } else if (q.type === 'fillEquation') {
    userAnswer = { ...fillAnswers.value }
  } else {
    userAnswer = textAnswer.value
  }
  const result = gradeQuestion(q, userAnswer)
  currentResult.value = result
  answered.value = true
  results.value.push(result)
  // 滚动到反馈
  setTimeout(() => {
    document.querySelector('.feedback-box')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, 100)
}

function nextQuestion() {
  if (currentIndex.value < totalQuestions.value - 1) {
    currentIndex.value++
    resetQuestionState()
  } else {
    finished.value = true
    saveResult()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function resetQuestionState() {
  currentAnswer.value = ''
  selectedOrder.value = []
  fillAnswers.value = {}
  textAnswer.value = ''
  answered.value = false
  currentResult.value = null
  showHint.value = false
}

function startChallenge() {
  started.value = true
  resetQuestionState()
}

function goBack() {
  router.push(`/play/${roomId.value}`)
}
function goDebrief() {
  router.push(`/debrief/${roomId.value}`)
}
function goLearn(q: any) {
  // 优先跳到对应 KP 的学习页
  router.push(q.learnRoute)
}
function goLearnById(qid: string) {
  const q = questions.value.find(qq => qq.id === qid)
  if (q) router.push(q.learnRoute)
}

function findKp(qid: string) {
  return questions.value.find(q => q.id === qid)?.linkedKp || ''
}

function saveResult() {
  // 持久化到 sessionStorage（与房间绑定）
  const key = `challenge:${roomId.value}`
  sessionStorage.setItem(key, JSON.stringify({
    score: totalScore.value,
    maxScore: maxScore.value,
    tier: tier.value,
    answeredAt: Date.now(),
    results: results.value,
  }))
}

onMounted(() => {
  // 如果 URL 带有 ?resume=1，尝试恢复
  if (route.query.resume === '1') {
    const saved = sessionStorage.getItem(`challenge:${roomId.value}`)
    if (saved) {
      // 简化：直接开始
      started.value = true
    }
  }
})
</script>

<style scoped>
.challenge-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #ebe6da 100%);
  padding: 24px 32px 48px;
}

.challenge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 14px 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.page-title {
  margin: 0;
  font-size: 18px;
  color: #2c3e50;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.progress-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 13px;
}
.progress-label {
  color: #95a5a6;
}
.progress-current {
  font-weight: bold;
  color: #ff6b35;
}

/* 欢迎卡片 */
.welcome-card {
  max-width: 720px;
  margin: 60px auto;
  background: #fff;
  padding: 48px 40px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  text-align: center;
}
.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.welcome-card h1 {
  font-size: 24px;
  color: #2c3e50;
  margin: 0 0 12px;
}
.welcome-subtitle {
  color: #7f8c8d;
  margin-bottom: 24px;
}
.welcome-info {
  text-align: left;
  margin: 24px 0;
}
.welcome-info ul {
  margin: 8px 0 0;
  padding-left: 20px;
  line-height: 1.8;
}
.welcome-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

/* 答题主区 */
.quiz-main {
  max-width: 800px;
  margin: 0 auto;
}
.question-card {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.question-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.question-stem {
  font-size: 18px;
  color: #2c3e50;
  margin: 0 0 24px;
  line-height: 1.6;
}

/* 选项 */
.options-grid {
  display: grid;
  gap: 12px;
}
.option-button {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  font-size: 15px;
}
.option-button:hover:not(:disabled) {
  background: #fff3e0;
  border-color: #ff6b35;
}
.option-button.selected {
  background: #fff3e0;
  border-color: #ff6b35;
}
.option-button.correct {
  background: #d4edda;
  border-color: #28a745;
}
.option-button.wrong {
  background: #f8d7da;
  border-color: #dc3545;
}
.option-button:disabled {
  cursor: default;
}
.option-key {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #ff6b35;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}
.option-text {
  flex: 1;
}
.option-badge {
  font-size: 20px;
  font-weight: bold;
}

/* 排序 */
.ordering-area {
  margin-bottom: 16px;
}
.ordering-tip {
  color: #7f8c8d;
  margin-bottom: 12px;
  font-size: 14px;
}
.ordering-pool, .ordering-slot {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.ordering-slot {
  padding: 12px;
  background: #fff3e0;
  border-radius: 10px;
  border: 2px dashed #ff6b35;
}
.ordering-slot-label {
  margin: 0 0 8px;
  font-size: 13px;
  color: #ff6b35;
  font-weight: bold;
}
.order-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.order-card.pool.used {
  opacity: 0.4;
  cursor: default;
}
.order-card.pool:hover:not(.used) {
  border-color: #ff6b35;
  transform: translateY(-2px);
}
.order-card.slot {
  background: #fff3e0;
  border-color: #ff6b35;
}
.order-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ff6b35;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 13px;
  flex-shrink: 0;
}
.order-text {
  font-size: 14px;
}
.order-remove {
  color: #dc3545;
  font-weight: bold;
}

/* 填空 */
.equation-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 18px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}
.equation-part {
  font-family: 'Cambria Math', serif;
  color: #2c3e50;
}
.equation-blank {
  width: 160px;
  padding: 8px 12px;
  border: 2px solid #ff6b35;
  border-radius: 6px;
  font-size: 16px;
  font-family: 'Cambria Math', serif;
  background: #fff;
}
.equation-blank:disabled {
  background: #f0f0f0;
  border-color: #ccc;
}

/* 文本答案 */
.text-answer {
  margin-bottom: 16px;
}

/* 反馈 */
.feedback-box {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  padding: 20px;
  border-radius: 12px;
  border: 2px solid;
  animation: slideUp 0.3s ease;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.feedback-correct {
  background: #d4edda;
  border-color: #28a745;
  color: #155724;
}
.feedback-partial {
  background: #fff3cd;
  border-color: #ffc107;
  color: #856404;
}
.feedback-wrong {
  background: #f8d7da;
  border-color: #dc3545;
  color: #721c24;
}
.feedback-icon {
  font-size: 36px;
  flex-shrink: 0;
}
.feedback-content {
  flex: 1;
}
.feedback-score {
  font-size: 18px;
  font-weight: bold;
  margin: 0 0 8px;
}
.feedback-text {
  margin: 0 0 12px;
  line-height: 1.6;
}
.feedback-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 提交 & 提示 */
.submit-area {
  text-align: center;
  margin-top: 24px;
}
.submit-hint {
  color: #95a5a6;
  margin-top: 8px;
  font-size: 13px;
}
.hint-area {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e0e0e0;
}
.hint-content {
  margin-top: 12px;
  padding: 12px 16px;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  line-height: 1.6;
  font-size: 14px;
}

/* 成绩展示 */
.result-card {
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
}
.result-header {
  padding: 48px 32px;
  text-align: center;
  color: #fff;
}
.tier-icon {
  font-size: 72px;
  margin-bottom: 12px;
}
.result-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}
.tier-reward {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}
.result-body {
  padding: 32px;
}
.score-summary {
  text-align: center;
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid #f0f0f0;
}
.score-big {
  font-size: 56px;
  font-weight: bold;
  color: #ff6b35;
}
.score-max {
  font-size: 24px;
  color: #95a5a6;
}
.score-text {
  color: #7f8c8d;
  margin: 8px 0 0;
}

/* 雷达图 */
.radar-section {
  margin-bottom: 32px;
}
.radar-section h3 {
  margin: 0 0 16px;
  color: #2c3e50;
}
.radar-grid {
  display: grid;
  gap: 12px;
}
.radar-bar {
  display: grid;
  grid-template-columns: 80px 1fr 50px;
  align-items: center;
  gap: 12px;
}
.radar-label {
  font-weight: bold;
  color: #2c3e50;
}
.bar-track {
  height: 18px;
  background: #f0f0f0;
  border-radius: 9px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b35 0%, #f7931e 100%);
  border-radius: 9px;
  transition: width 0.8s ease;
}
.radar-value {
  font-weight: bold;
  color: #ff6b35;
  text-align: right;
}

/* 错题 */
.wrong-section {
  margin-bottom: 32px;
}
.wrong-section h3 {
  margin: 0 0 16px;
  color: #2c3e50;
}
.wrong-item {
  padding: 16px;
  background: #fff8f3;
  border-left: 4px solid #ff6b35;
  border-radius: 8px;
  margin-bottom: 12px;
}
.wrong-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.wrong-icon {
  font-size: 18px;
}
.wrong-kp {
  font-weight: bold;
  color: #2c3e50;
  flex: 1;
}
.wrong-score {
  color: #ff6b35;
  font-weight: bold;
}
.wrong-feedback {
  margin: 0 0 12px;
  color: #555;
  line-height: 1.5;
  font-size: 14px;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

/* 动画 */
.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* 响应式 */
@media (max-width: 768px) {
  .challenge-page {
    padding: 16px;
  }
  .challenge-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  .question-card {
    padding: 20px;
  }
  .question-stem {
    font-size: 16px;
  }
  .radar-bar {
    grid-template-columns: 60px 1fr 45px;
  }
}
</style>
