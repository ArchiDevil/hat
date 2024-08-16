<script setup lang="ts">
import {ref} from 'vue'
import {MandeError} from 'mande'

import {createMemoryFromFile} from '../client/services/TmsService'

import FileUpload, {FileUploadUploaderEvent} from 'primevue/fileupload'

const emit = defineEmits<{
  uploaded: []
}>()

defineProps<{
  title: string
}>()

const uploading = ref(false)
const status = ref('')

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
    status.value = 'Uploading finished!'
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
      customUpload
      :disabled="uploading"
      @uploader="(event: FileUploadUploaderEvent) => uploadFile(event)"
    >
      <template #content="{files}">
        <div v-if="files.length">{{ files[0].name }} is waiting to upload.</div>
        <div v-else>{{ status }}</div>
      </template>
      <template #empty>
        <span v-if="!status">Choose TMX file to upload.</span>
      </template>
    </FileUpload>
  </div>
</template>
