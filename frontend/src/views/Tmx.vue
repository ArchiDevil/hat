<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {apiAccessor} from '../api'
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

onMounted(async () => {
  const route = useRoute()
  const api = apiAccessor(`/tmx/${route.params.id}`)
  document.value = await api.get<Document>()
})
</script>

<template>
  <div>
    <h1 class="font-bold text-2xl pt-8">TMX file viewer</h1>
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <p class="mb-4">Number of records: {{ document?.records.length }}</p>
    <div>
      <DocumentPair
        :record="record"
        v-for="record in document?.records"
        :key="record.source" />
    </div>
  </div>
</template>
