<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {
  getXliff,
  getDownloadXliffLink,
  getXliffRecords,
} from '../client/services/XliffService'
import { XliffFile } from '../client/schemas/XliffFile'
import {XliffFileRecord} from '../client/schemas/XliffFileRecord'

import Link from '../components/Link.vue'
import DocumentPair from '../components/DocumentPair.vue'
import SupportLinks from '../components/SupportLinks.vue'

const documentId = computed(() => {
  const route = useRoute()
  return Number(route.params.id)
})

const document = ref<XliffFile>()
const records = ref<XliffFileRecord[]>()

const downloadLink = computed(() => {
  return getDownloadXliffLink(documentId.value)
})

const documentStatus = computed(() => {
  return document.value?.status
})

const updateRecords = async () => {
  if (document.value?.status === 'done' || document.value?.status == 'error') {
    records.value = await getXliffRecords(documentId.value)
  } else {
    setTimeout(updateRecords, 1000)
  }
}

onMounted(async () => {
  document.value = await getXliff(documentId.value)
  await updateRecords()
})
</script>

<template>
  <div>
    <h1 class="font-bold text-2xl pt-8">XLIFF file viewer</h1>
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <template v-if="documentStatus == 'done' || documentStatus == 'error'">
      <template v-if="documentStatus == 'error'">
        <p class="mt-2 text-red-700">
          Error while processing the document. We still provide you the document
          content. It might be processed partially.
        </p>
        <p class="mt-2">
          If this problem persists, use one of these links to report an issue:
        </p>
        <SupportLinks class="mb-4"/>
      </template>

      <template v-if="records">
        <p>Number of records: {{ records.length }}</p>
        <Link
          :href="downloadLink"
          class="mb-4 inline-block"
        >
          Download XLIFF document
        </Link>
        <div>
          <DocumentPair
            v-for="record in records"
            :key="record.source"
            :record="record"
          />
        </div>
      </template>
      <template v-else>
        <p>Loading...</p>
      </template>
    </template>
    <template v-else>
      <p class="mt-2">
        The document is being processed right now. This should not take long.
      </p>
      <p class="mt-2">
        If the file is processed too long (it not should take more than 5-10
        minutes), use one of these links to report an issue:
      </p>
      <SupportLinks />
    </template>
  </div>
</template>
