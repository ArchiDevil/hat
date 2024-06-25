import {acceptHMRUpdate, defineStore} from 'pinia'

import {User} from '../client/schemas/User'
import {getCurrentUser} from '../client/services/UsersService'

export const useUserStore = defineStore('user', {
  state() {
    return {
      currentUser: undefined as User | undefined,
      lastTimeRequested: new Date(),
    }
  },
  actions: {
    async fetchCurrentUser() {
      this.currentUser = await getCurrentUser()
      this.lastTimeRequested = new Date()
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useUserStore, import.meta.hot))
}
