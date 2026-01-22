<script setup lang="ts">
import {ref, watch, computed} from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

import {getSegmentHistory} from '../../client/services/DocumentService'
import type {SegmentHistory} from '../../client/schemas/SegmentHistory'
import type {SegmentHistoryChangeType} from '../../client/schemas/SegmentHistoryChangeType'
import {
  applyDiffOps,
  type DiffPart,
  type DiffData,
} from '../../composables/useDiff'

interface HistoryWithDiff extends SegmentHistory {
  diffParts?: DiffPart[]
}

interface Props {
  recordId: number
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

const history = ref<SegmentHistory[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const changeTypeColors: Record<SegmentHistoryChangeType, string> = {
  initial_import: '#6B7280',
  machine_translation: '#3B82F6',
  tm_substitution: '#8B5CF6',
  glossary_substitution: '#10B981',
  repetition: '#14B8A6',
  manual_edit: '#F59E0B',
}

const changeTypeLabels: Record<SegmentHistoryChangeType, string> = {
  initial_import: 'Initial Import',
  machine_translation: 'Machine Translation',
  tm_substitution: 'TM Substitution',
  glossary_substitution: 'Glossary Substitution',
  repetition: 'Repetition',
  manual_edit: 'Manual Edit',
}

const fetchHistory = async () => {
  if (!props.recordId) return
  loading.value = true
  error.value = null
  try {
    const response = await getSegmentHistory(props.recordId)
    history.value = response.history
  } catch (err) {
    error.value = 'Failed to load history'
    console.error(err)
  } finally {
    loading.value = false
  }
}

watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      void fetchHistory()
    }
  }
)

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Process history to calculate diffs between consecutive states
const historyWithDiffs = computed<HistoryWithDiff[]>(() => {
  if (!history.value || history.value.length === 0) return []

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

const getAuthorName = (historyItem: SegmentHistory) => {
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
      v-if="loading"
      class="flex justify-center items-center py-8"
    >
      <i class="pi pi-spin pi-spinner text-2xl text-primary" />
      <span class="ml-2">Loading history...</span>
    </div>

    <div
      v-else-if="error"
      class="text-red-600 py-4 text-center"
    >
      <i class="pi pi-exclamation-circle mr-2" />
      {{ error }}
    </div>

    <div
      v-else-if="history.length === 0"
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
                changeTypeColors[data.change_type as SegmentHistoryChangeType],
            }"
          >
            {{ changeTypeLabels[data.change_type as SegmentHistoryChangeType] }}
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
