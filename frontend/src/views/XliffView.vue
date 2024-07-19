<script setup lang="ts">
import {computed, onMounted, watchEffect} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import {useXliffStore} from '../stores/xliff'

import Paginator, {PageState} from 'primevue/paginator'

import Link from '../components/Link.vue'
import DocSegment from '../components/DocSegment.vue'
import SubstitutionsList from '../components/xliff/SubstitutionsList.vue'
import LoadingMessage from '../components/xliff/LoadingMessage.vue'
import ProcessingErrorMessage from '../components/xliff/ProcessingErrorMessage.vue'
import RoutingLink from '../components/RoutingLink.vue'

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

const onSegmentUpdate = (record: number, text: string) => {
  store.updateRecord(record, text)
}

const onSegmentCommit = (record: number, text: string) => {
  onSegmentUpdate(record, text)
  store.focusNextSegment()
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
  <div class="w-full h-screen grid grid-rows-[1fr_auto] overflow-hidden">
    <div class="bg-surface-0 border-b">
      <div>
        <h2 class="text-xl font-bold mt-4 mb-4 ml-4 inline-block">
          {{ store.document?.name }}
        </h2>
        <RoutingLink
          name="home"
          class="ml-4"
          title="Return to main page"
        />
      </div>
      <p class="ml-4">Number of records: {{ store.document?.records_count }}</p>
      <template v-if="store.documentReady && !store.documentLoading">
        <ProcessingErrorMessage
          v-if="store.document?.status == 'error'"
          class="mt-2"
        />
      </template>
      <div
        v-if="store.records"
        class="flex flex-row gap-4 items-center"
      >
        <Paginator
          :rows="100"
          :total-records="store.document?.records_count"
          :first="page * 100"
          v-on:page="(event) => updatePage(event)"
          v-if="store.records && store.records?.length"
          class="inline-block"
        />
        <Link
          :href="store.downloadLink"
          class="inline-block"
          title="Download document"
        />
      </div>
    </div>
    <div class="overflow-hidden pt-2 grid grid-cols-[auto_1fr] gap-2">
      <template v-if="store.documentReady && !store.documentLoading">
        <template v-if="store.records">
          <div class="flex flex-col gap-1 pb-1 overflow-scroll">
            <DocSegment
              v-for="(record, idx) in store.records"
              :key="record.id"
              editable
              :record="record"
              :disabled="record.loading"
              :focused-id="store.currentFocusId"
              @commit="(text) => onSegmentCommit(record.id, text)"
              @update-record="(text) => onSegmentUpdate(record.id, text)"
              @focus="store.focusSegment(idx)"
            />
          </div>
          <SubstitutionsList
            class="border-l border-y rounded-l-lg px-2 mb-1 overflow-scroll"
          />
        </template>
        <p v-else>Loading...</p>
      </template>
      <LoadingMessage
        v-else
        class="mt-2"
      />
    </div>
  </div>
</template>
