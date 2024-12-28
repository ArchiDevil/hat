<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'

import {useTmStore} from '../stores/tm'
import {useDocStore} from '../stores/document'
import {useGlossaryStore} from '../stores/glossary'

import Panel from 'primevue/panel'

import TestingWarning from '../components/TestingWarning.vue'
import DocumentList from '../components/DocumentList.vue'
import DocUploadingDialog from '../components/DocUploadingDialog.vue'
import TmRecord from '../components/TmRecord.vue'
import PageNav from '../components/PageNav.vue'
import TmSettingsModal from '../components/TmSettingsModal.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import GlossaryUploadingDialog from '../components/glossary/GlossaryUploadingDialog.vue'
import GlossaryRecord from '../components/glossary/GlossaryRecord.vue'

const router = useRouter()

const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()
const docStore = useDocStore()

const tmSettingsVisible = ref(false)
const selectedDocumentId = ref<number | undefined>(undefined)

onMounted(async () => {
  await tmStore.fetchMemories()
  await glossaryStore.fetchGlossaries()
  await docStore.fetchDocs()
})

const showGlossaries = import.meta.env.VITE_ENABLE_GLOSSARIES === 'true'
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
      v-if="showGlossaries"
      class="mt-4"
      header="Glossaries"
      toggleable
    >
      <GlossaryUploadingDialog @uploaded="glossaryStore.fetchGlossaries()" />
      <GlossaryRecord
        v-for="file in glossaryStore.glossaries"
        :key="file.id"
        :file="file"
        :delete-method="() => glossaryStore.delete(file)"
        @delete="glossaryStore.fetchGlossaries()"
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
