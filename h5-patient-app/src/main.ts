import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Vant UI样式
import 'vant/lib/index.css'
// 全局样式
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
