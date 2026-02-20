<script setup lang="ts">
import {Dialog} from 'primevue'
import {useRouter} from 'vue-router'
import DocUploadingDialog from './DocUploadingDialog.vue'

const visible = defineModel<boolean>({required: true})
const router = useRouter()
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Upload a file"
    :style="{width: '40rem'}"
  >
    <template #default>
      <DocUploadingDialog
        title="Select a file to upload:"
        @processed="
          (fileId) => router.push({name: 'document', params: {id: fileId}})
        "
      />
    </template>
  </Dialog>
</template>
