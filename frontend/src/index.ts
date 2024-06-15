import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {createRouter, createWebHistory} from 'vue-router'

import App from './App.vue'
import IndexView from './views/IndexView.vue'
import TmxView from './views/TmxView.vue'
import XliffView from './views/XliffView.vue'

const pinia = createPinia()

const routes = [
  {path: '/', component: IndexView},
  {path: '/tmx/:id', component: TmxView},
  {path: '/xliff/:id', component: XliffView},
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
