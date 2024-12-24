<script setup lang="ts">
import {ref} from 'vue'

import {GlossaryResponse} from '../../client/schemas/GlossaryResponse'

import Button from 'primevue/button'
import RoutingLink from '../RoutingLink.vue'

const emit = defineEmits<{
  delete: []
}>()

const props = defineProps<{
  file: GlossaryResponse
  deleteMethod: () => Promise<any>
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
      #{{ file.id }} {{ file.name ?? 'Noname' }}
    </div>
    <RoutingLink
      name="glossary"
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
