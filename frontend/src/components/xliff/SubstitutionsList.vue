<script setup lang="ts">
import {useXliffStore} from '../../stores/xliff'

const store = useXliffStore()
</script>

<template>
  <div class="min-w-96 max-w-96">
    <div
      v-for="match in store.substitutions"
      class="py-2 text-base flex flex-row gap-4 border-b"
    >
      <div
        class="border p-1 rounded bg-surface-100 w-16 h-8 text-center grow-0"
      >
        {{ (match.similarity * 100.0).toFixed(0) }}%
      </div>
      <div class="w-1/2">{{ match.source }}</div>
      <div class="w-1/2">{{ match.target }}</div>
    </div>
  </div>
</template>
