<script setup lang="ts">
import {ref} from 'vue'
import {MandeError} from 'mande'

import {createMemoryFromFile} from '../client/services/TmsService'

import FileUpload, {FileUploadUploaderEvent} from 'primevue/fileupload'

const emit = defineEmits<{
  uploaded: []
}>()

const uploading = ref(false)
const status = ref('')

const removeFileCb = ref<(idx: number) => void>()
const saveCallback = (removeFileCallback: (idx: number) => void) => {
  removeFileCb.value = removeFileCallback
}

const uploadFile = async (event: FileUploadUploaderEvent) => {
  const files = event.files as File[]
  if (files.length != 1) {
    return
  }

  try {
    uploading.value = true
    status.value = 'Uploading...'
    await createMemoryFromFile({file: files[0]})
    uploading.value = false
    status.value = 'Uploading finished. You may choose another file.'
    if (removeFileCb.value) removeFileCb.value(0)
    emit('uploaded')
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}
</script>

<template>
  <div class="min-w-96 flex flex-col gap-2">
    <FileUpload
      mode="advanced"
      accept=".tmx"
      custom-upload
      auto
      :disabled="uploading"
      @uploader="(event: FileUploadUploaderEvent) => uploadFile(event)"
    >
      <template #content="{removeFileCallback}">
        <span :ref="() => saveCallback(removeFileCallback)" />
        <div v-if="status.length > 0">
          {{ status }}
        </div>
      </template>
      <template #empty>
        <span>Choose TMX file to upload.</span>
      </template>
    </FileUpload>
  </div>
</template>
