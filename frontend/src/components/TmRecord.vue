<script setup lang="ts">
import {ref} from 'vue'

import {Document} from '../client/schemas/Document'
import {TmxFile} from '../client/schemas/TmxFile'

import Button from 'primevue/button'
import RoutingLink from './RoutingLink.vue'

const emit = defineEmits<{
  delete: []
}>()

const props = defineProps<{
  file: Document | TmxFile
  deleteMethod: (id: number) => Promise<any>
}>()

const busy = ref(false)
const status = ref()

const deleteFile = async () => {
  try {
    busy.value = true
    status.value = 'Busy...'
    await props.deleteMethod(props.file.id)
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
      :title="file.name"
    >
      #{{ file.id }} {{ file.name }}
    </div>
    <RoutingLink
      name="tmx"
      :params="{id: file.id}"
      :disabled="busy"
      title="Open"
    />
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
