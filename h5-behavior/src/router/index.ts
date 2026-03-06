import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory('/behavior/'),
  routes: [
    { path: '/',            name: 'landing',      component: () => import('@/views/Landing.vue') },
    { path: '/concern',     name: 'concern',      component: () => import('@/views/Concern.vue') },
    { path: '/scene',       name: 'scene',        component: () => import('@/views/Scene.vue') },
    { path: '/belief',      name: 'belief',       component: () => import('@/views/Belief.vue') },
    { path: '/question',    name: 'question',     component: () => import('@/views/Question.vue') },
    { path: '/analyzing',   name: 'analyzing',    component: () => import('@/views/Analyzing.vue') },
    { path: '/factormap',   name: 'factormap',    component: () => import('@/views/Factormap.vue') },
    { path: '/result',      name: 'result',       component: () => import('@/views/Result.vue') },
    { path: '/expectation', name: 'expectation',  component: () => import('@/views/Expectation.vue') },
    { path: '/prescription',name: 'prescription', component: () => import('@/views/Prescription.vue') },
    { path: '/share',       name: 'share',        component: () => import('@/views/Share.vue') },
    { path: '/register',    name: 'register',     component: () => import('@/views/Register.vue') },
    { path: '/unlock',      name: 'unlock',       component: () => import('@/views/Unlock.vue'),
      meta: { requiresAuth: true } },
    { path: '/companion',   name: 'companion',    component: () => import('@/views/Companion.vue'),
      meta: { requiresAuth: true } },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    return { name: 'prescription' }
  }
})

export default router
