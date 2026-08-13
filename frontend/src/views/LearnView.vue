<template>
  <div class="learn-page">
    <header class="lp-header" :style="{ background: gradientFor(point?.subject_color) }">
      <div class="lp-header-inner">
        <el-button class="back-btn" @click="$router.back()" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="lp-title-wrap" v-if="point">
          <div class="lp-subject-row">
            <span class="lp-subject-icon">{{ point.subject_icon }}</span>
            <span class="lp-subject-name">{{ point.subject }}</span>
            <span class="lp-exam-weight">{{ point.exam_weight }}</span>
          </div>
          <h1 class="lp-title">{{ point.title }}</h1>
          <p class="lp-summary">{{ point.summary }}</p>
        </div>
        <div class="lp-title-wrap" v-else>
          <h1 class="lp-title">📚 知识点未找到</h1>
          <p class="lp-summary">未匹配到对应的知识点内容。识别字符串：<code>{{ kpId }}</code></p>
        </div>
      </div>
    </header>

    <div class="lp-content" v-if="point">
      <el-row :gutter="24">
        <el-col :span="17">
          <article class="lp-article">
            <div v-if="isLayer" class="lp-combo-banner">
              <el-icon><MagicStick /></el-icon>
              <span class="lp-combo-label">触发合技</span>
              <strong>{{ (point as any).combo }}</strong>
              <span class="lp-combo-name">（{{ (point as any).combo_name }}）</span>
            </div>
            <section
              v-for="(s, idx) in point.sections"
              :key="idx"
              class="lp-section"
              :id="`section-${idx}`"
            >
              <h2 class="lp-section-heading">
                <span class="lp-section-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                {{ s.heading }}
              </h2>
              <div class="lp-section-body" v-html="formatContent(s.content)"></div>
            </section>
          </article>
        </el-col>

        <el-col :span="7">
          <aside class="lp-sidebar">
            <div class="lp-card" v-if="point.key_terms?.length">
              <h3 class="lp-card-title">📖 关键术语</h3>
              <ul class="kp-term-list">
                <li v-for="t in point.key_terms" :key="t.term" class="kp-term-item">
                  <div class="kp-term-name">{{ t.term }}</div>
                  <div class="kp-term-def">{{ t.def }}</div>
                </li>
              </ul>
            </div>

            <div class="lp-card">
              <h3 class="lp-card-title">🧭 章节导航</h3>
              <ul class="kp-nav-list">
                <li v-for="(s, idx) in point.sections" :key="idx">
                  <a :href="`#section-${idx}`" @click.prevent="scrollTo(`section-${idx}`)">
                    <span class="kp-nav-num">{{ idx + 1 }}</span>
                    {{ s.heading }}
                  </a>
                </li>
              </ul>
            </div>

            <div class="lp-card lp-meta-card">
              <h3 class="lp-card-title">ℹ️ 学习信息</h3>
              <div class="lp-meta-row"><span>{{ isLayer ? '合技名称' : '学科' }}</span><strong>{{ isLayer ? (point as any).combo_name : point.subject }}</strong></div>
              <div class="lp-meta-row" v-if="!isLayer"><span>考点权重</span><strong>{{ point.exam_weight }}</strong></div>
              <div class="lp-meta-row"><span>章节数</span><strong>{{ point.sections.length }}</strong></div>
              <div class="lp-meta-row"><span>术语数</span><strong>{{ point.key_terms?.length || 0 }}</strong></div>
              <div class="lp-meta-row" v-if="isLayer"><span>关联武将</span><strong>{{ (point as any).combo }}</strong></div>
            </div>
          </aside>
        </el-col>
      </el-row>
    </div>

    <div v-else class="lp-not-found">
      <el-empty description="没有这个知识点的详细讲解">
        <el-button type="primary" @click="$router.back()">返回上一页</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { findAnyLearnPoint, learnLayers } from '../composables/learnData'

const route = useRoute()
// Decode UTF-8 percent-encoded route param (Chinese chars)
const kpId = computed(() => {
  const raw = route.params.kpId as string
  try { return decodeURIComponent(raw) } catch { return raw }
})
const point = computed(() => findAnyLearnPoint(kpId.value))
const isLayer = computed(() => learnLayers.some(l => l.id === kpId.value))

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function gradientFor(color?: string) {
  const c = color || '#5d4037'
  return `linear-gradient(135deg, ${c} 0%, ${c}dd 50%, ${c}99 100%)`
}

function formatContent(text: string): string {
  if (!text) return ''
  // 1. escape HTML
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 2. **bold** -> <strong>
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 3. *italic* -> <em>
  html = html.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
  // 4. \n\n -> paragraph break
  const paragraphs = html.split(/\n\n+/).map(p => p.trim()).filter(Boolean)
  return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br/>')}</p>`).join('')
}
</script>

