import {acceptHMRUpdate, defineStore} from 'pinia'

import {TranslationMemory} from '../client/schemas/TranslationMemory'
import {TranslationMemoryUsage} from '../client/schemas/TranslationMemoryUsage'
import {
  createTranslationMemory,
  deleteMemory,
  getMemories,
} from '../client/services/TmsService'
import {TranslationMemoryCreationSettings} from '../client/schemas/TranslationMemoryCreationSettings'

export const useTmStore = defineStore('tm', {
  state() {
    return {
      memories: [] as TranslationMemory[],
      // these fields must be moved out of the store
      memoryMode: 'newest' as TranslationMemoryUsage,
      selectedMemories: [] as TranslationMemory[],
    }
  },
  actions: {
    async create(
      settings: TranslationMemoryCreationSettings
    ): Promise<TranslationMemory> {
      const memory = await createTranslationMemory(settings)
      await this.fetchMemories()
      return memory
    },
    async fetchMemories() {
      this.memories = []
      this.selectedMemories = []
      this.memories = await getMemories()
      this.selectedMemories = this.memories
    },
    async delete(memory: TranslationMemory) {
      await deleteMemory(memory.id)
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
