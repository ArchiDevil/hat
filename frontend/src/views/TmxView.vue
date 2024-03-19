<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {getTmx} from '../client/services/TmxService'
import {TmxFileWithRecords} from '../client/schemas/TmxFileWithRecords'

import DocumentPair from '../components/DocumentPair.vue'

const document = ref<TmxFileWithRecords>()

onMounted(async () => {
  const route = useRoute()
  document.value = await getTmx(Number(route.params.id))
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
