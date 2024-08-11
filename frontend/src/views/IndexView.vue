<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {deleteTmx, getTmxs} from '../client/services/TmxService'
import {getDocs} from '../client/services/DocumentService'
import {Document} from '../client/schemas/Document'
import {TmxFile} from '../client/schemas/TmxFile'

import Panel from 'primevue/panel'

import DocumentList from '../components/DocumentList.vue'
import DocUploadingDialog from '../components/DocUploadingDialog.vue'
import TmRecord from '../components/TmRecord.vue'
import PageNav from '../components/PageNav.vue'
import SupportLinks from '../components/SupportLinks.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'

const tmxDocs = ref<TmxFile[]>([])
const docs = ref<Document[]>([])

const getTmxDocs = async () => {
  tmxDocs.value = await getTmxs()
}

const getDocuments = async () => {
  docs.value = await getDocs()
}

onMounted(async () => {
  await getTmxDocs()
  await getDocuments()
})
</script>

<template>
  <div class="container">
    <PageNav />
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
      <TmRecord
        v-for="file in tmxDocs"
        :key="file.id"
        :file="file"
        :delete-method="deleteTmx"
        @delete="getTmxDocs()"
      />
    </Panel>

    <Panel
      class="mt-4"
      header="Documents list"
      toggleable
    >
      <DocUploadingDialog
        title="Select a file to upload:"
        @processed="
          (fileId) => $router.push({name: 'document', params: {id: fileId}})
        "
      />
      <DocumentList
        :documents="docs"
        @delete="getDocuments()"
      />
    </Panel>
  </div>
</template>
