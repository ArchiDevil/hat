<script setup lang="ts">
import {onMounted, ref} from 'vue'
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

const tmxDocs = ref<TmxDoc[]>([])
const xliffDocs = ref<XliffDoc[]>([])
const fileDeleting = ref(false)

const getTmxDocs = async () => {
  tmxDocs.value = await tmxApi.get<TmxDoc[]>()
}

const getXliffDocs = async () => {
  xliffDocs.value = await xliffApi.get<XliffDoc[]>()
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
        @deleting="fileDeleting = true"
        @delete=";(fileDeleting = false), getTmxDocs()" />
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
        @deleting="fileDeleting = true"
        @delete=";(fileDeleting = false), getXliffDocs()" />
    </div>
  </div>
</template>
