/**
 * 汤探局 - 前后端共享类型定义 (P2 #21)
 *
 * 这些类型是从 backend/data/*.json 派生出来的。
 * 字段顺序与 JSON 保持一致，方便对照。
 *
 * 后端只负责校验，不直接 emit TypeScript。
 * 这里手写是因为数据量小，且字段变化 schema 必变。
 */

export interface IntroCard {
  title: string
  subtitle: string
  case_type: string
  case_label: string
  case_class: string
  core_knowledge: string[]
  knowledge_tag: string
  tip: string
  warning: string
}

export interface Layer {
  id: number
  name: string
  icon: string
  color: string
  unlock_combo: string
  unlock_cards: string[]
  reveal_text: string
  bloom_level: string
}

export interface CardClue {
  id: string
  label: string
  content: string
  knowledge_point: string
}

export interface Card {
  id: string
  name: string
  title: string
  category: string
  skill_name: string
  skill_text: string
  subject: string
  max_use: number
  combo_partner?: string
  combo_unlock_layer?: string
  badge_icon: string
  exam_tags: string[]
  clues: CardClue[]
}

export interface Question {
  id: string
  category: string
  text: string
  knowledge_point: string
  // 以下字段仅在 reveal=true 时由后端返回
  answer?: string
  hint?: string
  suggested_card?: string
}

export interface Script {
  id: string
  version: string
  case_title: string
  subtitle: string
  category: string
  grade_level: string
  duration_minutes: number
  max_questions: number
  max_card_usage: number
  knowledge_points_summary: string
  scene: string
  intro_card: IntroCard
  layers: Record<string, Layer>
  layers_order?: string[]
}

export interface Player {
  user_id: string
  user_name: string
}

export interface QARecord {
  id: string
  category: string
  text: string
  answer: string
  knowledge_point: string
  player_id: string
}

export interface ClueRecord {
  clue_id: string
  card_id: string
  label: string
  content: string
  knowledge_point: string
  layer?: string | null
  player_id: string
}

export interface NegationRecord {
  id: string
  text: string
  answer: string
  knowledge_point: string
  player_id: string
}

export interface RoomState {
  room_id: string
  players: Player[]
  phase: string
  questions_remaining: number
  questions_per_player: Record<string, number>
  card_usage: Record<string, number>
  per_player_card_usage: Record<string, Record<string, number>>
  unlocked_layers: string[]
  is_multiplayer: boolean
  turn_player_id: string
  current_player?: Player
  other_player?: Player | null
  negation_board: NegationRecord[]
  questions_log: QARecord[]
  clues_log: ClueRecord[]
  combo_history: any[]
}

/** 后端 API 统一响应包装 */
export interface ApiResponse<T = any> {
  ok: boolean
  error?: string
  [key: string]: any
}
