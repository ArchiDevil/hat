<script setup lang="ts">
import {computed, ref} from 'vue'

import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'

import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'

import RoutingLink from './RoutingLink.vue'

const emit = defineEmits<{
  delete: []
  openSettings: [documentId: number]
}>()

const props = defineProps<{
  document: DocumentWithRecordsCount
  deleteMethod: (id: number) => Promise<unknown>
}>()

const classes = computed(() => {
  return {
    'border-green-500': props.document.type == 'xliff',
    'border-blue-500': props.document.type == 'txt',
  }
})

const progressBarTitle = computed(() => {
  return `Segments: ${props.document.approved_records_count}/${props.document.records_count}`
})

const busy = ref(false)
const status = ref()

const deleteFile = async () => {
  try {
    busy.value = true
    status.value = 'Busy...'
    await props.deleteMethod(props.document.id)
    status.value = undefined
  } catch (error) {
    console.log(error)
    // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
    status.value = `${error} :(`
  } finally {
    busy.value = false
    emit('delete')
  }
}
</script>

<template>
  <div
    class="my-1 py-1 px-2 border flex gap-8 items-baseline rounded-border border-surface bg-surface-50"
  >
    <div
      class="w-[24rem] text-ellipsis whitespace-nowrap overflow-hidden"
      :title="document.name"
    >
      #{{ document.id }} {{ document.name }}
    </div>
    <RoutingLink
      name="document"
      :params="{id: document.id}"
      :disabled="busy"
      title="Open"
    />
    <div
      class="border rounded-lg p-2 w-16 text-center uppercase"
      :class="classes"
    >
      {{ document.type }}
    </div>
    <ProgressBar
      class="w-24 h-2 self-center"
      :value="(document.approved_records_count / document.records_count) * 100"
      :show-value="false"
      :title="progressBarTitle"
    />
    <span v-if="status">
      {{ status }}
    </span>
    <Button
      label="Settings"
      severity="secondary"
      :disabled="busy"
      @click="$emit('openSettings', document.id)"
    />
    <Button
      class="ml-auto"
      label="Delete"
      severity="danger"
      :disabled="busy"
      @click="deleteFile()"
    />
  </div>
</template>
