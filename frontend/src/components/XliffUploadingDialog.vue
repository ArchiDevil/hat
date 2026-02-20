<script setup lang="ts">
import {ref} from 'vue'
import {MandeError} from 'mande'
import {Checkbox, FileUpload, FileUploadUploaderEvent} from 'primevue'
import {uploadXliff} from '../client/services/DocumentService'

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
    await uploadXliff({
      file: files[0],
      update_approved: updateApproved.value,
    })
    uploading.value = false
    status.value = 'Uploading finished. You may choose another file.'
    if (removeFileCb.value) removeFileCb.value(0)
    emit('uploaded')
  } catch (error: unknown) {
    uploading.value = false
    status.value = `${(error as MandeError).message} :(`
  }
}

const updateApproved = ref(false)
</script>

<template>
  <div class="min-w-96">
    <div class="flex items-center my-2">
      <Checkbox
        id="umt"
        v-model="updateApproved"
        :binary="true"
      />
      <label
        for="umt"
        class="ml-2 cursor-pointer"
        @click="updateApproved = !updateApproved"
      >
        <span class="text-red-600 font-semibold">Warning:</span> Replace
        approved segments
      </label>
    </div>
    <FileUpload
      mode="advanced"
      custom-upload
      accept=".xliff"
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
        <span v-if="!status">Choose an XLIFF file to upload.</span>
      </template>
    </FileUpload>
  </div>
</template>
