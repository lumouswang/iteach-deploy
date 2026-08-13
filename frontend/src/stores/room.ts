/**
 * 房间状态 store (Pinia)
 * 真正被 PlayView / DebriefView 引用 (P1 #6)
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Clue {
  clue_id: string
  card_id: string
  label: string
  content?: string
  knowledge_point?: string
  layer?: string | null
  player_id?: string
}

export interface QA {
  id: string
  category: string
  text: string
  answer: string
  knowledge_point?: string
  player_id?: string
}

export interface RoomState {
  room_id: string
  players: Array<{ user_id: string; user_name: string }>
  phase: string
  questions_remaining: number
  questions_per_player: Record<string, number>
  card_usage: Record<string, number>
  per_player_card_usage: Record<string, Record<string, number>>
  unlocked_layers: string[]
  is_multiplayer: boolean
  turn_player_id: string
  current_player?: { user_id: string; user_name: string }
  other_player?: { user_id: string; user_name: string } | null
  negation_board: any[]
  questions_log: QA[]
  clues_log: Clue[]
  combo_history: any[]
}

export const useRoomStore = defineStore('room', () => {
  const roomId = ref<string>('')
  const playerId = ref<string>('')
  const phase = ref<string>('lobby')
  const questionsRemaining = ref<number>(5)
  const questionsPerPlayer = ref<Record<string, number>>({})
  const cardUsage = ref<Record<string, number>>({})
  const perPlayerCardUsage = ref<Record<string, Record<string, number>>>({})
  const unlockedLayers = ref<string[]>([])
  const negationBoard = ref<any[]>([])
  const questionsLog = ref<QA[]>([])
  const cluesLog = ref<Clue[]>([])
  const comboHistory = ref<any[]>([])
  const players = ref<Array<{ user_id: string; user_name: string }>>([])
  const turnPlayerId = ref<string>('')
  const isMultiplayer = ref(false)

  // 静态数据
  const scriptInfo = ref<any>(null)
  const cards = ref<any[]>([])
  const questions = ref<any[]>([])
  const knowledge = ref<any>(null)

  // 派生：当前回合玩家
  const currentPlayer = computed(() =>
    players.value.find(p => p.user_id === turnPlayerId.value) || null
  )
  const isMyTurn = computed(() => {
    if (!isMultiplayer.value) return true
    if (!turnPlayerId.value) return true
    return turnPlayerId.value === playerId.value
  })

  function applyState(s: RoomState | null | undefined) {
    if (!s) return
    roomId.value = s.room_id || roomId.value
    phase.value = s.phase || phase.value
    questionsRemaining.value = s.questions_remaining ?? questionsRemaining.value
    questionsPerPlayer.value = s.questions_per_player || {}
    cardUsage.value = s.card_usage || {}
    perPlayerCardUsage.value = s.per_player_card_usage || {}
    unlockedLayers.value = s.unlocked_layers || []
    negationBoard.value = s.negation_board || []
    questionsLog.value = s.questions_log || []
    cluesLog.value = s.clues_log || []
    comboHistory.value = s.combo_history || []
    players.value = s.players || []
    turnPlayerId.value = s.turn_player_id || ''
    isMultiplayer.value = s.is_multiplayer || false
  }

  function applyStatic(data: any) {
    if (data.cards) cards.value = data.cards
    if (data.questions) questions.value = data.questions
    if (data.knowledge) knowledge.value = data.knowledge
    if (data.script || data.script_info) scriptInfo.value = data.script || data.script_info
  }

  return {
    roomId, playerId, phase, questionsRemaining, questionsPerPlayer,
    cardUsage, perPlayerCardUsage, unlockedLayers, negationBoard,
    questionsLog, cluesLog, comboHistory, players, turnPlayerId,
    isMultiplayer, scriptInfo, cards, questions, knowledge,
    currentPlayer, isMyTurn,
    applyState, applyStatic,
  }
})
