<script setup lang="ts">
import {useQuery} from '@pinia/colada'

import ProjectListItem from './ProjectListItem.vue'
import {listProjects} from '../client/services/ProjectsService'

const {data: projects, status: projectsStatus} = useQuery({
  key: ['projects'],
  query: async () => {
    return await listProjects()
  },
  placeholderData: <T,>(prevData: T) => prevData,
})

defineEmits<{
  openSettings: [number]
}>()
</script>

<template>
  <div class="flex flex-col gap-4">
    <ProgressSpinner v-if="projectsStatus == 'pending'" />
    <ProjectListItem
      v-for="project in projects"
      v-else
      :key="project.name"
      :project="project"
      @open-settings="(docId) => $emit('openSettings', docId)"
    />
  </div>
</template>
