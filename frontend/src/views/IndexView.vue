<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {Button, Panel} from 'primevue'

import {useTmStore} from '../stores/tm'
import {useGlossaryStore} from '../stores/glossary'

import TmRecord from '../components/TmRecord.vue'
import PageNav from '../components/PageNav.vue'
import DocSettingsModal from '../components/DocSettingsModal.vue'
import TmxUploadingDialog from '../components/TmxUploadingDialog.vue'
import GlossaryUploadingDialog from '../components/glossary/GlossaryUploadingDialog.vue'
import GlossaryRecord from '../components/glossary/GlossaryRecord.vue'
import ProjectList from '../components/ProjectList.vue'
import AddProjectModal from '../components/AddProjectModal.vue'
import AddDocumentModal from '../components/AddDocumentModal.vue'
import UploadXliffModal from '../components/UploadXliffModal.vue'

const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const docSettingsVisible = ref(false)
const selectedDocumentId = ref<number | undefined>(undefined)

const addProjectVisible = ref(false)
const addDocumentVisible = ref(false)
const uploadXliffVisible = ref(false)

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
          <div class="flex flex-row gap-4">
            <Button
              icon="pi pi-file-arrow-up"
              size="small"
              label="Upload XLIFF"
              severity="secondary"
              @click="uploadXliffVisible = true"
            />
            <Button
              icon="pi pi-file-arrow-up"
              size="small"
              label="Upload document"
              @click="addDocumentVisible = true"
            />
            <Button
              icon="pi pi-plus"
              size="small"
              label="Add new project"
              severity="secondary"
              @click="addProjectVisible = true"
            />
          </div>
        </template>
        <template #default>
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
  <AddDocumentModal v-model="addDocumentVisible" />
  <UploadXliffModal v-model="uploadXliffVisible" />
</template>
