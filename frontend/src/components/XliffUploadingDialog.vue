<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {MandeError} from 'mande'

import {createXliff, processXliff} from '../client/services/XliffService'
import Button from './Button.vue'
import {XliffFile} from '../client/schemas/XliffFile'

const emit = defineEmits<{
  uploaded: []
  processed: []
}>()

defineProps({
  title: {
    type: String,
    required: true,
  },
})

const input = ref<HTMLInputElement | null>(null)
const file = ref(null) as Ref<File | null>
const uploadedFile = ref(null) as Ref<XliffFile | null>
const uploading = ref(false)
const status = ref('')

const processingAvailable = computed(() => uploadedFile.value != null)

const preProcessFile = async () => {
  status.value = ''
  const inputElement = input.value
  if (!inputElement?.files) {
    return
  }

  file.value = inputElement.files[0]

  try {
    uploading.value = true
    status.value = 'Uploading...'
    uploadedFile.value = await createXliff({file: file.value})
    uploading.value = false
    status.value = 'Done!'
    emit('uploaded')
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}

const startProcessing = async () => {
  if (!processingAvailable.value) {
    return
  }

  status.value = ''

  try {
    uploading.value = true
    status.value = 'Processing...'
    await processXliff(uploadedFile.value!.id)
    uploading.value = false
    status.value = 'Done!'
    emit('processed')
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
      accept=".xliff"
      :disabled="uploading"
      @change="preProcessFile"
    >
    <Button
      class="ml-2"
      :disabled="!processingAvailable || uploading"
      @click="startProcessing"
    >
      Start processing
    </Button>
    <span
      v-if="status"
      class="ml-2"
    >
      {{ status }}
    </span>
  </div>
</template>
