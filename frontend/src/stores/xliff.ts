import {acceptHMRUpdate, defineStore} from 'pinia'

import {DocumentRecord} from '../client/schemas/DocumentRecord'
import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'
import {MemorySubstitution} from '../client/schemas/MemorySubstitution'
import {
  getDownloadDocLink,
  getSegmentSubstitutions,
  getDoc,
  getDocRecords,
  updateDocRecord,
} from '../client/services/DocumentService'

export interface DocFileRecordWithStatus extends DocumentRecord {
  loading: boolean
}

export const useXliffStore = defineStore('xliff', {
  state() {
    return {
      documentLoading: false,
      document: undefined as DocumentWithRecordsCount | undefined,
      records: [] as DocFileRecordWithStatus[],
      currentFocusIdx: undefined as number | undefined,
      downloadLink: undefined as string | undefined,
      substitutions: [] as MemorySubstitution[],
    }
  },
  actions: {
    async loadDocument(doc_id: number) {
      this.documentLoading = true
      this.currentFocusIdx = undefined
      this.document = undefined
      this.document = await getDoc(doc_id)
      this.downloadLink = getDownloadDocLink(this.document.id)
      this.documentLoading = false
    },
    async loadRecords(page: number) {
      if (!this.document) {
        return
      }
      this.records = (await getDocRecords(this.document.id, page)).map(
        (record) => ({...record, loading: false})
      )
    },
    async updateRecord(record_id: number, content: string) {
      if (!this.document) {
        return
      }

      const idx = this.records.findIndex((record) => record.id === record_id)
      if (idx < 0) {
        console.warn('Record not found')
        return
      }
      this.records[idx].loading = true
      await updateDocRecord(this.document?.id, record_id, {
        target: content,
      })
      this.records[idx].loading = false
    },
    async focusSegment(idx: number) {
      this.currentFocusIdx = idx
      await this.loadSubstitutions()
    },
    focusNextSegment() {
      if (
        this.currentFocusIdx &&
        this.currentFocusIdx < this.records.length - 1
      ) {
        this.currentFocusIdx += 1
      }
    },
    async loadSubstitutions() {
      if (!this.document || this.currentFocusIdx === undefined) {
        this.substitutions = []
        return
      }

      this.substitutions = await getSegmentSubstitutions(
        this.document.id,
        this.currentFocusId!
      )
    },
  },
  getters: {
    documentReady: (state) =>
      state.document &&
      (state.document.status == 'done' || state.document.status == 'error'),
    currentFocusId: (state) =>
      state.records && state.currentFocusIdx !== undefined
        ? state.records[state.currentFocusIdx].id
        : undefined,
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useXliffStore, import.meta.hot))
}
