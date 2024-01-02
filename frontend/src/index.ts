import {createApp} from 'vue'
import {createRouter, createWebHistory} from 'vue-router'

import App from './App.vue'
import Index from './views/Index.vue'
import Tmx from './views/Tmx.vue'
import Xliff from './views/Xliff.vue'

const routes = [
  {path: '/', component: Index},
  {path: '/tmx/:id', component: Tmx},
  {path: '/xliff/:id', component: Xliff},
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')
