<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {MandeError} from 'mande'

import Button from './Button.vue'
import {createTmx} from '../client/services/TmxService'

const emit = defineEmits<{
  uploaded: []
}>()

defineProps<{
  title: string
}>()

const file = ref(null) as Ref<File | null>
const input = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const status = ref('')

const uploadAvailable = computed(() => file.value != null)

const updateFiles = () => {
  status.value = ''
  const element = input.value as HTMLInputElement
  if (!element.files) {
    return
  }
  file.value = element.files[0]
}

const uploadFile = async () => {
  if (!uploadAvailable.value) {
    return
  }

  const element = input.value as HTMLInputElement
  const attachedFile = element.files![0]

  try {
    uploading.value = true
    status.value = 'Uploading...'
    await createTmx({file: attachedFile})
    uploading.value = false
    status.value = 'Done!'
    emit('uploaded')
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}
</script>

<template>
  <div class="p-2 min-w-96 border border-slate-500">
    <label
      for="file"
      class="font-semibold mr-2"
    >
      {{ title }}
    </label>
    <input
      id="file-input"
      ref="input"
      type="file"
      accept=".tmx"
      @change="updateFiles"
    >
    <Button
      class="ml-2"
      :disabled="!uploadAvailable || uploading"
      @click="uploadFile"
    >
      Upload
    </Button>
    <span
      v-if="status"
      class="ml-2"
    >
      {{ status }}
    </span>
  </div>
</template>
