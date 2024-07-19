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
        class="border px-0.5 rounded bg-surface-100 w-16 text-center grow-0"
      >
        {{ (match.similarity * 100.0).toFixed(0) }}%
      </div>
      <div>{{ match.source }}</div>
      <div>{{ match.target }}</div>
    </div>
  </div>
</template>
