<script setup lang="ts">
import {
  ComponentPublicInstance,
  computed,
  onUpdated,
  ref,
  triggerRef,
  watch,
} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useQuery, useQueryCache} from '@pinia/colada'

import {Paginator} from 'primevue'

import DocSegment from '../components/DocSegment.vue'
import DocViewHeader from '../components/DocViewHeader.vue'
import SubstitutionsList from '../components/document/SubstitutionsList.vue'
import ProcessingErrorMessage from '../components/document/ProcessingErrorMessage.vue'
import DocumentSkeleton from '../components/document/DocumentSkeleton.vue'
import ToolsPanel from '../components/document/ToolsPanel.vue'
import TmSearchModal from '../components/TmSearchModal.vue'
import RecordCommentModal from '../components/document/RecordCommentModal.vue'
import AddTermModal from '../components/document/AddTermModal.vue'
import SegmentHistoryModal from '../components/document/SegmentHistoryModal.vue'
import GoSegmentModal from '../components/document/GoSegmentModal.vue'

import {
  getDoc,
  getDocRecords,
  getFirstUnapproved,
  getRecordPage,
} from '../client/services/DocumentService'
import {updateDocRecord} from '../client/services/RecordsService'

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
  placeholderData: (prevData) => prevData,
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

const updatePage = async (page: number) => {
  await router.push({query: {page}})
}

type PendingFocus = {type: 'row'; row: number} | {type: 'id'; id: number}
const pendingFocus = ref<PendingFocus>()

const resolvePendingFocus = () => {
  if (pendingFocus.value === undefined) return

  if (pendingFocus.value.type === 'row') {
    focusSegment({row: pendingFocus.value.row})
  } else if (pendingFocus.value.type === 'id') {
    focusSegment({id: pendingFocus.value.id})
  }

  pendingFocus.value = undefined
}

onUpdated(() => {
  resolvePendingFocus()
})

const goToSegment = async (rowNumber: number) => {
  const targetPage = Math.floor(rowNumber / 100)
  await updatePage(targetPage)
  pendingFocus.value = {
    type: 'row',
    row: rowNumber,
  }
  resolvePendingFocus()
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
  placeholderData: (prevData) => prevData,
})

const focusedRowNumber = ref<number>()
const focusedSegmentId = ref<number>()

watch(
  () => [documentId.value, sourceFilter.value, targetFilter.value],
  async () => {
    if (focusedSegmentId.value === undefined) {
      return
    }

    const response = await getRecordPage(
      documentId.value,
      focusedSegmentId.value,
      sourceFilter.value.trim(),
      targetFilter.value.trim()
    )
    if (response.page === null) {
      await updatePage(0)
    } else {
      await updatePage(response.page)
      pendingFocus.value = {
        type: 'id',
        id: focusedSegmentId.value,
      }
    }
  }
)

const recordsCount = computed(() => recordsData.value?.total_records)

const queryCache = useQueryCache()
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
  await queryCache.invalidateQueries({
    key: ['documents', documentId.value],
  })
  // TODO: this should be done too
  // await queryCache.invalidateQueries({
  //   key: ['projects', projectId.value],
  // })
}

const onSegmentCommit = async (
  id: number,
  text: string,
  updateRepeats: boolean,
  rowNumber: number
) => {
  await onSegmentUpdate(id, text, true, updateRepeats, true)
  focusSegment({row: rowNumber + 1})
}

type DocSegmentInstance = ComponentPublicInstance<typeof DocSegment>
const segmentRefs = new Map<number, DocSegmentInstance>()

const storeSegmentRef = (
  rowNumber: number,
  // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
  segment: DocSegmentInstance | Element | null
) => {
  if (segment == null || segment instanceof Element) return
  segmentRefs.set(rowNumber, segment)
}

const focusSegment = (lookup: {row: number} | {id: number}) => {
  const records = recordsData.value?.records
  if (!records) return

  let row: number
  let id: number

  if ('row' in lookup) {
    row = lookup.row
    const record = records.find((r) => r.row_number == lookup.row)
    if (!record) {
      console.error('Unable to find segment by row', row)
      return
    }
    id = record.id
  } else {
    id = lookup.id
    const record = records.find((r) => r.id == lookup.id)
    if (!record) {
      console.error('Unable to find segment by id', id)
      return
    }
    row = record.row_number
  }

  focusedRowNumber.value = row
  focusedSegmentId.value = id

  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const ref = segmentRefs.get(row)
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  ref?.focus()
}

