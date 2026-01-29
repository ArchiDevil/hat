<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {Button, Panel} from 'primevue'

import {useTmStore} from '../stores/tm'
import {useGlossaryStore} from '../stores/glossary'

import DocUploadingDialog from '../components/DocUploadingDialog.vue'
import TmRecord from '../components/TmRecord.vue'
import PageNav from '../components/PageNav.vue'
import DocSettingsModal from '../components/DocSettingsModal.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import GlossaryUploadingDialog from '../components/glossary/GlossaryUploadingDialog.vue'
import GlossaryRecord from '../components/glossary/GlossaryRecord.vue'
import ProjectList from '../components/ProjectList.vue'
import AddProjectModal from '../components/AddProjectModal.vue'

const router = useRouter()

const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const docSettingsVisible = ref(false)
const selectedDocumentId = ref<number | undefined>(undefined)

const addProjectVisible = ref(false)

onMounted(async () => {
  await tmStore.fetchMemories()
  await glossaryStore.fetchGlossaries()
})
</script>

<template>
  <div class="container">
    <PageNav class="mb-8" />

    <div class="flex flex-col gap-4">
      <Panel header="Projects">
        <template #icons>
          <Button
            icon="pi pi-plus"
            size="small"
            label="Add new project"
            @click="addProjectVisible = true"
          />
        </template>
        <template #default>
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
                docSettingsVisible = true
              }
            "
          />
        </template>
      </Panel>

      <Panel header="Glossaries">
        <GlossaryUploadingDialog @uploaded="glossaryStore.fetchGlossaries()" />
        <GlossaryRecord
          v-for="file in glossaryStore.glossaries"
          :key="file.id"
          :file="file"
          @update="glossaryStore.fetchGlossaries()"
        />
      </Panel>

      <Panel header="Translation Memories">
        <TmxUploadingDialog @uploaded="tmStore.fetchMemories()" />
        <TmRecord
          v-for="file in tmStore.memories"
          :key="file.id"
          :file="file"
          :delete-method="() => tmStore.delete(file)"
          @delete="tmStore.fetchMemories()"
        />
      </Panel>
    </div>
  </div>

  <DocSettingsModal
    v-if="selectedDocumentId"
    v-model="docSettingsVisible"
    :document-id="selectedDocumentId"
  />

  <AddProjectModal v-model="addProjectVisible" />
</template>
