import { createRouter, createWebHistory } from 'vue-router'
import LandingView from './views/LandingView.vue'
import IntroView from './views/IntroView.vue'
import PlayView from './views/PlayView.vue'
import DebriefView from './views/DebriefView.vue'
import LearnView from './views/LearnView.vue'
import ChallengeView from './views/ChallengeView.vue'
import TeacherDashboardView from './views/TeacherDashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: LandingView },              // ⭐ 门面页（教师/学生分流）
    { path: '/intro', component: IntroView },          // 学生端：进入游戏
    { path: '/play/:roomId', component: PlayView },
    { path: '/debrief/:roomId', component: DebriefView },
    { path: '/learn/:kpId', component: LearnView },
    { path: '/challenge/:roomId', component: ChallengeView },
    { path: '/teacher', component: TeacherDashboardView },  // 教师端 Dashboard
  ]
})

export default router
