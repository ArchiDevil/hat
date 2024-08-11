import {acceptHMRUpdate, defineStore} from 'pinia'

import {TranslationMemory} from '../client/schemas/TranslationMemory'
import {TranslationMemoryUsage} from '../client/schemas/TranslationMemoryUsage'
import {getTranslationMemories} from '../client/services/TmsService'

export const useTmxStore = defineStore('tmx', {
  state() {
    return {
      tmxFiles: [] as TranslationMemory[],
      tmxMode: 'newest' as TranslationMemoryUsage,
      selectedTmxFiles: [] as TranslationMemory[],
    }
  },
  actions: {
    async getTmx() {
      this.tmxFiles = []
      this.selectedTmxFiles = []
      this.tmxFiles = await getTranslationMemories()
      this.selectedTmxFiles = this.tmxFiles
    },
  },
  getters: {
    selectedIds(state) {
      return state.selectedTmxFiles.map(({id}) => id)
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTmxStore, import.meta.hot))
}
