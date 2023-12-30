<script setup lang="ts">
import {Ref, onMounted, ref} from 'vue'
import {mande} from 'mande'

import File from '../components/File.vue'
import UploadingDialog from '../components/UploadingDialog.vue'

interface TmxDoc {
  id: number
  name: string
}

interface XliffDoc {
  id: number
  name: string
}

const tmx_docs = ref([]) as Ref<TmxDoc[]>
const xliff_docs = ref([]) as Ref<XliffDoc[]>

const getTmxDocs = async () => {
  tmx_docs.value = await mande('/api/tmx').get<TmxDoc[]>()
}

const deleteTmx = async (id: number) => {
  await mande(`/api/tmx/${id}/delete`).post()
  await getTmxDocs()
}

const getXliffDocs = async () => {
  xliff_docs.value = await mande('/api/xliff').get<XliffDoc[]>()
}

const deleteXliff = async (id: number) => {
  await mande(`/api/xliff/${id}/delete`).post()
  await getXliffDocs()
}

onMounted(async () => {
  await getTmxDocs()
  await getXliffDocs()
})
</script>

<template>
  <div>
    <h1 class="font-bold text-2xl pt-8">Process TMX matches</h1>
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
        @delete="deleteTmx(file.id)" />
    </div>

    <div class="mt-8">
      <h2 class="font-bold text-lg">XLIFF documents list</h2>
      <UploadingDialog
        title="Select a XLIFF file:"
        extension=".xliff"
        url="/xliff/upload" />
      <File
        v-for="file in xliff_docs"
        :file="file"
        type="xliff"
        @delete="deleteXliff(file.id)" />
    </div>
  </div>
</template>
