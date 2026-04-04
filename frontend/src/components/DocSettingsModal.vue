<script setup lang="ts">
import {ref, computed, watch} from 'vue'
import {useQuery, useQueryCache} from '@pinia/colada'
import {Button, Dialog, Select} from 'primevue'

import {getDoc, updateDocument} from '../client/services/DocumentService'
import {PROJECT_KEYS, useProjects} from '../queries/projects'

const {documentId} = defineProps<{
  documentId: number
}>()

const busy = ref(false)
const modalVisible = defineModel<boolean>()

const queryCache = useQueryCache()
const save = async () => {
  busy.value = true
  await updateDocument(documentId, {
    project_id: chosenProject.value,
  })
  await queryCache.invalidateQueries({
    key: PROJECT_KEYS.root,
  })
  modalVisible.value = false
  busy.value = false
}

const {data: document} = useQuery({
  key: () => ['documents', documentId],
  query: async () => {
    return await getDoc(documentId)
  },
  enabled: () => modalVisible.value == true,
  placeholderData: (prevData) => prevData,
})

const {data: projects} = useProjects()
const chosenProject = ref<number>()
watch(document, (newVal) => {
  if (!newVal) return
  chosenProject.value = newVal.project_id ?? -1
})
const projectOptions = computed(() => {
  if (!projects.value) return []

  return projects.value.map((p) => {
    return {
      id: p.id,
      name: p.name,
    }
  })
})
</script>

<template>
  <Dialog
    v-model:visible="modalVisible"
    modal
    :header="`Document #${documentId} settings`"
    :style="{width: '32rem'}"
  >
    <span class="mb-2 block">Select project to put into:</span>
    <Select
      v-model="chosenProject"
      class="w-full"
      :options="projectOptions"
      option-label="name"
      option-value="id"
      :loading="chosenProject === undefined"
    />

    <template #footer>
      <Button
        type="button"
        severity="secondary"
        label="Cancel"
        :disabled="busy"
        @click="modalVisible = false"
      />
      <Button
        type="button"
        label="Save"
        :disabled="busy"
        @click="save"
      />
    </template>
  </Dialog>
</template>
