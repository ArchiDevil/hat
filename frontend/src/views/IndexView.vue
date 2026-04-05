<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {Button, Panel} from 'primevue'
import {useQueryCache} from '@pinia/colada'

import {useTmStore} from '../stores/tm'
import {GLOSSARY_KEYS, useGlossaries} from '../queries/glossaries'

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
import {isAdmin} from '../utilities/auth'

const tmStore = useTmStore()

const queryCache = useQueryCache()
const {data: glossaries} = useGlossaries()

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
})
</script>

<template>
  <div class="container">
    <PageNav class="mb-8" />

    <div class="flex flex-col gap-4">
      <Panel header="Projects">
        <template #icons>
          <div
            v-if="isAdmin()"
            class="flex flex-row gap-4"
          >
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
        <GlossaryUploadingDialog
          v-if="isAdmin()"
          @uploaded="queryCache.invalidateQueries({key: GLOSSARY_KEYS.root})"
        />
        <GlossaryRecord
          v-for="file in glossaries"
          :key="file.id"
          :file="file"
          @update="queryCache.invalidateQueries({key: GLOSSARY_KEYS.root})"
        />
      </Panel>

      <Panel header="Translation Memories">
        <TmxUploadingDialog
          v-if="isAdmin()"
          @uploaded="tmStore.fetchMemories()"
        />
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
