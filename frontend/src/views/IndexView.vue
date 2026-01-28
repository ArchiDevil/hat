<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {Fieldset} from 'primevue'

import {useTmStore} from '../stores/tm'
import {useGlossaryStore} from '../stores/glossary'

import DocUploadingDialog from '../components/DocUploadingDialog.vue'
import TmRecord from '../components/TmRecord.vue'
import PageNav from '../components/PageNav.vue'
import TmSettingsModal from '../components/TmSettingsModal.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import GlossaryUploadingDialog from '../components/glossary/GlossaryUploadingDialog.vue'
import GlossaryRecord from '../components/glossary/GlossaryRecord.vue'
import ProjectList from '../components/ProjectList.vue'

const router = useRouter()

const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const tmSettingsVisible = ref(false)
const selectedDocumentId = ref<number | undefined>(undefined)

onMounted(async () => {
  await tmStore.fetchMemories()
  await glossaryStore.fetchGlossaries()
})
</script>

<template>
  <div class="container">
    <PageNav />

    <div class="flex flex-col gap-4">
      <Fieldset legend="Projects">
        <DocUploadingDialog
          class="mb-4"
          title="Select a file to upload:"
          @processed="
            (fileId) => router.push({name: 'document', params: {id: fileId}})
          "
        />
        <ProjectList
          @open-settings="
            (docId) => {
              selectedDocumentId = docId
              tmSettingsVisible = true
            }
          "
        />
      </Fieldset>

      <Fieldset legend="Glossaries">
        <GlossaryUploadingDialog @uploaded="glossaryStore.fetchGlossaries()" />
        <GlossaryRecord
          v-for="file in glossaryStore.glossaries"
          :key="file.id"
          :file="file"
          @update="glossaryStore.fetchGlossaries()"
        />
      </Fieldset>

      <Fieldset legend="Translation Memories">
        <TmxUploadingDialog @uploaded="tmStore.fetchMemories()" />
        <TmRecord
          v-for="file in tmStore.memories"
          :key="file.id"
          :file="file"
          :delete-method="() => tmStore.delete(file)"
          @delete="tmStore.fetchMemories()"
        />
      </Fieldset>
    </div>
  </div>

  <TmSettingsModal
    v-if="selectedDocumentId"
    v-model="tmSettingsVisible"
    :document-id="selectedDocumentId"
  />
</template>
