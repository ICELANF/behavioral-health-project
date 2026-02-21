import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Vant 样式
import 'vant/lib/index.css'
// 全局样式
import './styles/global.scss'
// 品牌主题
import './styles/brand-themes.css'
import './styles/bhp-design-tokens.css'
import './styles/vant-overrides.css'

import { initTracker } from '@/utils/tracker'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// P5B: Initialize event tracker (page_view auto-tracking + session lifecycle)
initTracker(router)

app.mount('#app')
