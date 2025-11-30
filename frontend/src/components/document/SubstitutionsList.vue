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
      await getRecordSubstitutions(currentSegmentId!)
    )
      .map((sub): MemorySubstitution => {
        return {type: 'memory', ...sub}
      })
      .sort((a, b) => b.similarity - a.similarity)

    const glossarySubs = (
      await getRecordGlossaryRecords(currentSegmentId!)
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
  staleTime: 30 * 1000,
})

onMounted(async () => {
  await useGlossaryStore().fetchGlossaries()
})
</script>

<template>
  <div class="h-full overflow-scroll p-2">
    <div
      class="text-base w-[28rem] grid grid-cols-[auto_1fr_1fr] gap-y-3 gap-x-3"
    >
      <template
        v-for="(sub, i) in substitutions"
        :key="i"
      >
        <div
          class="border rounded px-1 text-center h-fit"
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
        <div class="border-b">
          {{ sub.source }}
        </div>
        <div class="border-b">
          {{ sub.target }}
        </div>
      </template>
    </div>
  </div>
</template>
