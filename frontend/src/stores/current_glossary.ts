import {acceptHMRUpdate, defineStore} from 'pinia'
import {GlossaryResponse} from '../client/schemas/GlossaryResponse'
import {listRecords, retrieveGlossary} from '../client/services/GlossaryService'
import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'

export const useCurrentGlossaryStore = defineStore('current_glossary', {
  state() {
    return {
      glossary: undefined as GlossaryResponse | undefined,
      records: [] as GlossaryRecordSchema[],
      filteredRecordsCount: 0,
    }
  },
  actions: {
    async loadGlossary(glossaryId: number) {
      this.glossary = await retrieveGlossary(glossaryId)

      const resp = await listRecords(glossaryId, 0, '')
      this.records = resp.records
      this.filteredRecordsCount = resp.total_rows
    },
    async loadRecords(page: number | undefined, search?: string) {
      if (!this.glossary) throw new Error('No glossary loaded')

      const resp = await listRecords(this.glossary?.id, page ?? 0, search)
      this.records = resp.records
      this.filteredRecordsCount = resp.total_rows
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(
    acceptHMRUpdate(useCurrentGlossaryStore, import.meta.hot)
  )
}
