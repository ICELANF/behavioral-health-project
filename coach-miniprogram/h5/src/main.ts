import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Install uni compat shim (must be before component imports)
import './compat/uni'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
