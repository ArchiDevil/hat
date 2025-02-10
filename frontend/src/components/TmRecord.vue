<script setup lang="ts">
import {ref} from 'vue'

import {TranslationMemory} from '../client/schemas/TranslationMemory'

import Button from 'primevue/button'
import RoutingLink from './RoutingLink.vue'

const emit = defineEmits<{
  delete: []
}>()

const props = defineProps<{
  file: TranslationMemory
  deleteMethod: () => Promise<unknown>
}>()

const busy = ref(false)
const status = ref()

const deleteFile = async () => {
  try {
    busy.value = true
    status.value = 'Busy...'
    await props.deleteMethod()
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
      :title="file.name"
    >
      #{{ file.id }} {{ file.name }}
    </div>
    <RoutingLink
      name="tm"
      :params="{id: file.id}"
      :disabled="busy"
      title="Open"
    />
    <span v-if="status">
      {{ status }}
    </span>
    <Button
      class="ml-auto"
      label="Delete"
      severity="danger"
      :disabled="busy"
      @click="deleteFile()"
    />
  </div>
</template>
