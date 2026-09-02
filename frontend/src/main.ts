import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.config.errorHandler = (err, instance, info) => {
  console.error('VUE_ERROR:', err, info)
  // 也在页面上显示
  const el = document.createElement('div')
  el.style.cssText = 'position:fixed;top:0;left:0;right:0;background:red;color:white;padding:12px;z-index:999999;font-family:monospace;font-size:13px;'
  el.innerText = `🚨 Vue Error: ${err?.message || err}\n${info || ''}`
  document.body.appendChild(el)
}

app.mount('#app')
