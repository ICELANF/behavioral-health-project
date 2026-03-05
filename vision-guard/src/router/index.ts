import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/survey',
      name: 'survey',
      component: () => import('@/views/Survey.vue'),
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('@/views/Report.vue'),
    },
    {
      path: '/education',
      name: 'education',
      component: () => import('@/views/Education.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/Profile.vue'),
    },
    {
      path: '/food',
      name: 'food',
      component: () => import('@/views/food/FoodLog.vue'),
    },
    {
      path: '/food/record',
      name: 'food-record',
      component: () => import('@/views/food/FoodRecord.vue'),
    },
    {
      path: '/food/survey',
      name: 'food-survey',
      component: () => import('@/views/food/NutritionSurvey.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
    },
  ],
})

export default router
