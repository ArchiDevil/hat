import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {RouteRecordRaw, createRouter, createWebHistory} from 'vue-router'
import {MandeError, defaults} from 'mande'

import PrimeVue from 'primevue/config'
import {definePreset} from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import {useUserStore} from './stores/user'
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

const routes: RouteRecordRaw[] = [
  {path: '/', name: 'home', component: IndexView},
  {path: '/tmx/:id', name: 'tmx', component: TmxView},
  {path: '/xliff/:id', name: 'xliff', component: XliffView},
  {path: '/users/', name: 'users', component: UsersView},
  {path: '/login/', name: 'login', component: LoginView},
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from) => {
  const store = useUserStore()

  if (to.name === 'login') {
    if (store.currentUser) {
      // redirect to home page if user is logged in
      return {name: 'home'}
    }
    return true
  }

  const requestInterval = 10 * 60 * 1000
  if (
    !store.currentUser ||
    store.lastTimeRequested.getTime() + requestInterval < Date.now()
  ) {
    try {
      await store.fetchCurrentUser()
    } catch (e) {
      const err = e as MandeError
      if (err.response.status == 401) {
        router.push({
          name: 'login',
          query: {
            redirect: to.path,
          },
        })
      } else {
        throw e
      }
    }
  }

  return true
})

if (import.meta.env.DEV) {
  // to test it locally
  defaults.credentials = 'include'
}

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
app.config.errorHandler = (err, instance, info) => {
  // TODO: add some kind of a monitoring system like sentry
  console.log('Error: ', err, '- ', info)
  console.log(instance)
}
app.mount('#app')