const jumpUnapproved = async () => {
  const result = await getFirstUnapproved(documentId.value)
  if (!result) return

  const pageResult = await getRecordPage(
    documentId.value,
    result.id,
    sourceFilter.value.trim(),
    targetFilter.value.trim()
  )

  if (pageResult.page === null) {
    console.error('Unable to find unapproved record page')
    return
  }

  await updatePage(pageResult.page)
  pendingFocus.value = {
    type: 'id',
    id: result.id,
  }
  resolvePendingFocus()
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

const showTmSearchModal = ref(false)
const showAddTermModal = ref(false)
const showGoModal = ref(false)

const modalRecordId = ref<number>()

const showCommentsModal = ref(false)
const onAddComment = (recordId: number) => {
  modalRecordId.value = recordId
  showCommentsModal.value = true
}

const showHistoryModal = ref(false)
const onShowHistory = (recordId: number) => {
  modalRecordId.value = recordId
  showHistoryModal.value = true
}
</script>

<template>
  <div
    v-if="documentReady"
    class="w-full h-screen grid grid-rows-[auto_1fr] overflow-hidden"
  >
    <div class="bg-surface-0 border-b border-surface">
      <DocViewHeader
        v-if="document"
        :document="document"
      />

      <template v-if="documentReady && !documentLoading">
        <ProcessingErrorMessage
          v-if="document?.status == 'error'"
          class="mt-2 ml-4"
        />
      </template>

      <ToolsPanel
        class="mx-4 mt-2"
        @source-filter-update="(val) => (sourceFilter = val)"
        @target-filter-update="(val) => (targetFilter = val)"
        @open-tm-search="showTmSearchModal = true"
        @open-add-term="showAddTermModal = true"
        @open-go-modal="showGoModal = true"
        @jump-to-unapproved="jumpUnapproved()"
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
          @page="(event) => updatePage(event.page)"
        />
      </div>
    </div>
    <div
      class="overflow-hidden grid grid-cols-[1fr_auto] items-start bg-surface-50"
    >
      <template v-if="documentReady">
        <template v-if="recordsData">
          <div
            class="grid grid-cols-[auto_auto_1fr_1fr_auto] gap-1 overflow-y-scroll mb-1 max-h-full py-2"
          >
            <DocSegment
              v-for="record in recordsData?.records"
              :key="record.id"
              :ref="(seg) => storeSegmentRef(record.row_number, seg)"
              :row-number="record.row_number"
              :source="record.source"
              :target="record.target"
              :disabled="record.loading"
              :approved="record.approved"
              :repetitions-count="record.repetitions_count"
              :has-comments="record.has_comments"
              @commit="
                (text, updateRepeats) =>
                  onSegmentCommit(
                    record.id,
                    text,
                    updateRepeats,
                    record.row_number
                  )
              "
              @update-record="
                (text, updateRepeats) =>
                  onSegmentUpdate(record.id, text, false, updateRepeats, false)
              "
              @focus="focusedSegmentId = record.id"
              @start-edit="() => onSegmentStartEdit(record.id)"
              @add-comment="() => onAddComment(record.id)"
              @view-history="() => onShowHistory(record.id)"
            />
          </div>
          <SubstitutionsList
            class="border-l border-surface"
            :document-id="documentId"
            :current-segment-id="focusedSegmentId"
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
    v-if="document"
    v-model="showTmSearchModal"
    :project-id="document.project_id"
  />

  <RecordCommentModal
    v-model="showCommentsModal"
    :record-id="modalRecordId ?? -1"
    @add-comment="refetchRecords"
  />

  <AddTermModal
    v-if="document"
    v-model="showAddTermModal"
    :project-id="document.project_id"
  />

  <SegmentHistoryModal
    :show="showHistoryModal"
    :record-id="modalRecordId ?? -1"
    @close="showHistoryModal = false"
  />

  <GoSegmentModal
    v-model="showGoModal"
    @go="(rowNumber) => goToSegment(rowNumber)"
  />
</template>
