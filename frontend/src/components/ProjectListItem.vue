<script setup lang="ts">
import {computed, ref} from 'vue'
import {useQuery, useQueryCache} from '@pinia/colada'
import {Panel, ProgressBar} from 'primevue'

import {ProjectResponse} from '../client/schemas/ProjectResponse'
import {retrieveProject} from '../client/services/ProjectsService'

import DocumentList from './DocumentList.vue'

const {project} = defineProps<{
  project: ProjectResponse
}>()

defineEmits<{
  openSettings: [number]
}>()

const collapsed = ref(true)

const {data: detailedInfo, status} = useQuery({
  key: () => ['projects', project.id],
  query: async () => {
    return await retrieveProject(project.id)
  },
  enabled: () => collapsed.value === false,
  placeholderData: <T,>(prevData: T) => prevData,
})

const queryCache = useQueryCache()
const projectName = computed(() =>
  project.id !== -1 ? `#${project.id} ${project.name}` : project.name
)

const progressBarValue = computed(() => {
  return detailedInfo.value
    ? (detailedInfo.value?.approved_words_count /
        detailedInfo.value?.total_words_count) *
        100
    : 0
})

const progressBarTitle = computed(() => {
  return `Words: ${detailedInfo.value?.approved_words_count} / ${detailedInfo.value?.total_words_count}`
})
</script>

<template>
  <Panel
    v-model:collapsed="collapsed"
    toggleable
  >
    <template #header>
      <div class="flex flex-row gap-4">
        <span>{{ projectName }}</span>
        <ProgressBar
          v-if="detailedInfo && !isNaN(progressBarValue)"
          class="w-36 h-2 self-center"
          :value="progressBarValue"
          :title="progressBarTitle"
          :show-value="false"
        />
      </div>
    </template>
    <template #default>
      <ProgressSpinner v-if="status === 'pending'" />
      <div
        v-else-if="
          detailedInfo === undefined || detailedInfo.documents.length === 0
        "
        class="pt-2 flex flex-row items-center gap-2"
      >
        <i class="pi pi-info-circle text-xl text-surface-500" />
        <span class="text-lg"> No documents in the project </span>
      </div>
      <DocumentList
        v-else
        :documents="detailedInfo!.documents"
        @open-settings="(docId) => $emit('openSettings', docId)"
        @delete="
          () =>
            queryCache.invalidateQueries({
              key: ['projects', project.id],
            })
        "
      />
    </template>
  </Panel>
</template>
