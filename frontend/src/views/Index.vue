<script lang="ts">
import {defineComponent} from 'vue'
import {mande} from 'mande'

import File from '../components/File.vue'
import Button from '../components/Button.vue'
import UploadingDialog from '../components/UploadingDialog.vue'

interface TmxDoc {
  id: number
  name: string
}

interface XliffDoc {
  id: number
  name: string
}

export default defineComponent({
  components: {Button, File, UploadingDialog},
  data() {
    return {
      tmx_docs: [] as TmxDoc[],
      xliff_docs: [] as XliffDoc[],
    }
  },
  async mounted() {
    await this.getTmxDocs()
    await this.getXliffDocs()
  },
  methods: {
    openTmx(id: number) {
      window.location.href = `/tmx/${id}`
    },
    async deleteTmx(id: number) {
      await mande(`/api/tmx/${id}/delete`).post()
      await this.getTmxDocs()
    },
    openXliff(id: number) {
      window.location.href = `/xliff/${id}`
    },
    async deleteXliff(id: number) {
      await mande(`/api/xliff/${id}/delete`).post()
      await this.getXliffDocs()
    },
    async getTmxDocs() {
      this.tmx_docs = [
        {id: 1, name: 'test.tmx'},
        {id: 2, name: 'test2.tmx'},
      ]
      // this.tmx_docs = await mande('/api/tmx').get<TmxDoc[]>()
    },
    async getXliffDocs() {
      this.xliff_docs = [
        {id: 1, name: 'test.xliff'},
        {id: 2, name: 'test2.xliff'},
      ]
      // this.xliff_docs = await mande('/api/xliff').get<XliffDoc[]>()
    },
  },
})
</script>

<template>
  <div class="text-base text-slate-900 font-medium">
    <h1 class="font-bold text-2xl">Process TMX matches</h1>
    <div class="mt-8">
      <h2 class="font-bold text-lg">TMX files list</h2>
      <UploadingDialog
        title="Select a TMX file:"
        extension=".tmx"
        url="/tmx/upload" />
      <File
        v-for="file in tmx_docs"
        :file="file"
        type="tmx"
        @delete="deleteTmx(file.id)"
        @open="openTmx(file.id)" />
    </div>

    <div class="mt-8">
      <h2 class="font-bold text-lg">XLIFF documents list</h2>
      <UploadingDialog
        title="Select a XLIFF file:"
        extension=".xliff"
        url="/xliff/upload" />
      <File
        v-for="file in tmx_docs"
        :file="file"
        type="xliff"
        @delete="deleteXliff(file.id)"
        @open="openXliff(file.id)" />
    </div>
  </div>
</template>

<style scoped>
.form {
  @apply p-2 min-w-96;
  border: 2px solid grey;
}
</style>
