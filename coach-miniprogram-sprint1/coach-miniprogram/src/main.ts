import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// ─── 样式引入（顺序固定）────────────────────────────────────
import './styles/bhp-design-tokens.css'

export function createApp() {
  const app = createSSRApp(App)
  app.use(createPinia())
  return { app }
}
