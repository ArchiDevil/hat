<script setup lang="ts">
import {ref, watchEffect, computed} from 'vue'

import {
  getTranslationMemories,
  setTranslationMemories,
} from '../client/services/DocumentService'
import {TmMode} from '../client/schemas/TmMode'
import {useTmStore} from '../stores/tm'

import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Listbox from 'primevue/listbox'
import Select from 'primevue/select'

const props = defineProps<{
  documentId: number
}>()

const modalVisible = defineModel<boolean>()
const chosenTms = ref<{id: number; name: string}[]>([])
const readOptions = computed(() => {
  return useTmStore().memories.map((memory) => {
    return {id: memory.id, name: memory.name}
  })
})
const writeOptions = computed(() => {
  return [{id: -1, name: "Don't use TM"}].concat(readOptions.value)
})

const busy = ref(false)
const chosenTmId = ref<number>(-1)

watchEffect(async () => {
  const docMemories = await getTranslationMemories(props.documentId)
  chosenTms.value = docMemories
    .filter((memory) => memory.mode == 'read')
    .map((memory) => {
      return {id: memory.memory.id, name: memory.memory.name}
    })
  chosenTmId.value =
    docMemories.find((memory) => memory.mode == 'write')?.memory.id ?? -1
})

const save = async () => {
  busy.value = true
  await setTranslationMemories(props.documentId, {
    memories: chosenTms.value
      .map((tm) => {
        return {
          id: tm.id,
          mode: 'read' as TmMode,
        }
      })
      .concat(
        chosenTmId.value !== -1
          ? [{id: chosenTmId.value, mode: 'write' as TmMode}]
          : []
      ),
  })
  modalVisible.value = false
  busy.value = false
}
</script>

<template>
  <Dialog
    v-model:visible="modalVisible"
    modal
    header="Select memories to use"
    :style="{width: '32rem'}"
  >
    <span class="mb-2 block">Select memories to read from:</span>
    <div class="mb-4 w-full">
      <Listbox
        v-model="chosenTms"
        :options="readOptions"
        multiple
        checkmark
        optionLabel="name"
      />
    </div>
    <span class="mb-2 block">Select memory to write into:</span>
    <Select
      class="mb-4 w-full"
      :options="writeOptions"
      optionLabel="name"
      optionValue="id"
      v-model="chosenTmId"
    />
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        label="Save"
        :disabled="busy"
        @click="save"
      />
    </div>
  </Dialog>
</template>
