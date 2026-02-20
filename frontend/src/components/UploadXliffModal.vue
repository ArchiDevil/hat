<script setup lang="ts">
import {Dialog} from 'primevue'
import XliffUploadingDialog from './XliffUploadingDialog.vue'

const visible = defineModel<boolean>({required: true})
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Upload a file"
    :style="{width: '40rem'}"
  >
    <template #default>
      <XliffUploadingDialog @uploaded="visible = false" />
    </template>
  </Dialog>
</template>
