<script setup lang="ts">
import {useXliffStore} from '../../stores/xliff'

const store = useXliffStore()
</script>

<template>
  <div class="min-w-96 max-w-96">
    <div
      v-for="match in store.substitutions"
      class="py-2 text-base grid grid-cols-[auto_1fr_1fr] gap-2 border-b"
    >
      <div
        class="border rounded bg-surface-200 w-16 text-center grow-0 h-fit"
      >
        {{ (match.similarity * 100.0).toFixed(0) }}%
      </div>
      <div class="font-text">{{ match.source }}</div>
      <div class="font-text">{{ match.target }}</div>
    </div>
  </div>
</template>
