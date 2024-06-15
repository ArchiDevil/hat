import {acceptHMRUpdate, defineStore} from 'pinia'

import {TmxFile} from '../client/schemas/TmxFile'
import {getTmxs} from '../client/services/TmxService'

interface SelectedTmx extends TmxFile {
  selected: boolean
}

export const useTmxStore = defineStore('tmx', {
  state() {
    return {
      tmxFiles: [] as SelectedTmx[],
    }
  },
  actions: {
    async getTmx() {
      this.tmxFiles = [] as SelectedTmx[]
      const files = await getTmxs()
      for (const file of files) {
        this.tmxFiles = [
          ...this.tmxFiles,
          {
            id: file.id,
            name: file.name,
            selected: true,
          },
        ]
      }
    },
    selectAll() {
      for (const tmx of this.tmxFiles) {
        tmx.selected = true
      }
    },
    selectNone() {
      for (const tmx of this.tmxFiles) {
        tmx.selected = false
      }
    },
  },
  getters: {
    selectedCount(state) {
      return state.tmxFiles.filter((tmx) => tmx.selected).length
    },
    totalCount(state) {
      return state.tmxFiles.length
    },
    selectedIds(state) {
      return state.tmxFiles.filter((tmx) => tmx.selected).map(({id}) => id)
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTmxStore, import.meta.hot))
}
