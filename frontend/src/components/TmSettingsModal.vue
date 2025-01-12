<script setup lang="ts">
import {ref, watchEffect, computed} from 'vue'

import {
  getGlossaries,
  getTranslationMemories,
  setGlossaries,
  setTranslationMemories,
} from '../client/services/DocumentService'
import {TmMode} from '../client/schemas/TmMode'
import {useTmStore} from '../stores/tm'

import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Listbox from 'primevue/listbox'
import Select from 'primevue/select'
import {useGlossaryStore} from '../stores/glossary'

const props = defineProps<{
  documentId: number
}>()

const busy = ref(false)
const tmStore = useTmStore()
const glossaryStore = useGlossaryStore()

const modalVisible = defineModel<boolean>()
const chosenTms = ref<{id: number; name: string}[]>([])
const tmReadOptions = computed(() => {
  return tmStore.memories.map((memory) => {
    return {id: memory.id, name: memory.name}
  })
})
const tmWriteOptions = computed(() => {
  return [{id: -1, name: "Don't use TM"}].concat(tmReadOptions.value)
})

const chosenTmId = ref<number>(-1)
const createNewMode = ref(false)
const newTmName = ref('')
const createNewTm = async () => {
  busy.value = true
  await tmStore.create({
    name: newTmName.value,
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
  return glossaryStore.glossaries.map((glossary) => {
    return {id: glossary.id, name: glossary.name}
  })
})

watchEffect(async () => {
  const docMemories = await getTranslationMemories(props.documentId)
  chosenTms.value = docMemories
    .filter((memory) => memory.mode == 'read')
    .map((memory) => {
      return {id: memory.memory.id, name: memory.memory.name}
    })
  chosenTmId.value =
    docMemories.find((memory) => memory.mode == 'write')?.memory.id ?? -1

  const docGlossaries = await getGlossaries(props.documentId)
  chosenGlossaries.value = docGlossaries.map(({glossary}) => {
    return {id: glossary.id, name: glossary.name}
  })
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
  await setGlossaries(props.documentId, {
    glossaries: chosenGlossaries.value.map((glossary) => {
      return {
        id: glossary.id,
      }
    }),
  })
  modalVisible.value = false
  busy.value = false
}
</script>

<template>
  <Dialog
    v-model:visible="modalVisible"
    modal
    :header="`Document #${documentId} settings`"
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
        size="small"
        class="w-full"
        v-model="newTmName"
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
        optionLabel="name"
      />
    </div>

    <span class="mb-2 block">Select memory to write into:</span>
    <Select
      class="mb-4 w-full"
      :options="tmWriteOptions"
      optionLabel="name"
      optionValue="id"
      v-model="chosenTmId"
    />

    <span class="mb-2 block">Select glossaries to use:</span>
    <div class="mb-4 w-full">
      <Listbox
        v-model="chosenGlossaries"
        :options="glossaryOptions"
        multiple
        checkmark
        optionLabel="name"
      />
    </div>

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
