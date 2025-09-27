import {acceptHMRUpdate, defineStore} from 'pinia'
import {GlossaryResponse} from '../client/schemas/GlossaryResponse'
import {listRecords, retrieveGlossary} from '../client/services/GlossaryService'
import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'

export const useCurrentGlossaryStore = defineStore('current_glossary', {
  state() {
    return {
      glossary: undefined as GlossaryResponse | undefined,
      records: [] as GlossaryRecordSchema[],
    }
  },
  actions: {
    async loadGlossary(glossaryId: number) {
      this.glossary = await retrieveGlossary(glossaryId)
      this.records = await listRecords(glossaryId, 0)
    },
    async loadRecords(page: number | undefined) {
      if (!this.glossary) throw new Error('No glossary loaded')
      this.records = await listRecords(this.glossary?.id, page ?? 0)
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(
    acceptHMRUpdate(useCurrentGlossaryStore, import.meta.hot)
  )
}
