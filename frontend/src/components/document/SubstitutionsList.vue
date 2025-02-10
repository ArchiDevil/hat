<script setup lang="ts">
import {GlossarySubstitution, MemorySubstitution} from './types'

defineProps<{
  substitutions: (MemorySubstitution | GlossarySubstitution)[]
}>()

const subClass = (sub: MemorySubstitution | GlossarySubstitution) => {
  if (sub.type === 'glossary') return 'bg-violet-200'

  if (sub.similarity >= 0.9) return 'bg-green-200'
  if (sub.similarity >= 0.85) return 'bg-lime-200'
  if (sub.similarity >= 0.8) return 'bg-yellow-200'
  if (sub.similarity >= 0.75) return 'bg-amber-200'
  return 'bg-orange-200'
}
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
