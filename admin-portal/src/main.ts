import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import router from './router'
import App from './App.vue'
import 'ant-design-vue/dist/reset.css'
import './style.css'
import '@/styles/react-components.css'
import './styles/bhp-design-tokens.css'
import './styles/antd-overrides.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Antd)

app.mount('#app')
