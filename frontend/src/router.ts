import {type MandeError} from 'mande'
import {createRouter, createWebHistory, RouteRecordRaw} from 'vue-router'

const IndexView = () => import('./views/IndexView.vue')
const LoginView = () => import('./views/LoginView.vue')
const TmView = () => import('./views/TmView.vue')
const GlossaryView = () => import('./views/GlossaryView.vue')
const DocView = () => import('./views/DocView.vue')
const UsersView = () => import('./views/UsersView.vue')

import {useUserStore} from './stores/user'

export const getRouter = () => {
  const routes: RouteRecordRaw[] = [
    {path: '/', name: 'home', component: IndexView},
    {path: '/tm/:id', name: 'tm', component: TmView},
    {path: '/document/:id', name: 'document', component: DocView},
    {path: '/glossary/:id', name: 'glossary', component: GlossaryView},
    {path: '/users/', name: 'users', component: UsersView},
    {path: '/login/', name: 'login', component: LoginView},
  ]

  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  router.beforeEach(async (to) => {
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
          await router.push({
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

  return router
}
