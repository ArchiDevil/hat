<script setup lang="ts">
import {ref, watchEffect, computed} from 'vue'
import {useQueryCache} from '@pinia/colada'
import {Button, Dialog, InputText, Listbox, Select} from 'primevue'

import {useGlossaries} from '../queries/glossaries'
import {PROJECT_KEYS} from '../queries/projects'
import {TM_KEYS, useTranslationMemories} from '../queries/tms'

import {TmMode} from '../client/schemas/TmMode'
import {
  getProjectGlossaries,
  getProjectTranslationMemories,
  setProjectGlossaries,
  setProjectTranslationMemories,
} from '../client/services/ProjectsService'
import {createTranslationMemory} from '../client/services/TmsService'

const {projectId} = defineProps<{
  projectId: number
}>()

const busy = ref(false)

const {data: tms} = useTranslationMemories()
const {data: glossaries} = useGlossaries()

const modalVisible = defineModel<boolean>()
const chosenTms = ref<{id: number; name: string}[]>([])
const tmReadOptions = computed(() => {
  if (!tms.value) return []

  return tms.value.map((memory) => {
    return {id: memory.id, name: memory.name}
  })
})
const tmWriteOptions = computed(() => {
  return [{id: -1, name: "Don't use TM"}].concat(tmReadOptions.value)
})

const chosenWriteTmId = ref<number>(-1)
const createNewMode = ref(false)
const newTmName = ref('')
const createNewTm = async () => {
  busy.value = true
  await createTranslationMemory({
    name: newTmName.value,
  })
  await queryCache.invalidateQueries({
    key: TM_KEYS.root,
  })
  resetTmState()
  busy.value = false
}
const resetTmState = () => {
  newTmName.value = ''
  createNewMode.value = false
}

const chosenGlossaries = ref<{id: number; name: string}[]>([])
const glossaryOptions = computed(() => {
  if (!glossaries.value) return []

  return glossaries.value?.map((glossary) => {
    return {id: glossary.id, name: glossary.name}
  })
})

// eslint-disable-next-line @typescript-eslint/no-misused-promises
watchEffect(async () => {
  const projMemories = await getProjectTranslationMemories(projectId)
  chosenTms.value = projMemories.translation_memories
    .filter((memory) => memory.mode == 'read')
    .map((memory) => {
      return {id: memory.memory.id, name: memory.memory.name}
    })
  chosenWriteTmId.value =
    projMemories.translation_memories.find((memory) => memory.mode == 'write')
      ?.memory.id ?? -1

  const docGlossaries = await getProjectGlossaries(projectId)
  chosenGlossaries.value = docGlossaries.glossaries.map((glossary) => {
    return {id: glossary.id, name: glossary.name}
  })
})

const queryCache = useQueryCache()
const save = async () => {
  busy.value = true
  await setProjectTranslationMemories(projectId, {
    translation_memories: chosenTms.value
      .map((tm) => {
        return {
          id: tm.id,
          mode: 'read' as TmMode,
        }
      })
      .concat(
        chosenWriteTmId.value !== -1
          ? [{id: chosenWriteTmId.value, mode: 'write' as TmMode}]
          : []
      ),
  })
  await setProjectGlossaries(projectId, {
    glossaries: chosenGlossaries.value.map((glossary) => glossary.id),
  })
  await queryCache.invalidateQueries({
    key: PROJECT_KEYS.root,
  })
  modalVisible.value = false
  busy.value = false
}
</script>

<template>
  <Dialog
    v-model:visible="modalVisible"
    modal
    :header="`Project #${projectId} settings`"
    :style="{width: '32rem'}"
  >
    <div
      v-if="!createNewMode"
      class="flex gap-2 mb-2 items-baseline"
    >
      <span>Select memories to read from:</span>
      <Button
        class="ml-auto"
        label="Create"
        size="small"
        @click="createNewMode = true"
      />
    </div>
    <div
      v-else
      class="flex gap-2 mb-2 items-baseline"
    >
      <InputText
        v-model="newTmName"
        size="small"
        class="w-full"
        placeholder="New memory name..."
      />
      <Button
        class="ml-auto w-20"
        label="Ok"
        size="small"
        :disabled="!newTmName.length"
        @click="createNewTm()"
      />
      <Button
        class="w-20"
        label="Cancel"
        size="small"
        @click="resetTmState()"
      />
    </div>
    <div class="mb-4 w-full">
      <Listbox
        v-model="chosenTms"
        :options="tmReadOptions"
        multiple
        checkmark
        option-label="name"
      />
    </div>

    <span class="mb-2 block">Select memory to write into:</span>
    <Select
      v-model="chosenWriteTmId"
      class="mb-4 w-full"
      :options="tmWriteOptions"
      option-label="name"
      option-value="id"
    />

    <span class="mb-2 block">Select glossaries to use:</span>
    <div class="mb-4 w-full">
      <Listbox
        v-model="chosenGlossaries"
        :options="glossaryOptions"
        multiple
        checkmark
        option-label="name"
      />
    </div>

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
