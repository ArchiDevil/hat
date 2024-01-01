<script setup lang="ts">
import {Ref, onMounted, ref} from 'vue'
import {apiAccessor} from '../api'

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

const tmxApi = apiAccessor('/tmx')
const xliffApi = apiAccessor('/xliff')

const tmx_docs = ref([]) as Ref<TmxDoc[]>
const xliff_docs = ref([]) as Ref<XliffDoc[]>

const getTmxDocs = async () => {
  tmx_docs.value = await tmxApi.get<TmxDoc[]>()
}

const deleteTmx = async (id: number) => {
  await tmxApi.post(`/${id}/delete`)
  await getTmxDocs()
}

const getXliffDocs = async () => {
  xliff_docs.value = await xliffApi.get<XliffDoc[]>()
}

const deleteXliff = async (id: number) => {
  await xliffApi.post(`/${id}/delete`)
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
        url="/tmx/upload"
        @uploaded="getTmxDocs()" />
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
        url="/xliff/upload"
        @uploaded="getXliffDocs()" />
      <File
        v-for="file in xliff_docs"
        :file="file"
        type="xliff"
        @delete="deleteXliff(file.id)" />
    </div>
  </div>
</template>
