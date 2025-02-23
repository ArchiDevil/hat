import {acceptHMRUpdate, defineStore} from 'pinia'

import {DocumentRecord} from '../client/schemas/DocumentRecord'
import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'
import {MemorySubstitution} from '../client/schemas/MemorySubstitution'
import {
  getDownloadDocLink,
  getRecordSubstitutions,
  getDoc,
  getDocRecords,
  updateDocRecord,
  getRecordGlossaryRecords,
} from '../client/services/DocumentService'
import {useDocStore} from './document'
import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'

export interface DocFileRecordWithStatus extends DocumentRecord {
  loading: boolean
}

export const useCurrentDocStore = defineStore('current_document', {
  state() {
    return {
      documentLoading: false,
      document: undefined as DocumentWithRecordsCount | undefined,
      records: [] as DocFileRecordWithStatus[],
      currentFocusIdx: undefined as number | undefined,
      downloadLink: undefined as string | undefined,
      substitutions: [] as MemorySubstitution[],
      glossaryRecords: [] as GlossaryRecordSchema[],
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
    async updateRecord(record_id: number, content: string, approved: boolean) {
      if (!this.document) {
        return
      }

      const idx = this.records.findIndex((record) => record.id === record_id)
      if (idx < 0) {
        console.warn('Record not found')
        return
      }
      this.records[idx].loading = true
      const newRecord = await updateDocRecord(record_id, {
        target: content,
        approved: approved,
      })
      this.records[idx] = {
        ...newRecord,
        loading: false,
      }
      // rerequest a document to update its records count
      // this is because more than one record can be updated by a backend
      // (repetitions, for example)
      this.document = await getDoc(this.document.id)
      await useDocStore().updateDocument(this.document.id)
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
      this.substitutions = []
      this.glossaryRecords = []

      if (!this.document || this.currentFocusIdx === undefined) {
        return
      }

      this.substitutions = await getRecordSubstitutions(
        this.document.id,
        this.currentFocusId!
      )
      this.glossaryRecords = await getRecordGlossaryRecords(
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
  import.meta.hot.accept(acceptHMRUpdate(useCurrentDocStore, import.meta.hot))
}
