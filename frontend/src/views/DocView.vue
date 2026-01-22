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
import ToolsPanel from '../components/document/ToolsPanel.vue'
import TmSearchModal from '../components/TmSearchModal.vue'
import RecordCommentModal from '../components/document/RecordCommentModal.vue'
import AddTermModal from '../components/document/AddTermModal.vue'
import SegmentHistoryModal from '../components/document/SegmentHistoryModal.vue'

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
    // TODO: it must refetch infinitely until some of these conditions are met
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

const translationProgress = computed(() => {
  const doc = document.value
  if (!doc || doc.total_word_count === 0) return 0
  return (doc.approved_word_count / doc.total_word_count) * 100
})

const updatePage = async (event: PageState) => {
  await router.push({query: {page: event.page}})
}

const sourceFilter = ref('')
const targetFilter = ref('')

const {data: recordsData, refetch: refetchRecords} = useQuery({
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
      sourceFilter.value.trim(),
      targetFilter.value.trim()
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
  // be cautious as incorrect changes here will trigger a lot of updates
  enabled: () => documentReady.value,
  placeholderData: <T>(prevData: T) => prevData,
})

const recordsCount = computed(() => recordsData.value?.total_records)

const onSegmentUpdate = async (
  id: number,
  text: string,
  approved: boolean,
  updateRepeats: boolean,
  commit: boolean
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

  await updateDocRecord(id, {
    target: text,
    approved: approved,
    update_repetitions: updateRepeats,
  })
  if (commit) {
    await refetchRecords()
  } else {
    recordsData.value.records[idx].loading = false
  }
  triggerRef(recordsData)

  // rerequest a document to update its records count this is because more than
  // one record can be updated by a backend (repetitions, for example)
  await refetchDoc()
  await useDocStore().updateDocument(documentId.value)
}

const onSegmentCommit = async (
  id: number,
  text: string,
  updateRepeats: boolean,
  idx: number
) => {
  await onSegmentUpdate(id, text, true, updateRepeats, true)
  focusSegment(idx + 1)
}

const focusSegment = (newIdx: number) => {
  if (!recordsData.value?.records.length) return
  focusedSegmentIdx.value = Math.min(
    newIdx,
    recordsData.value?.records.length - 1
  )
}

const onSegmentStartEdit = (id: number) => {
  if (!document.value || !recordsData.value) {
    return
  }

  const idx = recordsData.value.records.findIndex((record) => record.id === id)
  if (idx < 0) {
    console.error('Record not found')
    return
  }

  recordsData.value.records[idx].approved = false
  triggerRef(recordsData)
}

const focusedSegmentIdx = ref<number>()
const currentSegmentId = computed(() => {
  if (!recordsData.value || focusedSegmentIdx.value == undefined)
    return undefined
  if (focusedSegmentIdx.value >= recordsData.value.records.length)
    return undefined
  return recordsData.value.records[focusedSegmentIdx.value].id
})

const showTmSearchModal = ref(false)

const showCommentsModal = ref(false)
const commentsRecordId = ref<number>()
const onAddComment = (recordId: number) => {
  commentsRecordId.value = recordId
  showCommentsModal.value = true
}

const showAddTermModal = ref(false)

const showHistoryModal = ref(false)
const historyRecordId = ref<number>()
const onShowHistory = (recordId: number) => {
  historyRecordId.value = recordId
  showHistoryModal.value = true
}
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
        {{ document?.approved_word_count }} /
        {{ document?.total_word_count }} words <span class="text-gray-500">({{
          document !== undefined
            ? Number(
              document.approved_word_count / document.total_word_count * 100
            ).toFixed(2)
            : 0.0
        }}%)</span>
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

      <ToolsPanel
        @source-filter-update="(val) => (sourceFilter = val)"
        @target-filter-update="(val) => (targetFilter = val)"
        @open-tm-search="showTmSearchModal = true"
        @open-add-term="showAddTermModal = true"
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
              :focused="currentSegmentId == record.id"
              :approved="record.approved"
              :repetitions-count="record.repetitions_count"
              :has-comments="record.has_comments"
              :record-src="record.translation_src ?? undefined"
              @commit="
                (text, updateRepeats) =>
                  onSegmentCommit(record.id, text, updateRepeats, idx)
              "
              @update-record="
                (text, updateRepeats) =>
                  onSegmentUpdate(record.id, text, false, updateRepeats, false)
              "
              @focus="focusedSegmentIdx = idx"
              @start-edit="() => onSegmentStartEdit(record.id)"
              @add-comment="() => onAddComment(record.id)"
              @view-history="() => onShowHistory(record.id)"
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

  <TmSearchModal
    v-model="showTmSearchModal"
    :document-id="documentId"
  />

  <RecordCommentModal
    v-model="showCommentsModal"
    :record-id="commentsRecordId ?? -1"
    @add-comment="refetchRecords"
  />

  <AddTermModal
    v-model="showAddTermModal"
    :document-id="documentId"
  />

  <SegmentHistoryModal
    :show="showHistoryModal"
    :record-id="historyRecordId ?? -1"
    @close="showHistoryModal = false"
  />
</template>
