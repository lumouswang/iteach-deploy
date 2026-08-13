/**
 * 挑战题库 composable
 * 提供：题目加载、答题计分、错题追溯、奖项判定
 */
import { ref, computed } from 'vue'
import challengeData from '../data/challenge_questions.json'

export type QuestionType = 'choice' | 'ordering' | 'judge' | 'fillEquation' | 'shortAnswer' | 'openEnded'

export interface Question {
  id: string
  type: QuestionType
  abilityLayer: string
  linkedLayer: string
  linkedKp: string
  stem: string
  options?: Array<{ key: string; text: string }>
  answer?: string
  items?: Array<{ id: string; text: string }>
  correctOrder?: string[]
  blanks?: Array<{ id: string; answer: string; altAnswers: string[]; placeholder: string }>
  sampleAnswer?: string
  keyPoints?: string[]
  evaluationCriteria?: string[]
  commonMistakes?: string[]
  explanation: string
  hint: string
  learnRoute: string
}

export interface UserAnswer {
  questionId: string
  // choice/judge: 'A' | 'B' | 'C' | 'D'
  // ordering: string[] 用户排序
  // fillEquation: Record<blankId, string>
  // shortAnswer/openEnded: string
  raw: any
  userInput?: string
}

export interface QuestionResult {
  questionId: string
  score: number  // 0/1/2
  maxScore: number
  correct: boolean
  partial: boolean
  userAnswer: any
  feedback: string
}

