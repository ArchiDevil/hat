import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {createRouter, createWebHistory} from 'vue-router'

import PrimeVue from 'primevue/config'
import {definePreset} from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import App from './App.vue'

const IndexView = () => import('./views/IndexView.vue')
const LoginView = () => import('./views/LoginView.vue')
const TmxView = () => import('./views/TmxView.vue')
const XliffView = () => import('./views/XliffView.vue')
const UsersView = () => import('./views/UsersView.vue')

const themePreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{sky.50}',
      100: '{sky.100}',
      200: '{sky.200}',
      300: '{sky.300}',
      400: '{sky.400}',
      500: '{sky.500}',
      600: '{sky.600}',
      700: '{sky.700}',
      800: '{sky.800}',
      900: '{sky.900}',
      950: '{sky.950}',
    },
  },
})

const pinia = createPinia()

const routes = [
  {path: '/', component: IndexView},
  {path: '/tmx/:id', component: TmxView},
  {path: '/xliff/:id', component: XliffView},
  {path: '/users/', component: UsersView},
  {path: '/login/', component: LoginView},
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(pinia)
app.use(PrimeVue, {
  theme: {
    preset: themePreset,
    options: {
      darkModeSelector: '',
      cssLayer: {
        name: 'primevue',
        order: 'tailwind-base, primevue, tailwind-utilities',
      },
    },
  },
})

app.use(router)
app.mount('#app')