<style scoped>
.learn-page {
  min-height: 100vh;
  background: #faf6ef;
}

.lp-header {
  color: #fff;
  padding: 30px 0 40px;
  position: relative;
  overflow: hidden;
}
.lp-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.15) 0%, transparent 50%);
  pointer-events: none;
}
.lp-header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 30px;
  position: relative;
}
.back-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: #fff;
  margin-bottom: 20px;
}
.back-btn:hover {
  background: rgba(255,255,255,0.3);
  border-color: rgba(255,255,255,0.5);
}
.lp-title-wrap {
  max-width: 800px;
}
.lp-subject-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 14px;
}
.lp-subject-icon {
  font-size: 24px;
}
.lp-subject-name {
  background: rgba(255,255,255,0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
}
.lp-exam-weight {
  background: rgba(255,255,255,0.3);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}
.lp-title {
  font-size: 36px;
  margin: 0 0 12px;
  font-weight: 700;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.15);
}
.lp-summary {
  font-size: 16px;
  line-height: 1.7;
  margin: 0;
  opacity: 0.95;
  max-width: 700px;
}

.lp-content {
  max-width: 1200px;
  margin: -20px auto 40px;
  padding: 0 30px;
  position: relative;
  z-index: 1;
}

.lp-combo-banner {
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
  border-left: 4px solid #e6a23c;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #b8875a;
}
.lp-combo-label {
  font-size: 11px;
  letter-spacing: 1px;
  color: #909399;
  background: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #e6a23c;
}
.lp-combo-name {
  color: #909399;
  font-size: 13px;
}

.lp-article {
  background: #fff;
  border-radius: 12px;
  padding: 36px 44px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.lp-section {
  padding-bottom: 28px;
  margin-bottom: 28px;
  border-bottom: 1px dashed #e8e0d0;
}
.lp-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}
.lp-section-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 22px;
  color: #5d4037;
  margin: 0 0 16px;
  font-weight: 700;
}
.lp-section-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #d4a574, #b8875a);
  color: #fff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  font-family: 'Georgia', serif;
}
.lp-section-body {
  font-size: 15px;
  line-height: 1.9;
  color: #3d3530;
}
.lp-section-body :deep(p) {
  margin: 0 0 14px;
}
.lp-section-body :deep(strong) {
  color: #5d4037;
  background: linear-gradient(transparent 60%, #fde6c8 60%);
  padding: 0 2px;
}
.lp-section-body :deep(em) {
  color: #b8875a;
  font-style: italic;
}
.lp-section-body :deep(code) {
  background: #faf6ef;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Cascadia Code', 'Consolas', monospace;
  font-size: 13px;
  color: #b8875a;
  border: 1px solid #e8e0d0;
}

.lp-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.lp-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.lp-card-title {
  margin: 0 0 14px;
  font-size: 14px;
  color: #5d4037;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
}

.kp-term-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.kp-term-item {
  padding: 8px 0;
  border-bottom: 1px dashed #f0e8d8;
}
.kp-term-item:last-child {
  border-bottom: none;
}
.kp-term-name {
  font-size: 13px;
  font-weight: 700;
  color: #b8875a;
  margin-bottom: 4px;
}
.kp-term-def {
  font-size: 12px;
  color: #5a4a3f;
  line-height: 1.6;
}

.kp-nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.kp-nav-list li a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  color: #5d4037;
  font-size: 13px;
  text-decoration: none;
  transition: all 0.2s;
}
.kp-nav-list li a:hover {
  background: #faf6ef;
  color: #b8875a;
}
.kp-nav-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: #faf6ef;
  color: #b8875a;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}
.kp-nav-list li a:hover .kp-nav-num {
  background: #b8875a;
  color: #fff;
}

.lp-meta-card .lp-meta-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px dashed #f0e8d8;
}
.lp-meta-card .lp-meta-row:last-child {
  border-bottom: none;
}
.lp-meta-card .lp-meta-row span {
  color: #909399;
}
.lp-meta-card .lp-meta-row strong {
  color: #5d4037;
  text-align: right;
}

.lp-not-found {
  max-width: 600px;
  margin: 60px auto;
  padding: 0 20px;
}

@media (max-width: 992px) {
  .lp-content .el-col {
    margin-bottom: 20px;
  }
  .lp-article {
    padding: 24px 20px;
  }
  .lp-title {
    font-size: 28px;
  }
  .lp-section-heading {
    font-size: 18px;
  }
}

@media print {
  .lp-sidebar, .back-btn, .lp-combo-banner { display: none !important; }
  .lp-article { box-shadow: none !important; border: 1px solid #d4a574 !important; }
}
</style>
