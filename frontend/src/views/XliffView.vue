<script setup lang="ts">
import {computed, onMounted, watchEffect} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import Paginator, {PageState} from 'primevue/paginator'

import Link from '../components/Link.vue'
import DocSegment from '../components/DocSegment.vue'
import SupportLinks from '../components/SupportLinks.vue'
import PageTitle from '../components/PageTitle.vue'
import {useXliffStore} from '../stores/xliff'

// TODO: 100 records per page is a magic number, it should be obtained from
// the server side somehow

const route = useRoute()
const router = useRouter()
const store = useXliffStore()

const documentId = computed(() => {
  return Number(route.params.id)
})
const page = computed(() => {
  return Number(route.query['page'] ?? '0')
})

const loadDocument = async () => {
  store.loadDocument(documentId.value)
  if (!store.document) {
    setTimeout(loadDocument, 1000)
  }
}

const updatePage = async (event: PageState) => {
  router.push({query: {page: event.page}})
}

const onSegmentCommit = (record: number, text: string) => {
  store.updateRecord(record, text)
  if (store.currentFocusIdx != 99) {
    store.focusNextSegment()
  }
}

const onSegmentUpdate = (record: number, text: string) => {
  store.updateRecord(record, text)
}

watchEffect(async () => {
  if (!store.document || !store.documentReady) {
    return
  }
  store.loadRecords(page.value)
})

onMounted(async () => {
  await loadDocument()
})
</script>

<template>
  <div>
    <PageTitle title="XLIFF file viewer" />
    <h2 class="text-xl font-bold mt-2 mb-4">{{ store.document?.name }}</h2>
    <p>Number of records: {{ store.document?.records_count }}</p>
    <template v-if="store.documentReady && !store.documentLoading">
      <template v-if="store.document?.status == 'error'">
        <p class="mt-2 text-red-700">
          Error while processing the document. We still provide you the document
          content. It might be processed partially.
        </p>
        <p class="mt-2">
          If this problem persists, use one of these links to report an issue:
        </p>
        <SupportLinks class="mb-4" />
      </template>

      <template v-if="store.records">
        <Link
          :href="store.downloadLink ?? ''"
          class="mb-4 inline-block"
        >
          Download XLIFF document
        </Link>
        <Paginator
          :rows="100"
          :total-records="store.document?.records_count"
          :first="page * 100"
          v-on:page="(event) => updatePage(event)"
          v-if="store.records && store.records?.length"
        />
        <div class="flex flex-col gap-1">
          <DocSegment
            v-for="(record, idx) in store.records"
            :key="record.id"
            editable
            :record="record"
            :disabled="record.loading"
            :focused-id="store.currentFocusId"
            @commit="(text) => onSegmentCommit(record.id, text)"
            @update-record="(text) => onSegmentUpdate(record.id, text)"
            @focus="store.currentFocusIdx = idx"
          />
        </div>
        <Paginator
          :rows="100"
          :total-records="store.document?.records_count"
          :first="page * 100"
          v-on:page="(event) => updatePage(event)"
          v-if="store.records && store.records?.length"
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
