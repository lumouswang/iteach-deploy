import learnContent from '../data/learn_content.json'

export interface LearnPoint {
  id: string
  title: string
  subject: string
  subject_icon: string
  subject_color: string
  exam_weight: string
  summary: string
  sections: { heading: string; content: string }[]
  key_terms: { term: string; def: string }[]
}

export interface LearnLayer {
  id: string
  key: string
  title: string
  subject: string
  subject_icon: string
  subject_color: string
  exam_weight: string
  combo: string
  combo_name: string
  summary: string
  sections: { heading: string; content: string }[]
  key_terms: { term: string; def: string }[]
}

export const learnPoints: LearnPoint[] = learnContent.points as LearnPoint[]
export const learnLayers: LearnLayer[] = learnContent.layers as LearnLayer[]

const KP_INDEX = new Map(learnPoints.map(p => [p.id, p]))
const LAYER_INDEX = new Map(learnLayers.map(l => [l.id, l]))

// P2 修复：布鲁姆层级中文标签 → 组合技层 id 的容错映射
// 即使后端某处把 "识记" 当成 knowledge_point 传过来，前端也能解析到正确的层详情页
const BLOOM_TO_LAYER: Record<string, string> = {
  '识记': 'phenomenon',
  '理解': 'condition',
  '分析': 'microscopic',
  '评价': 'ultimate',
  '创造': 'ultimate',
}

/** Find a learning point by its clue knowledge_point string. */
export function findLearnPoint(kpName: string): LearnPoint | undefined {
  return KP_INDEX.get(kpName)
}

/** Find a combo / layer learning entry by layer id (phenomenon/condition/microscopic/ultimate). */
export function findLayerPoint(layerId: string): LearnLayer | undefined {
  return LAYER_INDEX.get(layerId)
}

/** Lookup entry that decides whether a :kpId route param refers to a clue KP or a combo layer. */
export function findAnyLearnPoint(kpOrLayerId: string): LearnPoint | LearnLayer | undefined {
  return (
    KP_INDEX.get(kpOrLayerId) ||
    LAYER_INDEX.get(kpOrLayerId) ||
    LAYER_INDEX.get(BLOOM_TO_LAYER[kpOrLayerId] || '') ||
    undefined
  )
}
