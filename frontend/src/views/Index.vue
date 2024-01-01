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

const tmxDocs = ref([]) as Ref<TmxDoc[]>
const xliffDocs = ref([]) as Ref<XliffDoc[]>
const fileDeleting = ref(false)

const getTmxDocs = async () => {
  tmxDocs.value = await tmxApi.get<TmxDoc[]>()
}

const deleteTmx = async (id: number) => {
  fileDeleting.value = true
  await tmxApi.post(`/${id}/delete`)
  fileDeleting.value = false
  await getTmxDocs()
}

const getXliffDocs = async () => {
  xliffDocs.value = await xliffApi.get<XliffDoc[]>()
}

const deleteXliff = async (id: number) => {
  fileDeleting.value = true
  await xliffApi.post(`/${id}/delete`)
  fileDeleting.value = false
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
        v-for="file in tmxDocs"
        :file="file"
        :busy="fileDeleting"
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
        v-for="file in xliffDocs"
        :file="file"
        :busy="fileDeleting"
        type="xliff"
        @delete="deleteXliff(file.id)" />
    </div>
  </div>
</template>
