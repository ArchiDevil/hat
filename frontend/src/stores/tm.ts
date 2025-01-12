import {acceptHMRUpdate, defineStore} from 'pinia'

import {TranslationMemory} from '../client/schemas/TranslationMemory'
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
      this.memories = await getMemories()
    },
    async delete(memory: TranslationMemory) {
      await deleteMemory(memory.id)
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTmStore, import.meta.hot))
}
