import {acceptHMRUpdate, defineStore} from 'pinia'
import {getCurrentUser} from '../client/services/UserService'
import {logout} from '../client/services/AuthService'
import {UserWithPermissions} from '../client/schemas/UserWithPermissions'

export const useUserStore = defineStore('user', {
  state() {
    return {
      currentUser: undefined as UserWithPermissions | undefined,
      lastTimeRequested: new Date(),
    }
  },
  actions: {
    async fetchCurrentUser() {
      this.currentUser = await getCurrentUser()

      // it might be not loaded yet
      const umami = window.umami
      umami?.identify(this.currentUser.email)

      this.lastTimeRequested = new Date()
    },
    async logout() {
      await logout()
      this.currentUser = undefined
      this.lastTimeRequested = new Date()
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useUserStore, import.meta.hot))
}
