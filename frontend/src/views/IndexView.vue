<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {deleteTmx, getTmxs} from '../client/services/TmxService'
import {deleteXliff, getXliffs} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import {TmxFile} from '../client/schemas/TmxFile'

import File from '../components/File.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import XliffUploadingDialog from '../components/XliffUploadingDialog.vue'

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
      <TmxUploadingDialog
        title="Select a TMX file:"
        @uploaded="getTmxDocs()"
      />
      <File
        v-for="file in tmxDocs"
        :key="file.id"
        :file="file"
        :delete-method="deleteTmx"
        type="tmx"
        @delete="getTmxDocs()"
      />
    </div>

    <div class="mt-8">
      <h2 class="font-bold text-lg">XLIFF documents list</h2>
      <XliffUploadingDialog
        title="Select a XLIFF file:"
        @processed="getXliffDocs()"
      />
      <File
        v-for="file in xliffDocs"
        :key="file.id"
        :file="file"
        :delete-method="deleteXliff"
        type="xliff"
        @delete="getXliffDocs()"
      />
    </div>
  </div>
</template>
