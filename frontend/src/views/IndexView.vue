<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {deleteTmx, getTmxs} from '../client/services/TmxService'
import {deleteXliff, getXliffs} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import {TmxFile} from '../client/schemas/TmxFile'

import Panel from 'primevue/panel'

import File from '../components/File.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import XliffUploadingDialog from '../components/XliffUploadingDialog.vue'
import SupportLinks from '../components/SupportLinks.vue'

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
    <Panel
      class="w-1/2 border rounded bg-red-50 px-4 mt-4"
      header="Warning!"
      toggleable
    >
      <p>
        The tool is currently in a testing phase. Please, be ready to sudden
        breakups and unexpected crashes.
        <span class="text-red-700 font-semibold">
          Use small portions of data with Yandex first!
        </span>
        If you find any bug or have ideas, please report them in any form using
        these links:
      </p>
      <SupportLinks />
    </Panel>

    <Panel
      class="mt-4"
      header="TMX files list"
      toggleable
    >
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
    </Panel>

    <Panel
      class="mt-4"
      header="XLIFF documents list"
      toggleable
    >
      <XliffUploadingDialog
        title="Select a XLIFF file:"
        @processed="
          (fileId) => $router.push({name: 'xliff', params: {id: fileId}})
        "
      />
      <File
        v-for="file in xliffDocs"
        :key="file.id"
        :file="file"
        :delete-method="deleteXliff"
        type="xliff"
        @delete="getXliffDocs()"
      />
    </Panel>
  </div>
</template>
