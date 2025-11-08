<script setup lang="ts">
import {computed, ref, triggerRef, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useQuery} from '@pinia/colada'

import Paginator, {PageState} from 'primevue/paginator'
import ProgressBar from 'primevue/progressbar'

import Link from '../components/NavLink.vue'
import DocSegment from '../components/DocSegment.vue'
import SubstitutionsList from '../components/document/SubstitutionsList.vue'
import ProcessingErrorMessage from '../components/document/ProcessingErrorMessage.vue'
import RoutingLink from '../components/RoutingLink.vue'
import DocumentSkeleton from '../components/document/DocumentSkeleton.vue'
import FilterPanel from '../components/document/FilterPanel.vue'
import {
  getDoc,
  getDocRecords,
  getDownloadDocLink,
  updateDocRecord,
} from '../client/services/DocumentService'
import {useDocStore} from '../stores/document'

// TODO: 100 records per page is a magic number, it should be obtained from
// the server side somehow

const route = useRoute()
const router = useRouter()

const documentId = computed(() => {
  return Number(route.params.id)
})
const page = computed(() => {
  return Number(route.query.page ?? '0')
})

const {
  data: document,
  isLoading: documentLoading,
  refetch: refetchDoc,
} = useQuery({
  key: () => ['document', documentId.value],
  query: () => getDoc(documentId.value),
  placeholderData: <T>(prevData: T) => prevData,
})

watch(document, (newVal) => {
  if (
    newVal &&
    !documentLoading.value &&
    newVal.status !== 'done' &&
    newVal.status !== 'error'
  ) {
    setTimeout(refetchDoc, 5000)
  }
})

const documentReady = computed(() => {
  const doc = document.value
  if (!doc) return false
  return doc.status == 'done' || doc.status == 'error'
})

const documentDownloadLink = computed(() => {
  return getDownloadDocLink(documentId.value)
})

const recordsCount = computed(() => recordsData.value?.total_records)

const translationProgress = computed(() => {
  const doc = document.value
  if (!doc) return 0
  return (doc.approved_records_count / doc.records_count) * 100
})

const updatePage = async (event: PageState) => {
  await router.push({query: {page: event.page}})
}

const sourceFilter = ref('')
const targetFilter = ref('')

const {data: recordsData} = useQuery({
  key: () => [
    'doc-records',
    documentId.value,
    page.value,
    sourceFilter.value,
    targetFilter.value,
  ],
  query: async () => {
    const data = await getDocRecords(
      documentId.value,
      page.value,
      sourceFilter.value,
      targetFilter.value
    )
    return {
      page: data.page,
      total_records: data.total_records,
      records: data.records.map((record) => ({
        ...record,
        loading: false,
      })),
    }
  },
  enabled: () =>
    !documentLoading.value &&
    (document.value?.status == 'done' || document.value?.status == 'error'),
  placeholderData: <T>(prevData: T) => prevData,
})

const onSegmentUpdate = async (
  id: number,
  text: string,
  approved: boolean,
  updateRepeats: boolean
) => {
  if (!document.value || !recordsData.value) {
    return
  }

  // TODO: this should be a kind of mutation instead of manual updating
  const idx = recordsData.value.records.findIndex((record) => record.id === id)
  if (idx < 0) {
    console.error('Record not found')
    return
  }
  recordsData.value.records[idx].loading = true
  triggerRef(recordsData)

  const newRecord = await updateDocRecord(id, {
    target: text,
    approved: approved,
    update_repetitions: updateRepeats,
  })
  recordsData.value.records[idx] = {
    ...newRecord,
    loading: false,
    repetitions_count: recordsData.value.records[idx].repetitions_count,
  }
  triggerRef(recordsData)

  // rerequest a document to update its records count
  // this is because more than one record can be updated by a backend
  // (repetitions, for example)
  await refetchDoc()
  await useDocStore().updateDocument(documentId.value)
}

const onSegmentCommit = async (
  id: number,
  text: string,
  updateRepeats: boolean,
  idx: number
) => {
  await onSegmentUpdate(id, text, true, updateRepeats)
  focusSegment(idx + 1)
}

const focusSegment = (newIdx: number) => {
  if (!recordsData.value?.records.length) return
  focusedSegmentIdx.value = Math.min(
    newIdx,
    recordsData.value?.records.length - 1
  )
}

const focusedSegmentIdx = ref<number>()
const currentSegmentId = computed(() => {
  if (!recordsData.value || focusedSegmentIdx.value == undefined)
    return undefined
  if (focusedSegmentIdx.value >= recordsData.value.records.length)
    return undefined
  return recordsData.value.records[focusedSegmentIdx.value].id
})
</script>

<template>
  <div
    v-if="documentReady"
    class="w-full h-screen grid grid-rows-[auto_1fr] overflow-hidden"
  >
    <div class="bg-surface-0 border-b">
      <div>
        <h2 class="text-xl font-bold my-4 ml-4 inline-block">
          {{ document?.name }}
        </h2>
        <RoutingLink
          name="home"
          class="ml-4"
          title="Return to main page"
        />
      </div>
      <div class="ml-4 flex flex-row gap-2 items-baseline">
        Progress:
        <ProgressBar
          class="w-64 h-2 inline-block"
          :value="translationProgress"
          :show-value="false"
        />
        {{ document?.approved_records_count }} /
        {{ document?.records_count }}
        <Link
          :href="documentDownloadLink"
          class="inline-block"
          title="Download in the current state"
        />
      </div>
      <template v-if="documentReady && !documentLoading">
        <ProcessingErrorMessage
          v-if="document?.status == 'error'"
          class="mt-2 ml-4"
        />
      </template>

      <FilterPanel
        @source-filter-update="(val) => (sourceFilter = val)"
        @target-filter-update="(val) => (targetFilter = val)"
      />

      <div
        v-if="documentReady"
        class="flex flex-row gap-4 items-center"
      >
        <Paginator
          :rows="100"
          :total-records="recordsCount"
          :first="page * 100"
          class="inline-block"
          @page="(event) => updatePage(event)"
        />
      </div>
    </div>
    <div
      class="overflow-hidden grid grid-cols-[1fr_auto] items-start bg-surface-50"
    >
      <template v-if="documentReady">
        <template v-if="recordsData">
          <div
            class="grid grid-cols-[auto_auto_1fr_1fr_auto] gap-1 overflow-scroll mb-1 max-h-full py-2"
          >
            <DocSegment
              v-for="(record, idx) in recordsData?.records"
              :id="record.id"
              :key="record.id"
              editable
              :source="record.source"
              :target="record.target"
              :disabled="record.loading"
              :focused-id="currentSegmentId"
              :approved="record.approved"
              :repetitions-count="record.repetitions_count"
              @commit="
                (text, updateRepeats) =>
                  onSegmentCommit(record.id, text, updateRepeats, idx)
              "
              @update-record="
                (text, updateRepeats) =>
                  onSegmentUpdate(record.id, text, false, updateRepeats)
              "
              @focus="focusedSegmentIdx = idx"
            />
          </div>
          <SubstitutionsList
            class="border-l"
            :document-id="documentId"
            :current-segment-id="currentSegmentId"
          />
        </template>
        <p v-else>
          Loading...
        </p>
      </template>
    </div>
  </div>
  <DocumentSkeleton v-else />
</template>
