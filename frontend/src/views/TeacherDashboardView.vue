<template>
  <!-- 教师端 Dashboard (P1) -->
  <div class="teacher-dashboard">
    <header class="td-header">
      <div class="td-brand">
        <span class="td-logo">📋</span>
        <h1 class="td-title">教师控制台 · 汤探局</h1>
        <span class="td-subtitle">TANG_DETECTIVE TEACHER CONSOLE</span>
      </div>
      <div class="td-header-actions">
        <el-tag effect="dark" type="success" round>
          {{ teacherId }}
        </el-tag>
        <el-button @click="refreshAll" :loading="loading" type="primary" plain>
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button @click="$router.push('/')" plain>退出</el-button>
      </div>
    </header>

    <!-- 顶部统计卡片 -->
    <section class="td-stats">
      <div class="stat-card stat-active">
        <div class="stat-icon">�</div>
        <div class="stat-body">
          <div class="stat-num">{{ overview.total_rooms || 0 }}</div>
          <div class="stat-label">活跃房间</div>
        </div>
      </div>
      <div class="stat-card stat-students">
        <div class="stat-icon">👨‍🎓</div>
        <div class="stat-body">
          <div class="stat-num">{{ overview.total_students || 0 }}</div>
          <div class="stat-label">在线学生</div>
        </div>
      </div>
      <div class="stat-card stat-layers">
        <div class="stat-icon">🏔️</div>
        <div class="stat-body">
          <div class="stat-num">{{ aggregated.avg_layer_unlocked?.toFixed(1) || '0.0' }}<small>/4</small></div>
          <div class="stat-label">平均解锁层数</div>
        </div>
      </div>
      <div class="stat-card stat-questions">
        <div class="stat-icon">❓</div>
        <div class="stat-body">
          <div class="stat-num">{{ aggregated.avg_questions_used?.toFixed(1) || '0.0' }}</div>
          <div class="stat-label">平均提问次数</div>
        </div>
      </div>
      <div class="stat-card stat-combo">
        <div class="stat-icon">⚔️</div>
        <div class="stat-body">
          <div class="stat-num">{{ aggregated.combo_success_rate?.toFixed(0) || '0' }}<small>%</small></div>
          <div class="stat-label">合技成功率</div>
        </div>
      </div>
    </section>

    <!-- 学生排行榜 -->
    <section class="td-leaderboard">
      <div class="lb-header">
        <h2>🏆 学生排行榜</h2>
        <div class="lb-controls">
          <el-select v-model="leaderboardSortBy" size="small" @change="fetchLeaderboard" style="width: 140px;">
            <el-option label="综合积分" value="total_score" />
            <el-option label="线索最多" value="clues" />
            <el-option label="合技最多" value="combos" />
            <el-option label="错课最少" value="negations" />
            <el-option label="解锁最深" value="layers" />
          </el-select>
          <el-button @click="fetchLeaderboard" :loading="leaderboardLoading" size="small" plain>
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </div>
      <div v-if="leaderboard.rankings.length === 0" class="lb-empty">
        <div class="empty-icon">🎮</div>
        <div class="empty-text">尚无学生数据</div>
        <div class="empty-hint">学生创建房间并参与后会自动出现</div>
      </div>
      <div v-else class="lb-table-wrap">
        <table class="lb-table">
          <thead>
            <tr>
              <th width="60">名次</th>
              <th width="80">奖牌</th>
              <th>学生</th>
              <th width="70">房间</th>
              <th width="70">提问</th>
              <th width="70">线索</th>
              <th width="70">合技</th>
              <th width="70">层数</th>
              <th width="90">积分</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in leaderboard.rankings"
              :key="row.user_id"
              :class="`lb-row rank-${row.rank}`"
            >
              <td class="lb-rank">#{{ row.rank }}</td>
              <td class="lb-badge">{{ row.badge }}</td>
              <td class="lb-name">{{ row.user_name }}</td>
              <td class="lb-room"><code>{{ row.room_id.slice(0, 6) }}</code></td>
              <td>{{ row.questions_asked }}</td>
              <td class="lb-clue">📌 {{ row.clues }}</td>
              <td class="lb-combo">⚔️ {{ row.combos }}</td>
              <td class="lb-layers">🏔️ {{ row.layers_unlocked }}/4</td>
              <td class="lb-score">{{ row.total_score }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 主体内容：左 = 房间列表 + 控制，右 = 考点 + 学情 -->
    <main class="td-main">
      <!-- 左栏：房间列表 + 课堂控制 -->
      <section class="td-panel">
        <div class="panel-header">
          <h2>🏠 房间列表</h2>
          <el-tag size="small">{{ rooms.length }} 个</el-tag>
        </div>
        <div v-if="rooms.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无活跃房间</div>
          <div class="empty-hint">学生创建房间后将自动显示</div>
        </div>
        <div v-else class="room-list">
          <div
            v-for="room in rooms"
            :key="room.room_id"
            class="room-card"
            :class="{ selected: selectedRoomId === room.room_id }"
            @click="selectRoom(room)"
          >
            <div class="room-card-head">
              <div class="room-id">
                <span class="room-tag">房间</span>
                <code>{{ room.room_id.slice(0, 8) }}</code>
              </div>
              <el-tag size="small" :type="phaseType(room.phase)">{{ phaseLabel(room.phase) }}</el-tag>
            </div>
            <div class="room-students">
              <el-avatar
                v-for="p in room.players"
                :key="p.user_id"
                :size="28"
                class="student-avatar"
              >
                {{ p.user_name?.charAt(0) || '?' }}
              </el-avatar>
              <span class="student-count">{{ room.players.length }} 人</span>
            </div>
            <div class="room-progress">
              <div class="progress-row">
                <span>🏔️ 解锁层数</span>
                <strong>{{ room.layers_unlocked }} / 4</strong>
              </div>
              <el-progress
                :percentage="(room.layers_unlocked / 4) * 100"
                :show-text="false"
                :stroke-width="6"
                :color="progressColor"
              />
              <div class="progress-row">
                <span>❓ 提问</span>
                <strong>{{ room.questions_used }}</strong>
                <span style="margin-left:12px">📌 线索</span>
                <strong>{{ room.clues_collected }}</strong>
                <span style="margin-left:12px">⚔️ 合技</span>
                <strong>{{ room.combos_succeeded }}</strong>
              </div>
            </div>
            <div v-if="room.control_state?.paused" class="paused-badge">
              ⏸️ 已暂停
            </div>
          </div>
        </div>

        <!-- 课堂控制面板（选中房间后） -->
        <div v-if="selectedRoom" class="control-panel">
          <div class="panel-header">
            <h2>🎮 课堂控制</h2>
          </div>
          <div class="control-room-info">
            <span class="control-label">当前房间:</span>
            <code class="control-value">{{ selectedRoom.room_id.slice(0, 16) }}</code>
          </div>
          <div class="control-buttons">
            <el-button
              v-if="!selectedRoom.control_state?.paused"
              type="warning"
              @click="pauseRoom"
              :loading="actionLoading.pause"
              block
            >
              ⏸️ 暂停房间
            </el-button>
            <el-button
              v-else
              type="success"
              @click="resumeRoom"
              :loading="actionLoading.resume"
              block
            >
              ▶️ 恢复房间
            </el-button>
          </div>

          <div class="broadcast-area">
            <div class="broadcast-label">📢 广播消息（学生端弹 toast）</div>
            <el-input
              v-model="broadcastText"
              type="textarea"
              :rows="2"
              placeholder="例如：请大家注意，毛细现象的考点即将出现..."
            />
            <el-button
              type="primary"
              @click="broadcastMessage"
              :loading="actionLoading.broadcast"
              :disabled="!broadcastText.trim()"
              block
              style="margin-top:8px"
            >
              📡 广播给全班
            </el-button>
          </div>

          <div class="kick-area">
            <div class="broadcast-label">🚪 踢出学生</div>
            <el-select v-model="kickUserId" placeholder="选择学生" style="width:100%">
              <el-option
                v-for="p in selectedRoom.players"
                :key="p.user_id"
                :label="`${p.user_name} (${p.user_id.slice(0,6)})`"
                :value="p.user_id"
              />
            </el-select>
            <el-button
              type="danger"
              @click="kickStudent"
              :loading="actionLoading.kick"
              :disabled="!kickUserId"
              block
              style="margin-top:8px"
            >
              ⚠️ 踢出该学生
            </el-button>
          </div>
        </div>
      </section>

      <!-- 中栏：考点统计 -->
      <section class="td-panel">
        <div class="panel-header">
          <h2>📚 14 个考点掌握率</h2>
          <el-tag size="small" type="info">实时统计</el-tag>
        </div>
        <div class="kp-grid">
          <div
            v-for="kp in kpCatalog"
            :key="kp.name"
            class="kp-card"
            :class="`kp-${kp.status === '已掌握' ? 'mastered' : kp.status === '待加强' ? 'partial' : 'weak'}`"
          >
            <div class="kp-card-head">
              <span class="kp-subject" :style="{background: kp.subject_color}">
                {{ kp.subject }}
              </span>
              <el-tag size="small" :type="kp.weight === '必考' ? 'danger' : 'warning'">
                {{ kp.weight }}
              </el-tag>
            </div>
            <div class="kp-name">{{ kp.name }}</div>
            <div class="kp-progress-row">
              <span>班级掌握率</span>
              <strong>{{ kp.class_mastery_pct }}%</strong>
            </div>
            <el-progress
              :percentage="kp.class_mastery_pct"
              :stroke-width="10"
              :color="kpProgressColor"
              :format="() => ''"
            />
            <div class="kp-stats-row">
              <span>✅ 命中 {{ kp.class_hits }}</span>
              <span>❌ 未达 {{ kp.class_misses }}</span>
            </div>
            <div class="kp-status">
              <span v-if="kp.status === '已掌握'" class="badge-ok">✓ 已掌握</span>
              <span v-else-if="kp.status === '待加强'" class="badge-warn">⚠ 待加强</span>
              <span v-else class="badge-weak">✗ 未达标</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 右栏：学情画像 + 热力图 -->
      <section class="td-panel">
        <div class="panel-header">
          <h2>👥 学情画像</h2>
        </div>

        <div v-if="!selectedRoom" class="empty-state">
          <div class="empty-icon">👈</div>
          <div class="empty-text">请先选择左侧房间</div>
        </div>

        <div v-else-if="studentsInRoom.length === 0" class="empty-state">
          <div class="empty-icon">👻</div>
          <div class="empty-text">房间暂无学生</div>
        </div>

        <div v-else>
          <el-tabs v-model="activeStudentIdx" type="card">
            <el-tab-pane
              v-for="(s, idx) in studentsInRoom"
              :key="s.user_id"
              :label="s.user_name"
              :name="String(idx)"
            />
          </el-tabs>

          <div v-if="currentStudentProfile" class="student-profile">
            <div class="profile-head">
              <el-avatar :size="48" class="profile-avatar">
                {{ currentStudentProfile.user_name?.charAt(0) }}
              </el-avatar>
              <div>
                <div class="profile-name">{{ currentStudentProfile.user_name }}</div>
                <div class="profile-meta">
                  <el-tag size="small">{{ currentStudentProfile.thinking_style }}</el-tag>
                </div>
              </div>
            </div>

            <div class="profile-stats">
              <div class="ps-item">
                <div class="ps-num">{{ currentStudentProfile.stats.questions_asked }}</div>
                <div class="ps-label">提问</div>
              </div>
              <div class="ps-item">
                <div class="ps-num">{{ currentStudentProfile.stats.clues_found }}</div>
                <div class="ps-label">线索</div>
              </div>
              <div class="ps-item">
                <div class="ps-num">{{ currentStudentProfile.stats.negations }}</div>
                <div class="ps-label">否决</div>
              </div>
              <div class="ps-item">
                <div class="ps-num">{{ currentStudentProfile.stats.combos_succeeded }}</div>
                <div class="ps-label">合技</div>
              </div>
              <div class="ps-item">
                <div class="ps-num">{{ currentStudentProfile.stats.cards_used }}<small>/{{ currentStudentProfile.stats.cards_total }}</small></div>
                <div class="ps-label">用卡</div>
              </div>
            </div>

            <h3 class="profile-h3">🎯 能力雷达（5 维）</h3>
            <div class="ability-radar">
              <div
                v-for="(score, key) in currentStudentProfile.ability_radar"
                :key="key"
                class="ability-bar"
              >
                <span class="ability-label">{{ key }}</span>
                <el-progress
                  :percentage="score"
                  :stroke-width="14"
                  :color="radarColor(score)"
                  :format="(p) => `${p.toFixed(0)}`"
                />
              </div>
            </div>

            <h3 class="profile-h3">⚠️ 否决模式（最近 10 条）</h3>
            <div v-if="currentStudentProfile.negation_patterns.length === 0" class="no-data">
              没有否决记录，太棒了！
            </div>
            <div v-else class="negation-list">
              <div
                v-for="(n, i) in currentStudentProfile.negation_patterns"
                :key="i"
                class="negation-item"
              >
                <el-tag size="small" type="danger">{{ n.category }}</el-tag>
                <span class="negation-text">{{ n.text }}</span>
                <el-tag v-if="n.layer" size="small" type="info">{{ n.layer }}</el-tag>
              </div>
            </div>

            <h3 class="profile-h3">🔥 答题热力图</h3>
            <div class="heatmap">
              <div
                v-for="s in heatmapData.students"
                :key="s.user_id"
                class="heat-row"
              >
                <span class="heat-name">{{ s.user_name || '匿名' }}</span>
                <div class="heat-bars">
                  <div class="heat-bar heat-q" :style="{flex: s.questions || 0}">
                    ❓ {{ s.questions || 0 }}
                  </div>
                  <div class="heat-bar heat-c" :style="{flex: s.clues || 0}">
                    📌 {{ s.clues || 0 }}
                  </div>
                  <div class="heat-bar heat-n" :style="{flex: s.negations || 0}">
                    ❌ {{ s.negations || 0 }}
                  </div>
                  <div class="heat-bar heat-b" :style="{flex: s.combos || 0}">
                    ⚔️ {{ s.combos || 0 }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="heatmapData.stuck_students?.length" class="stuck-warning">
              <h3 class="profile-h3">🚨 卡住的学生（需要引导）</h3>
              <div
                v-for="s in heatmapData.stuck_students"
                :key="s.user_id"
                class="stuck-item"
              >
                <strong>{{ s.user_name }}</strong>
                <span>{{ s.suggestion }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="td-footer">
      <span>汤探局 · 教师控制台 · P1 教学设计加分项</span>
      <span>最后更新: {{ lastUpdate }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const teacherId = ref(`T-${Math.random().toString(36).slice(2, 8).toUpperCase()}`)
const loading = ref(false)
const lastUpdate = ref('—')

const overview = ref<any>({})
const rooms = ref<any[]>([])
const kpCatalog = ref<any[]>([])
const selectedRoomId = ref('')

// 排行榜状态
const leaderboard = ref<any>({ rankings: [], total_students: 0, sort_by: 'total_score' })
const leaderboardSortBy = ref('total_score')
const leaderboardLoading = ref(false)
const selectedRoom = ref<any>(null)
const currentStudentProfile = ref<any>(null)
const heatmapData = ref<any>({ students: {}, stuck_students: [] })

const activeStudentIdx = ref('0')
const studentsInRoom = computed(() => selectedRoom.value?.players || [])

const broadcastText = ref('')
const kickUserId = ref('')

const actionLoading = ref({
  pause: false,
  resume: false,
  broadcast: false,
  kick: false,
})

const aggregated = computed(() => overview.value?.aggregated || {})

// ---- API ----
const API_BASE = (typeof window !== 'undefined' && (window as any).__TEACHER_API) ||
                 ''

async function fetchOverview() {
  try {
    const r = await axios.get(`${API_BASE}/api/teacher/overview`, {
      params: { teacher_id: teacherId.value, _t: Date.now() },
      headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
    })
    overview.value = r.data
    rooms.value = r.data.rooms_detail || []
    lastUpdate.value = new Date().toLocaleTimeString()
  } catch (e) {
    console.error('teacher overview fetch failed:', e)
    // 静默失败：避免频繁弹窗，下一次定时刷新会重试
  }
}

async function fetchKpCatalog() {
  try {
    const r = await axios.get(`${API_BASE}/api/teacher/kp_catalog`, {
      params: { _t: Date.now() },
      headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
    })
    kpCatalog.value = r.data
  } catch (e) {
    console.error(e)
  }
}

async function selectRoom(room: any) {
  selectedRoomId.value = room.room_id
  selectedRoom.value = room
  activeStudentIdx.value = '0'
  kickUserId.value = ''
  broadcastText.value = ''
  await fetchStudentProfile(room.room_id, room.players[0]?.user_id)
  await fetchHeatmap(room.room_id)
}

async function fetchStudentProfile(roomId: string, userId: string) {
  if (!userId) {
    currentStudentProfile.value = null
    return
  }
  try {
    const r = await axios.get(`${API_BASE}/api/teacher/student/${roomId}/${userId}`, {
      params: { _t: Date.now() },
      headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
    })
    currentStudentProfile.value = r.data
  } catch (e) {
    console.error(e)
    currentStudentProfile.value = null
  }
}

async function fetchHeatmap(roomId: string) {
  try {
    const r = await axios.get(`${API_BASE}/api/teacher/heatmap/${roomId}`, {
      params: { _t: Date.now() },
      headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
    })
    heatmapData.value = r.data
  } catch (e) {
    console.error(e)
  }
}

async function refreshAll() {
  loading.value = true
  await Promise.all([fetchOverview(), fetchKpCatalog(), fetchLeaderboard()])
  if (selectedRoomId.value) {
    await Promise.all([
      fetchStudentProfile(selectedRoomId.value, selectedRoom.value?.players[0]?.user_id),
      fetchHeatmap(selectedRoomId.value)
    ])
  }
  loading.value = false
}

async function fetchLeaderboard() {
  leaderboardLoading.value = true
  try {
    const r = await axios.get(`${API_BASE}/api/teacher/leaderboard`, {
      params: { sort_by: leaderboardSortBy.value, _t: Date.now() },
      headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
    })
    leaderboard.value = r.data
  } catch (e) {
    console.error(e)
    leaderboard.value = { rankings: [], total_students: 0, sort_by: leaderboardSortBy.value }
  } finally {
    leaderboardLoading.value = false
  }
}

// ---- 课堂控制 ----
async function pauseRoom() {
  if (!selectedRoom.value) return
  actionLoading.value.pause = true
  try {
    const r = await axios.post(`${API_BASE}/api/teacher/pause/${selectedRoom.value.room_id}`, {
      teacher_id: teacherId.value,
    })
    if (r.data.ok) {
      ElMessage.success('房间已暂停')
      await refreshAll()
    }
  } finally {
    actionLoading.value.pause = false
  }
}

async function resumeRoom() {
  if (!selectedRoom.value) return
  actionLoading.value.resume = true
  try {
    const r = await axios.post(`${API_BASE}/api/teacher/resume/${selectedRoom.value.room_id}`, {
      teacher_id: teacherId.value,
    })
    if (r.data.ok) {
      ElMessage.success('房间已恢复')
      await refreshAll()
    }
  } finally {
    actionLoading.value.resume = false
  }
}

async function broadcastMessage() {
  if (!selectedRoom.value || !broadcastText.value.trim()) return
  actionLoading.value.broadcast = true
  try {
    const r = await axios.post(`${API_BASE}/api/teacher/broadcast/${selectedRoom.value.room_id}`, {
      teacher_id: teacherId.value,
      message: broadcastText.value.trim(),
    })
    if (r.data.ok) {
      ElMessage.success('消息已广播')
      broadcastText.value = ''
      await refreshAll()
    }
  } finally {
    actionLoading.value.broadcast = false
  }
}

async function kickStudent() {
  if (!selectedRoom.value || !kickUserId.value) return
  try {
    await ElMessageBox.confirm(
      `确认踢出学生 ${kickUserId.value.slice(0, 8)}？`,
      '课堂纪律管理',
      { confirmButtonText: '确认踢出', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  actionLoading.value.kick = true
  try {
    const r = await axios.post(`${API_BASE}/api/teacher/kick/${selectedRoom.value.room_id}`, {
      teacher_id: teacherId.value,
      user_id: kickUserId.value,
    })
    if (r.data.ok) {
      ElMessage.success(`已踢出学生`)
      kickUserId.value = ''
      await refreshAll()
    }
  } finally {
    actionLoading.value.kick = false
  }
}

// ---- 切换学生 ----
import { watch } from 'vue'
watch(activeStudentIdx, async (idx) => {
  if (!selectedRoom.value) return
  const student = selectedRoom.value.players[parseInt(idx)]
  if (student) {
    await fetchStudentProfile(selectedRoom.value.room_id, student.user_id)
  }
})

// ---- 工具 ----
function phaseType(phase: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, any> = {
    lobby: 'info',
    intro: 'primary',
    questioning: 'warning',
    card_play: 'warning',
    reveal: 'success',
    debrief: 'success',
    extend: 'primary',
    end: 'info',
  }
  return map[phase] || 'info'
}

function phaseLabel(phase: string): string {
  const map: Record<string, string> = {
    lobby: '大厅',
    intro: '导入',
    questioning: '提问',
    card_play: '出卡',
    reveal: '揭晓',
    debrief: '复盘',
    extend: '拓展',
    end: '结束',
  }
  return map[phase] || phase
}

function progressColor(percentage: number): string {
  if (percentage >= 75) return '#67C23A'
  if (percentage >= 50) return '#E6A23C'
  return '#F56C6C'
}

function kpProgressColor(percentage: number): string {
  if (percentage >= 70) return '#67C23A'
  if (percentage >= 40) return '#E6A23C'
  return '#F56C6C'
}

function radarColor(score: number): string {
  if (score >= 70) return '#67C23A'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

// ---- 生命周期 ----
let timer: any = null
onMounted(() => {
  refreshAll()
  timer = setInterval(refreshAll, 5000)  // 每 5 秒自动刷新
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.teacher-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%);
  padding: 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* Header */
.td-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
  color: white;
  padding: 16px 24px;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px rgba(30, 58, 95, 0.2);
}
.td-brand {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.td-logo {
  font-size: 28px;
}
.td-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
}
.td-subtitle {
  font-size: 11px;
  color: #cbd5e0;
  letter-spacing: 2px;
}
.td-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Stats */
.td-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  padding: 16px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border-left: 4px solid #409eff;
  transition: all 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}
.stat-active { border-left-color: #409eff; }
.stat-students { border-left-color: #67c23a; }
.stat-layers { border-left-color: #e6a23c; }
.stat-questions { border-left-color: #f56c6c; }
.stat-combo { border-left-color: #909399; }

.stat-icon {
  font-size: 32px;
  opacity: 0.85;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.stat-num small {
  font-size: 14px;
  color: #909399;
  font-weight: 400;
}
.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* 排行榜 */
.td-leaderboard {
  background: white;
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}
.lb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f4f8;
}
.lb-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}
.lb-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}
.lb-empty {
  text-align: center;
  padding: 32px 16px;
  color: #909399;
}
.lb-empty .empty-icon {
  font-size: 48px;
  opacity: 0.5;
}
.lb-empty .empty-text {
  font-size: 14px;
  margin-top: 8px;
  color: #606266;
}
.lb-empty .empty-hint {
  font-size: 12px;
  margin-top: 4px;
  color: #c0c4cc;
}
.lb-table-wrap {
  overflow-x: auto;
}
.lb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.lb-table thead {
  background: #f5f7fa;
}
.lb-table th {
  padding: 10px 8px;
  text-align: center;
  color: #606266;
  font-weight: 600;
  border-bottom: 2px solid #e4e7ed;
  white-space: nowrap;
}
.lb-table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  color: #303133;
}
.lb-row {
  transition: background 0.2s;
}
.lb-row:hover {
  background: #f5f7fa;
}
.lb-row.rank-1 {
  background: linear-gradient(90deg, #fff8e1 0%, #ffffff 100%);
  font-weight: 600;
}
.lb-row.rank-2 {
  background: linear-gradient(90deg, #f5f7fa 0%, #ffffff 100%);
}
.lb-row.rank-3 {
  background: linear-gradient(90deg, #fef0f0 0%, #ffffff 100%);
}
.lb-rank {
  font-weight: 700;
  color: #d4a574;
  font-size: 14px;
}
.lb-row.rank-1 .lb-rank {
  color: #c79100;
}
.lb-badge {
  font-size: 20px;
}
.lb-name {
  text-align: left !important;
  font-weight: 500;
  color: #303133;
  padding-left: 12px !important;
}
.lb-room code {
  font-size: 11px;
  font-family: monospace;
  background: #fafbfc;
  padding: 2px 6px;
  border-radius: 3px;
  color: #909399;
}
.lb-clue, .lb-combo, .lb-layers {
  font-size: 12px;
}
.lb-score {
  font-size: 16px;
  font-weight: 700;
  color: #409eff;
}
.lb-row.rank-1 .lb-score {
  color: #c79100;
  font-size: 18px;
}

/* Main grid */
.td-main {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 16px;
  min-height: 600px;
}

/* Panel */
.td-panel {
  background: white;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f4f8;
}
.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: #909399;
}
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}
.empty-text {
  font-size: 14px;
  margin-top: 8px;
}
.empty-hint {
  font-size: 12px;
  margin-top: 4px;
  color: #c0c4cc;
}

/* Room list */
.room-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}
.room-card {
  padding: 12px;
  background: #fafbfc;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.room-card:hover {
  background: #f0f4f8;
  border-color: #409eff;
}
.room-card.selected {
  background: #ecf5ff;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64,158,255,0.2);
}
.room-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.room-id {
  display: flex;
  align-items: center;
  gap: 6px;
}
.room-tag {
  font-size: 10px;
  background: #909399;
  color: white;
  padding: 1px 6px;
  border-radius: 3px;
}
.room-id code {
  font-size: 12px;
  font-family: monospace;
  color: #606266;
}
.room-students {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}
.student-avatar {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
}
.student-count {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}
.room-progress {
  font-size: 12px;
  color: #606266;
}
.progress-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 4px 0;
}
.progress-row strong {
  color: #303133;
}
.paused-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: #e6a23c;
  color: white;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

/* Control panel */
.control-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px solid #f0f4f8;
}
.control-room-info {
  background: #fafbfc;
  padding: 8px 10px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 12px;
}
.control-label {
  color: #909399;
  margin-right: 6px;
}
.control-value {
  font-family: monospace;
  color: #303133;
  font-weight: 600;
}
.control-buttons {
  margin-bottom: 12px;
}
.broadcast-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  font-weight: 500;
}
.broadcast-area, .kick-area {
  margin-bottom: 12px;
}

/* KP grid */
.kp-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-height: 600px;
  overflow-y: auto;
}
.kp-card {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: #fafbfc;
}
.kp-card.kp-mastered {
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  border-color: #b3e19d;
}
.kp-card.kp-partial {
  background: linear-gradient(135deg, #fdf6ec 0%, #faecd8 100%);
  border-color: #f3d19e;
}
.kp-card.kp-weak {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  border-color: #fbc4c4;
}
.kp-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.kp-subject {
  color: white;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.kp-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
  line-height: 1.4;
}
.kp-progress-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}
.kp-progress-row strong {
  color: #303133;
  font-size: 13px;
}
.kp-stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}
.kp-status {
  margin-top: 6px;
  text-align: center;
}
.badge-ok {
  color: #67c23a;
  font-size: 12px;
  font-weight: 600;
}
.badge-warn {
  color: #e6a23c;
  font-size: 12px;
  font-weight: 600;
}
.badge-weak {
  color: #f56c6c;
  font-size: 12px;
  font-weight: 600;
}

/* Student profile */
.profile-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.profile-avatar {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
  font-weight: 700;
}
.profile-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.profile-meta {
  margin-top: 4px;
}
.profile-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}
.ps-item {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 6px;
  text-align: center;
}
.ps-num {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}
.ps-num small {
  font-size: 11px;
  color: #909399;
  font-weight: 400;
}
.ps-label {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}
.profile-h3 {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin: 12px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px dashed #e4e7ed;
}
.ability-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.ability-label {
  width: 70px;
  font-size: 12px;
  color: #606266;
}
.negation-list {
  max-height: 200px;
  overflow-y: auto;
}
.negation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
  font-size: 12px;
}
.negation-text {
  flex: 1;
  color: #606266;
}
.no-data {
  font-size: 12px;
  color: #67c23a;
  text-align: center;
  padding: 16px;
  background: #f0f9eb;
  border-radius: 6px;
}

.heatmap {
  background: #fafbfc;
  padding: 10px;
  border-radius: 6px;
}
.heat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.heat-name {
  width: 80px;
  font-size: 12px;
  color: #606266;
}
.heat-bars {
  flex: 1;
  display: flex;
  gap: 4px;
  height: 24px;
}
.heat-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  border-radius: 3px;
  padding: 0 6px;
  min-width: 30px;
}
.heat-q { background: #409eff; }
.heat-c { background: #67c23a; }
.heat-n { background: #f56c6c; }
.heat-b { background: #e6a23c; }

.stuck-warning {
  margin-top: 12px;
  padding: 10px;
  background: #fef0f0;
  border-radius: 6px;
  border-left: 3px solid #f56c6c;
}
.stuck-item {
  display: flex;
  flex-direction: column;
  padding: 6px 0;
  font-size: 12px;
  color: #606266;
}
.stuck-item strong {
  color: #f56c6c;
  margin-bottom: 2px;
}

.td-footer {
  margin-top: 16px;
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}

/* 响应式 */
@media (max-width: 1280px) {
  .td-main {
    grid-template-columns: 280px 1fr 340px;
  }
  .td-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 768px) {
  .td-main {
    grid-template-columns: 1fr;
  }
}
</style>