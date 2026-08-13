import { createRouter, createWebHistory } from 'vue-router'
import IntroView from './views/IntroView.vue'
import PlayView from './views/PlayView.vue'
import DebriefView from './views/DebriefView.vue'
import LearnView from './views/LearnView.vue'
import ChallengeView from './views/ChallengeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: IntroView },
    { path: '/play/:roomId', component: PlayView },
    { path: '/debrief/:roomId', component: DebriefView },
    { path: '/learn/:kpId', component: LearnView },
    { path: '/challenge/:roomId', component: ChallengeView },
  ]
})

export default router
