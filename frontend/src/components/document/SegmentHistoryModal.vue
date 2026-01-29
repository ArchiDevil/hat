<script setup lang="ts">
import {computed} from 'vue'
import {useQuery} from '@pinia/colada'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

import {getSegmentHistory} from '../../client/services/RecordsService'
import type {DocumentRecordHistory} from '../../client/schemas/DocumentRecordHistory'
import type {DocumentRecordHistoryChangeType} from '../../client/schemas/DocumentRecordHistoryChangeType'
import {
  applyDiffOps,
  type DiffPart,
  type DiffData,
} from '../../composables/useDiff'

interface HistoryWithDiff extends DocumentRecordHistory {
  diffParts?: DiffPart[]
}

const props = defineProps<{
  recordId: number
  show: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const changeTypeColors: Record<DocumentRecordHistoryChangeType, string> = {
  initial_import: '#6B7280',
  machine_translation: '#3B82F6',
  tm_substitution: '#8B5CF6',
  glossary_substitution: '#10B981',
  repetition: '#14B8A6',
  manual_edit: '#F59E0B',
}

const changeTypeLabels: Record<DocumentRecordHistoryChangeType, string> = {
  initial_import: 'Initial Import',
  machine_translation: 'Machine Translation',
  tm_substitution: 'TM Substitution',
  glossary_substitution: 'Glossary Substitution',
  repetition: 'Repetition',
  manual_edit: 'Manual Edit',
}

const {data: history, status: historyStatus} = useQuery({
  key: () => ['history', props.recordId],
  query: async () => (await getSegmentHistory(props.recordId)).history,
  enabled: () => props.show,
  placeholderData: <T,>(prevData: T) => prevData,
})

const formatTimestamp = (timestamp: string) => {
  dayjs.extend(relativeTime)
  return dayjs(timestamp).fromNow()
}

// Process history to calculate diffs between consecutive states
const historyWithDiffs = computed<HistoryWithDiff[]>(() => {
  if (history.value === undefined || history.value.length === 0) return []

  // Process from oldest to newest (reverse order)
  const reversedHistory = [...history.value].reverse()
  const result: HistoryWithDiff[] = []

  let currentText = ''
  for (const item of reversedHistory) {
    const diffData = JSON.parse(item.diff) as DiffData
    if (!diffData.ops || !Array.isArray(diffData.ops)) {
      result.push({...item, diffParts: undefined})
    } else {
      const {newText, diffParts} = applyDiffOps(currentText, diffData.ops)
      result.push({...item, diffParts})
      currentText = newText
    }
  }

  // Return in original order (newest first)
  return result.reverse()
})

const getAuthorName = (historyItem: DocumentRecordHistory) => {
  return historyItem.author?.username ?? 'System'
}

const getDiffClass = (type: DiffPart['type']) => {
  switch (type) {
    case 'added':
      return 'bg-green-200 text-green-900'
    case 'removed':
      return 'bg-red-200 text-red-900 line-through'
    case 'equal':
      return 'text-surface-900'
    default:
      return ''
  }
}
</script>

<template>
  <Dialog
    :visible="show"
    modal
    header="Segment History"
    :style="{width: '80vw', maxWidth: '1200px'}"
    @update:visible="emit('close')"
  >
    <div
      v-if="historyStatus === 'pending'"
      class="flex justify-center items-center py-8"
    >
      <i class="pi pi-spin pi-spinner text-2xl text-primary" />
      <span class="ml-2">Loading history...</span>
    </div>
    <div
      v-else-if="historyStatus === 'error'"
      class="text-red-600 py-4 text-center"
    >
      <i class="pi pi-exclamation-circle mr-2" />
      Failed to load history
    </div>
    <div
      v-else-if="history && history.length === 0"
      class="text-surface-500 py-8 text-center"
    >
      <i class="pi pi-history text-4xl mb-2 block" />
      No history available for this segment
    </div>

    <DataTable
      v-else
      :value="historyWithDiffs"
      data-key="id"
      :row-hover="true"
      striped-rows
    >
      <Column
        field="author"
        header="Author"
        style="width: 150px"
      >
        <template #body="{data}">
          <div class="flex items-center gap-2">
            <span>{{ getAuthorName(data) }}</span>
          </div>
        </template>
      </Column>

      <Column
        field="diff"
        header="Difference"
      >
        <template #body="{data}">
          <span
            v-if="!data.diff"
            class="text-surface-400"
          >
            No diff
          </span>
          <div
            v-else-if="data.diffParts"
            class="whitespace-pre-wrap break-words"
          >
            <span
              v-for="(part, idx) in data.diffParts"
              :key="idx"
              :class="getDiffClass(part.type)"
            >
              {{ part.text }}
            </span>
          </div>
          <span
            v-else
            class="text-surface-400"
          >
            Unable to parse diff
          </span>
        </template>
      </Column>

      <Column
        field="timestamp"
        header="Date"
        style="width: 180px"
      >
        <template #body="{data}">
          {{ formatTimestamp(data.timestamp) }}
        </template>
      </Column>

      <Column
        field="change_type"
        header="Change Type"
        style="width: 180px"
      >
        <template #body="{data}">
          <span
            class="inline-block px-2 py-1 rounded-full text-sm font-medium text-white"
            :style="{
              backgroundColor:
                changeTypeColors[
                  data.change_type as DocumentRecordHistoryChangeType
                ],
            }"
          >
            {{
              changeTypeLabels[
                data.change_type as DocumentRecordHistoryChangeType
              ]
            }}
          </span>
        </template>
      </Column>
    </DataTable>

    <template #footer>
      <Button
        label="Close"
        @click="emit('close')"
      />
    </template>
  </Dialog>
</template>
