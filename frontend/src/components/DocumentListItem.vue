<script setup lang="ts">
import {computed, ref} from 'vue'
import {Button, ProgressBar} from 'primevue'

import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'
import RoutingLink from './RoutingLink.vue'
import {hasPermission} from '../utilities/auth'

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
  return `Words: ${props.document.approved_word_count}/${props.document.total_word_count}`
})

const progressValue = computed(() => {
  if (props.document.total_word_count === 0) return 0
  return (
    (props.document.approved_word_count / props.document.total_word_count) * 100
  )
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
    <div class="w-[24rem] truncate">
      <RoutingLink
        name="document"
        :params="{id: document.id}"
        :disabled="busy"
        :title="document.name"
      >
        #{{ document.id }} {{ document.name }}
      </RoutingLink>
    </div>
    <div
      class="border border-surface rounded-lg p-2 w-16 text-center uppercase"
      :class="classes"
    >
      {{ document.type }}
    </div>
    <ProgressBar
      class="w-24 h-2 self-center"
      :value="progressValue"
      :show-value="false"
      :title="progressBarTitle"
    />
    <span v-if="status">
      {{ status }}
    </span>
    <Button
      v-if="hasPermission('document:update')"
      icon="pi pi-cog"
      severity="secondary"
      :disabled="busy"
      variant="text"
      rounded
      @click="$emit('openSettings', document.id)"
    />
    <Button
      v-if="hasPermission('document:delete')"
      class="ml-auto"
      icon="pi pi-trash"
      severity="danger"
      :disabled="busy"
      variant="text"
      rounded
      @click="deleteFile()"
    />
  </div>
</template>
