import {createApp} from 'vue'
import {createRouter, createWebHistory} from 'vue-router'

import App from './App.vue'
import IndexView from './views/IndexView.vue'
import TmxView from './views/TmxView.vue'
import XliffView from './views/XliffView.vue'

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
app.use(router)
app.mount('#app')
