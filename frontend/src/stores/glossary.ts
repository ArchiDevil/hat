import {acceptHMRUpdate, defineStore} from 'pinia'

import {
  createGlossaryFromFile,
  listGlossary,
  deleteGlossary,
} from '../client/services/GlossaryService'
import {GlossaryResponse} from '../client/schemas/GlossaryResponse'
import {GlossaryLoadFileResponse} from '../client/schemas/GlossaryLoadFileResponse'

export const useGlossaryStore = defineStore('glossary', {
  state() {
    return {
      glossaries: [] as GlossaryResponse[],
    }
  },
  actions: {
    async create(name: string, file: Blob): Promise<GlossaryLoadFileResponse> {
      return await createGlossaryFromFile(name, {file})
    },
    async fetchGlossaries() {
      this.glossaries = await listGlossary()
    },
    async delete(glossary: GlossaryResponse) {
      await deleteGlossary(glossary.id)
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useGlossaryStore, import.meta.hot))
}
