<script setup lang="ts">
import {onMounted} from 'vue'

import {TmxUsage} from '../client/schemas/TmxUsage'
import {useTmxStore} from '../stores/tmx'

import AppModal from './AppModal.vue'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Select from 'primevue/select'

defineEmits<{
  close: []
}>()
defineProps<{open: boolean}>()

const tmxStore = useTmxStore()
const options = [
  {name: 'Use newest TM', value: 'newest'},
  {name: 'Use oldest TM', value: 'oldest'},
] as {
  name: string
  value: TmxUsage
}[]

onMounted(async () => {
  tmxStore.getTmx()
})
</script>

<template>
  <AppModal :open="open">
    <div class="m-4">
      <p class="mb-2 font-semibold">Select TMX files to use in substitution</p>
      <div class="flex flex-col gap-2 mb-4">
        <label>When segment found in multiple TMXs:</label>
        <Select
          v-model="tmxStore.tmxMode"
          :options="options"
          option-label="name"
          option-value="value"
        />
      </div>
      <Button
        label="Use all TMXs"
        class="mr-2 mb-2"
        severity="secondary"
        @click="tmxStore.selectAll()"
      />
      <Button
        label="Use none of TMXs"
        class="ml-2 mb-2"
        severity="secondary"
        @click="tmxStore.selectNone()"
      />
      <div
        class="flex items-center mb-2"
        v-for="file in tmxStore.tmxFiles"
      >
        <Checkbox
          id="fid"
          v-model="file.selected"
          :binary="true"
        />
        <label
          for="fid"
          class="ml-2"
        >
          {{ file.name }}
        </label>
      </div>
      <Button
        label="Close"
        class="mt-2 w-20"
        @click="$emit('close')"
      />
    </div>
  </AppModal>
</template>
