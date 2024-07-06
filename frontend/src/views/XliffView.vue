<script setup lang="ts">
import {computed, onMounted, ref, watchEffect} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import {
  getXliff,
  getDownloadXliffLink,
  getXliffRecords,
} from '../client/services/XliffService'
import {XliffFileWithRecordsCount} from '../client/schemas/XliffFileWithRecordsCount'
import {XliffFileRecord} from '../client/schemas/XliffFileRecord'

import Paginator, {PageState} from 'primevue/paginator'

import Link from '../components/Link.vue'
import DocumentPair from '../components/DocumentPair.vue'
import SupportLinks from '../components/SupportLinks.vue'
import PageTitle from '../components/PageTitle.vue'

const route = useRoute()
const router = useRouter()

const documentId = computed(() => {
  return Number(route.params.id)
})

const document = ref<XliffFileWithRecordsCount>()
const records = ref<XliffFileRecord[]>()
const page = computed(() => {
  return Number(route.query['page'] ?? '0')
})
const downloadLink = computed(() => {
  return getDownloadXliffLink(documentId.value)
})
const documentReady = computed(() => {
  return (
    document.value &&
    (document.value.status == 'done' || document.value.status == 'error')
  )
})

watchEffect(async () => {
  if (!document.value || !documentReady.value) {
    return
  }
  records.value = await getXliffRecords(documentId.value, page.value)
})

const loadDocument = async () => {
  document.value = await getXliff(documentId.value)
  const status = document.value.status
  if (status == 'uploaded' || status == 'pending' || status == 'processing') {
    setTimeout(loadDocument, 1000)
  }
}

const updatePage = async (event: PageState) => {
  router.push({
    query: {
      page: event.page,
    },
  })
}

onMounted(async () => {
  await loadDocument()
})
</script>

<template>
  <div>
    <PageTitle title="XLIFF file viewer" />
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <p class="mb-4">Number of records: {{ document?.records_count }}</p>
    <template v-if="documentReady">
      <template v-if="document?.status == 'error'">
        <p class="mt-2 text-red-700">
          Error while processing the document. We still provide you the document
          content. It might be processed partially.
        </p>
        <p class="mt-2">
          If this problem persists, use one of these links to report an issue:
        </p>
        <SupportLinks class="mb-4" />
      </template>

      <template v-if="records">
        <Link
          :href="downloadLink"
          class="mb-4 inline-block"
        >
          Download XLIFF document
        </Link>
        <Paginator
          :rows="100"
          :total-records="document?.records_count"
          :first="page * 100"
          v-on:page="(event) => updatePage(event)"
          v-if="records && records?.length"
        />
        <div>
          <DocumentPair
            v-for="(record, i) in records"
            :key="i"
            :record="record"
          />
        </div>
        <Paginator
          :rows="100"
          :total-records="document?.records_count"
          :first="page * 100"
          v-on:page="(event) => updatePage(event)"
          v-if="records && records?.length"
        />
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
