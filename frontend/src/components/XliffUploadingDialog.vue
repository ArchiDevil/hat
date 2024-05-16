<script setup lang="ts">
import {Ref, ref, computed} from 'vue'
import {MandeError} from 'mande'

import {createXliff, processXliff} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'
import Button from './Button.vue'
import AppCheckbox from './AppCheckbox.vue'

const emit = defineEmits<{
  uploaded: []
  processed: [fileId: number]
}>()

defineProps<{
  title: string
}>()

const input = ref<HTMLInputElement | null>(null)
const file = ref(null) as Ref<File | null>
const uploadedFile = ref(null) as Ref<XliffFile | null>
const uploading = ref(false)
const status = ref('')
const substituteNumbers = ref(false)

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
    status.value = 'Ready for processing'
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
    await processXliff(uploadedFile.value!.id, {
      substitute_numbers: substituteNumbers.value,
    })
    uploading.value = false
    status.value = 'Done!'
    emit('processed', uploadedFile.value!.id)
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}
</script>

<template>
  <div class="border border-slate-500 p-2 min-w-96">
    <div class=" ">
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
      <span
        v-if="status"
        class="ml-2"
      >
        {{ status }}
      </span>
    </div>

    <div
      v-if="processingAvailable"
      class="mt-3"
    >
      <p class="font-semibold">
        Processing options
      </p>
      <AppCheckbox
        v-model:value="substituteNumbers"
        title="Substitute segments with numbers only"
      />
    </div>

    <div
      v-if="processingAvailable"
      class="mt-5"
    >
      <Button
        :disabled="!processingAvailable || uploading"
        @click="startProcessing"
      >
        Start processing
      </Button>
    </div>
  </div>
</template>
