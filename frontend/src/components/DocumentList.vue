<script setup lang="ts">
import {deleteDoc} from '../client/services/DocumentService'
import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'

import DocumentRecord from './DocumentRecord.vue'

const emit = defineEmits<{
  delete: []
  openSettings: [documentId: number]
}>()

defineProps<{
  documents: DocumentWithRecordsCount[]
}>()
</script>

<template>
  <div>
    <DocumentRecord
      v-for="doc in documents"
      :key="doc.id"
      :document="doc"
      :delete-method="deleteDoc"
      type="document"
      @delete="emit('delete')"
      @open-settings="(docId) => $emit('openSettings', docId)"
    />
  </div>
</template>
