<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'

import {useTmStore} from '../stores/tm'
import {useDocStore} from '../stores/document'

import Panel from 'primevue/panel'

import TestingWarning from '../components/TestingWarning.vue'
import DocumentList from '../components/DocumentList.vue'
import DocUploadingDialog from '../components/DocUploadingDialog.vue'
import TmRecord from '../components/TmRecord.vue'
import PageNav from '../components/PageNav.vue'
import TmSettingsModal from '../components/TmSettingsModal.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'

const router = useRouter()

const tmStore = useTmStore()
const docStore = useDocStore()

const tmSettingsVisible = ref(false)
const selectedDocumentId = ref<number | undefined>(undefined)

onMounted(async () => {
  await tmStore.fetchMemories()
  await docStore.fetchDocs()
})
</script>

<template>
  <div class="container">
    <PageNav />
    <TestingWarning />

    <Panel
      class="mt-4"
      header="Translation Memories"
      toggleable
    >
      <TmxUploadingDialog @uploaded="tmStore.fetchMemories()" />
      <TmRecord
        v-for="file in tmStore.memories"
        :key="file.id"
        :file="file"
        :delete-method="() => tmStore.delete(file)"
        @delete="tmStore.fetchMemories()"
      />
    </Panel>

    <Panel
      class="mt-4"
      header="Documents"
      toggleable
    >
      <DocUploadingDialog
        title="Select a file to upload:"
        @processed="
          (fileId) => router.push({name: 'document', params: {id: fileId}})
        "
      />
      <DocumentList
        :documents="docStore.docs"
        @delete="docStore.fetchDocs()"
        @open-settings="
          (docId) => {
            selectedDocumentId = docId
            tmSettingsVisible = true
          }
        "
      />
    </Panel>
  </div>

  <TmSettingsModal
    v-if="selectedDocumentId"
    v-model="tmSettingsVisible"
    :document-id="selectedDocumentId"
  />
</template>
