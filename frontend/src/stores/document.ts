import {acceptHMRUpdate, defineStore} from 'pinia'

import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'
import {getDoc, getDocs} from '../client/services/DocumentService'

export const useDocStore = defineStore('document', {
  state() {
    return {
      docs: [] as DocumentWithRecordsCount[],
    }
  },
  actions: {
    async fetchDocs() {
      this.docs = await getDocs()
    },
    async updateDocument(id: number) {
      const idx = this.docs.findIndex((doc) => doc.id === id)
      if (idx !== -1) {
        this.docs[idx] = await getDoc(this.docs[idx].id)
      }
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useDocStore, import.meta.hot))
}
