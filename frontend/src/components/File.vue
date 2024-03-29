<script setup lang="ts">
import {PropType, ref} from 'vue'

import {XliffFile} from '../client/schemas/XliffFile'
import {TmxFile} from '../client/schemas/TmxFile'

import Button from './Button.vue'
import RoutingLink from './RoutingLink.vue'

const emit = defineEmits<{
  delete: []
}>()

const props = defineProps({
  file: {
    type: Object as PropType<XliffFile | TmxFile>,
    required: true,
  },
  type: {
    type: String as PropType<'xliff' | 'tmx'>,
    required: true,
  },
  deleteMethod: {
    type: Function as PropType<(id: number) => Promise<any>>,
    required: true,
  },
})

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
    class="bg-slate-200 my-1 py-1 px-2 border-slate-500 border flex items-baseline">
    <div class="w-48 text-ellipsis whitespace-nowrap overflow-hidden">
      #{{ file.id }} {{ file.name }}
    </div>
    <RoutingLink
      class="ml-2"
      :href="`${type}/${file.id}`"
      :disabled="busy">
      Open
    </RoutingLink>
    <Button
      class="ml-2"
      @click="deleteFile()"
      :disabled="busy">
      Delete
    </Button>
    <span
      class="ml-2"
      v-if="status">
      {{ status }}
    </span>
  </div>
</template>
*
