<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {apiAccessor} from '../api'
import Link from '../components/Link.vue'
import DocumentPair from '../components/DocumentPair.vue'

interface Document {
  id: number
  name: string
  records: Record[]
}

interface Record {
  source: string
  target: string
}

const document = ref<Document>()
const downloadLink = computed(() => {
  if (document.value) {
    return `/api/xliff/${document.value.id}/download`
  }
})

onMounted(async () => {
  const route = useRoute()
  const api = apiAccessor(`/xliff/${route.params.id}`)
  document.value = await api.get<Document>()
})
</script>

<template>
  <div>
    <h1 class="font-bold text-2xl pt-8">XLIFF file viewer</h1>
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <p>Number of records: {{ document?.records.length }}</p>
    <Link
      :href="downloadLink"
      class="mb-4 block">
      Download
    </Link>
    <div>
      <DocumentPair
        :record="record"
        v-for="record in document?.records"
        :key="record.source" />
    </div>
  </div>
</template>
