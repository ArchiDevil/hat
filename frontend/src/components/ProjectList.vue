<script setup lang="ts">
import {ProgressSpinner} from 'primevue'
import ProjectListItem from './ProjectListItem.vue'
import {useProjects} from '../queries/projects'

const {data: projects, status: projectsStatus} = useProjects()

defineEmits<{
  openDocSettings: [number]
  openSettings: [number]
  uploadDocument: [number]
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
      @open-doc-settings="(docId) => $emit('openDocSettings', docId)"
      @open-settings="(projId) => $emit('openSettings', projId)"
      @upload-document="(projectId) => $emit('uploadDocument', projectId)"
    />
  </div>
</template>
