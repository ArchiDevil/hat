import {acceptHMRUpdate, defineStore} from 'pinia'

import {TranslationMemory} from '../client/schemas/TranslationMemory'
import {TranslationMemoryUsage} from '../client/schemas/TranslationMemoryUsage'
import {getMemories} from '../client/services/TmsService'

export const useTmStore = defineStore('tm', {
  state() {
    return {
      memories: [] as TranslationMemory[],
      memoryMode: 'newest' as TranslationMemoryUsage,
      selectedMemories: [] as TranslationMemory[],
    }
  },
  actions: {
    async fetchMemories() {
      this.memories = []
      this.selectedMemories = []
      this.memories = await getMemories()
      this.selectedMemories = this.memories
    },
  },
  getters: {
    selectedIds(state) {
      return state.selectedMemories.map(({id}) => id)
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTmStore, import.meta.hot))
}
