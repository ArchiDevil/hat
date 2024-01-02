<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {apiAccessor} from '../api'

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
  const urlParams = new URLSearchParams(window.location.search)
  const fileId = urlParams.get('id')

  if (fileId) {
    const api = apiAccessor(`/tmx/${fileId}`)
    document.value = await api.get<Document>()
  }
})
</script>

<template>
  <div>
    <h1 class="font-bold text-2xl pt-8">TMX file viewer</h1>
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <p class="mb-4">Number of records: {{ document?.records.length }}</p>
    <div class="grid grid-cols-2 gap-2">
      <template v-for="record in document?.records.slice(0, 50)">
        <p class="border-2 rounded p-2">
          {{ record.source }}
        </p>
        <p class="border-2 rounded p-2">
          {{ record.target }}
        </p>
      </template>
    </div>
  </div>
</template>
