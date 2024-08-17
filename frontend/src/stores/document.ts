import {acceptHMRUpdate, defineStore} from 'pinia'

import {Document} from '../client/schemas/Document'
import {getDocs} from '../client/services/DocumentService'

export const useDocStore = defineStore('document', {
  state() {
    return {
      docs: [] as Document[],
    }
  },
  actions: {
    async fetchDocs() {
      this.docs = await getDocs()
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useDocStore, import.meta.hot))
}
