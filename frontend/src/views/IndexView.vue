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
import ProjectSettingsModal from '../components/ProjectSettingsModal.vue'

const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const docSettingsVisible = ref(false)
const selectedDocumentId = ref<number | undefined>(undefined)

const addProjectVisible = ref(false)

const projectSettingsVisible = ref(false)
const projectSettingsId = ref<number>()

const addDocumentProjectId = ref<number>()
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
              label="Update translations"
              severity="secondary"
              @click="uploadXliffVisible = true"
            />
            <Button
              icon="pi pi-plus"
              size="small"
              label="Add new project"
              @click="addProjectVisible = true"
            />
          </div>
        </template>
        <template #default>
          <ProjectList
            @open-doc-settings="
              (docId) => {
                selectedDocumentId = docId
                docSettingsVisible = true
              }
            "
            @open-settings="
              (projId) => {
                projectSettingsId = projId
                projectSettingsVisible = true
              }
            "
            @upload-document="
              (projectId) => {
                addDocumentProjectId = projectId
                addDocumentVisible = true
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

  <AddDocumentModal
    v-model="addDocumentVisible"
    :project-id="addDocumentProjectId ?? -1"
  />
  <DocSettingsModal
    v-if="selectedDocumentId"
    v-model="docSettingsVisible"
    :document-id="selectedDocumentId"
  />

  <AddProjectModal v-model="addProjectVisible" />
  <ProjectSettingsModal
    v-if="projectSettingsId"
    v-model="projectSettingsVisible"
    :project-id="projectSettingsId"
  />

  <UploadXliffModal v-model="uploadXliffVisible" />
</template>
