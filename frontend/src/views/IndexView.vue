<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {createTmx, deleteTmx, getTmxs} from '../client/services/TmxService'
import {
  createXliff,
  deleteXliff,
  getXliffs,
} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import {TmxFile} from '../client/schemas/TmxFile'

import File from '../components/File.vue'
import UploadingDialog from '../components/UploadingDialog.vue'

const tmxDocs = ref<TmxFile[]>([])
const xliffDocs = ref<XliffFile[]>([])

const getTmxDocs = async () => {
  tmxDocs.value = await getTmxs()
}

const getXliffDocs = async () => {
  xliffDocs.value = await getXliffs()
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
        url="/api/tmx/upload"
        :upload-method="(file: File) => createTmx({file})"
        @uploaded="getTmxDocs()" />
      <File
        v-for="file in tmxDocs"
        :file="file"
        :delete-method="deleteTmx"
        type="tmx"
        @delete="getTmxDocs()" />
    </div>

    <div class="mt-8">
      <h2 class="font-bold text-lg">XLIFF documents list</h2>
      <UploadingDialog
        title="Select a XLIFF file:"
        extension=".xliff"
        url="/api/xliff/upload"
        :upload-method="(file: File) => createXliff({file})"
        @uploaded="getXliffDocs()" />
      <File
        v-for="file in xliffDocs"
        :file="file"
        :delete-method="deleteXliff"
        type="xliff"
        @delete="getXliffDocs()" />
    </div>
  </div>
</template>
