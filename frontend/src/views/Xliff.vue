<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {getXliff, getDownloadXliffLink} from '../client/services/XliffService'
import {XliffFileWithRecords} from '../client/schemas/XliffFileWithRecords'

import Link from '../components/Link.vue'
import DocumentPair from '../components/DocumentPair.vue'

const documentId = computed(() => {
  const route = useRoute()
  return Number(route.params.id)
})

const document = ref<XliffFileWithRecords>()

const downloadLink = computed(() => {
  return getDownloadXliffLink(documentId.value)
})

onMounted(async () => {
  document.value = await getXliff(documentId.value)
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
