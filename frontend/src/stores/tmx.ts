import {acceptHMRUpdate, defineStore} from 'pinia'

import {TmxFile} from '../client/schemas/TmxFile'
import {TmxUsage} from '../client/schemas/TmxUsage'
import {getTmxs} from '../client/services/TmxService'

export const useTmxStore = defineStore('tmx', {
  state() {
    return {
      tmxFiles: [] as TmxFile[],
      tmxMode: 'newest' as TmxUsage,
      selectedTmxFiles: [] as TmxFile[],
    }
  },
  actions: {
    async getTmx() {
      this.tmxFiles = []
      this.selectedTmxFiles = []
      this.tmxFiles = await getTmxs()
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
