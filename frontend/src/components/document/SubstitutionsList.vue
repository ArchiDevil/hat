<script setup lang="ts">
import {onMounted} from 'vue'
import {useQuery} from '@pinia/colada'

import {GlossarySubstitution, MemorySubstitution} from './types'
import {
  getRecordGlossaryRecords,
  getRecordSubstitutions,
} from '../../client/services/DocumentService'
import {useGlossaryStore} from '../../stores/glossary'

const {documentId, currentSegmentId = undefined} = defineProps<{
  documentId: number
  currentSegmentId?: number
}>()

const subClass = (sub: MemorySubstitution | GlossarySubstitution) => {
  if (sub.type === 'glossary') return 'bg-violet-200'

  if (sub.similarity >= 0.9) return 'bg-green-200'
  if (sub.similarity >= 0.85) return 'bg-lime-200'
  if (sub.similarity >= 0.8) return 'bg-yellow-200'
  if (sub.similarity >= 0.75) return 'bg-amber-200'
  return 'bg-orange-200'
}

const {data: substitutions} = useQuery({
  key: () => ['substitutions', documentId, currentSegmentId ?? -1],
  query: async () => {
    const memorySubs = (
      await getRecordSubstitutions(documentId, currentSegmentId!)
    )
      .map((sub): MemorySubstitution => {
        return {type: 'memory', ...sub}
      })
      .sort((a, b) => b.similarity - a.similarity)

    const glossarySubs = (
      await getRecordGlossaryRecords(documentId, currentSegmentId!)
    )
      .map((sub): GlossarySubstitution => {
        return {
          type: 'glossary',
          source: sub.source,
          target: sub.target,
          comment: sub.comment ?? undefined,
          parentName:
            useGlossaryStore().glossaries.find((g) => g.id == sub.glossary_id)
              ?.name ?? '',
        }
      })
      .sort((a, b) =>
        a.source.toLowerCase().localeCompare(b.source.toLowerCase())
      )
    return [...memorySubs, ...glossarySubs]
  },
  enabled: () => currentSegmentId !== undefined,
  placeholderData: <T>(prevData: T) => prevData,
})

onMounted(async () => {
  await useGlossaryStore().fetchGlossaries()
})
</script>

<template>
  <div class="min-w-[28rem] max-w-[28rem]">
    <div
      v-for="(sub, i) in substitutions"
      :key="i"
      class="py-2 text-base grid grid-cols-[auto_1fr_1fr] gap-2 border-b"
    >
      <div
        class="border rounded px-1 text-center grow-0 h-fit"
        :class="subClass(sub)"
      >
        <label v-if="sub.type == 'memory'">
          {{ (sub.similarity * 100.0).toFixed(0) }}%
        </label>
        <label
          v-else-if="sub.type == 'glossary'"
          :title="sub.parentName"
        >
          Term
        </label>
      </div>
      <div class="font-text">
        {{ sub.source }}
      </div>
      <div class="font-text">
        {{ sub.target }}
      </div>
    </div>
  </div>
</template>
