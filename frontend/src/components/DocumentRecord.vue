<script setup lang="ts">
import {computed, ref} from 'vue'

import {Document} from '../client/schemas/Document'

import Button from 'primevue/button'
import RoutingLink from './RoutingLink.vue'

const emit = defineEmits<{
  delete: []
}>()

const props = defineProps<{
  document: Document
  deleteMethod: (id: number) => Promise<any>
}>()

const classes = computed(() => {
  return {
    'border-green-500': props.document.type == 'xliff',
    'border-blue-500': props.document.type == 'txt',
  }
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
    <Button
      label="Delete"
      severity="secondary"
      :disabled="busy"
      @click="deleteFile()"
    />
    <span v-if="status">
      {{ status }}
    </span>
  </div>
</template>