export const useChallenge = () => {
  const questions = ref<Question[]>(challengeData.questions as Question[])
  const gradingRules = ref(challengeData.grading)
  const passingScore = ref((challengeData as any).passingScore ?? (challengeData as any).meta?.passingScore ?? 4)

  const totalQuestions = computed(() => questions.value.length)

  // ---------- 评分 ----------
  function gradeChoice(q: Question, userKey: string): { score: number; max: number; feedback: string } {
    const correct = q.answer === userKey
    const feedback = correct
      ? `✅ 正确！${q.explanation}`
      : `❌ 错误。正确答案：${q.answer}。${q.explanation}`
    return { score: correct ? 1 : 0, max: 1, feedback }
  }

  function gradeOrdering(q: Question, userOrder: string[]): { score: number; max: number; feedback: string } {
    const correct = q.correctOrder || []
    let matchCount = 0
    userOrder.forEach((id, idx) => {
      if (correct[idx] === id) matchCount++
    })
    const allCorrect = matchCount === correct.length
    const partial = matchCount > 0 && matchCount < correct.length
    const score = allCorrect ? 2 : partial ? 1 : 0
    const feedback = allCorrect
      ? `✅ 完美！${q.explanation}`
      : partial
      ? `⚠️ 部分正确（${matchCount}/${correct.length} 步正确）。${q.explanation}`
      : `❌ 顺序错误。正确顺序：${correct.map((id, i) => `${i + 1}. ${q.items?.find(it => it.id === id)?.text}`).join(' → ')}`
    return { score, max: 2, feedback }
  }

  function gradeFillEquation(q: Question, userBlanks: Record<string, string>): { score: number; max: number; feedback: string } {
    const blanks = q.blanks || []
    let correctCount = 0
    blanks.forEach(b => {
      const userAns = (userBlanks[b.id] || '').trim()
      const allAccepted = [b.answer, ...b.altAnswers].map(a => a.toLowerCase())
      if (allAccepted.includes(userAns.toLowerCase())) correctCount++
    })
    const allCorrect = correctCount === blanks.length
    const partial = correctCount > 0 && correctCount < blanks.length
    const score = allCorrect ? 2 : partial ? 1 : 0
    const feedback = allCorrect
      ? `✅ 方程式完全正确！${q.explanation}`
      : partial
      ? `⚠️ 部分正确（${correctCount}/${blanks.length}）。${q.explanation}`
      : `❌ 错误。正确方程式：${q.explanation}`
    return { score, max: 2, feedback }
  }

  function gradeShortAnswer(q: Question, userText: string): { score: number; max: number; feedback: string } {
    const text = (userText || '').trim()
    if (text.length < 5) {
      return { score: 0, max: 2, feedback: `⚠️ 答案过短（<5 字）。参考答案：${q.sampleAnswer}` }
    }
    // 简单关键词匹配（不依赖 LLM）
    const keyPoints = q.keyPoints || []
    let hitCount = 0
    keyPoints.forEach(kp => {
      // 提取关键词（中文 2-4 字片段）
      const fragments = kp.match(/[\u4e00-\u9fa5]{2,4}/g) || []
      fragments.forEach(f => {
        if (text.includes(f)) hitCount++
      })
    })
    const allCorrect = hitCount >= 3
    const partial = hitCount >= 1 && hitCount < 3
    const score = allCorrect ? 2 : partial ? 1 : 0
    const feedback = allCorrect
      ? `✅ 答得很全面！${q.explanation}`
      : partial
      ? `⚠️ 答对部分要点。建议补充。参考答案：${q.sampleAnswer}`
      : `❌ 关键点缺失。参考答案：${q.sampleAnswer}`
    return { score, max: 2, feedback }
  }

  function gradeOpenEnded(q: Question, userText: string): { score: number; max: number; feedback: string } {
    const text = (userText || '').trim()
    if (text.length < 10) {
      return { score: 0, max: 2, feedback: `⚠️ 答案过短（<10 字）。请详细描述鉴别方法。` }
    }
    const criteria = q.evaluationCriteria || []
    let hitCount = 0
    criteria.forEach(c => {
      const fragments = c.match(/[\u4e00-\u9fa5]{2,4}/g) || []
      fragments.forEach(f => {
        if (text.includes(f)) hitCount++
      })
    })
    const allCorrect = hitCount >= 4
    const partial = hitCount >= 1 && hitCount < 4
    const score = allCorrect ? 2 : partial ? 1 : 0
    const feedback = allCorrect
      ? `✅ 方案完整！${q.explanation}`
      : partial
      ? `⚠️ 方案部分可行。常见遗漏：${q.commonMistakes?.join('；')}`
      : `❌ 方案欠考虑。常见错误：${q.commonMistakes?.join('；')}。参考答案：${q.sampleAnswer}`
    return { score, max: 2, feedback }
  }

  function gradeQuestion(q: Question, userAnswer: any): QuestionResult {
    let result: { score: number; max: number; feedback: string }
    switch (q.type) {
      case 'choice':
      case 'judge':
        result = gradeChoice(q, userAnswer)
        break
      case 'ordering':
        result = gradeOrdering(q, userAnswer)
        break
      case 'fillEquation':
        result = gradeFillEquation(q, userAnswer)
        break
      case 'shortAnswer':
        result = gradeShortAnswer(q, userAnswer)
        break
      case 'openEnded':
        result = gradeOpenEnded(q, userAnswer)
        break
      default:
        result = { score: 0, max: 1, feedback: '❓ 未知题型' }
    }
    return {
      questionId: q.id,
      score: result.score,
      maxScore: result.max,
      correct: result.score === result.max,
      partial: result.score > 0 && result.score < result.max,
      userAnswer,
      feedback: result.feedback,
    }
  }

  // ---------- 奖项判定 ----------
  function judgeTier(totalScore: number) {
    const tiers = gradingRules.value.tiers
    for (const t of tiers) {
      if (totalScore >= t.minScore) return t
    }
    return tiers[tiers.length - 1]
  }

  // ---------- 能力层覆盖度（雷达图数据）----------
  function computeAbilityRadar(results: QuestionResult[]) {
    const abilityMap: Record<string, { got: number; max: number }> = {}
    results.forEach((r, i) => {
      const q = questions.value[i]
      const layer = q.abilityLayer
      if (!abilityMap[layer]) abilityMap[layer] = { got: 0, max: 0 }
      abilityMap[layer].got += r.score
      abilityMap[layer].max += r.maxScore
    })
    return Object.entries(abilityMap).map(([layer, v]) => ({
      layer,
      ability: ((v.got / v.max) * 100).toFixed(0),
      label: ({ L1: '识别', L2: '理解', L3: '应用', L4: '整合', L5: '反思' } as any)[layer] || layer,
    }))
  }

  return {
    questions,
    totalQuestions,
    passingScore,
    gradingRules,
    gradeQuestion,
    judgeTier,
    computeAbilityRadar,
  }
}
