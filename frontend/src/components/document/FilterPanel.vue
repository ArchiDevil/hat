<script setup lang="ts">
import {InputText} from 'primevue'
import {debounce} from '../../utilities/utils'

const emit = defineEmits<{
  sourceFilterUpdate: [string]
  targetFilterUpdate: [string]
}>()

const updateSourceFilter = debounce((value: string) => {
  emit('sourceFilterUpdate', value)
}, 1000)

const updateTargetFilter = debounce((value: string) => {
  emit('targetFilterUpdate', value)
}, 1000)
</script>

<template>
  <div class="mx-4 mt-4 p-4 bg-surface-50 rounded-lg border">
    <h3 class="font-semibold mb-3 text-surface-700">
      Filter Segments
    </h3>
    <div class="flex flex-row gap-4 items-center">
      <InputText
        placeholder="Filter by source text..."
        class="w-96"
        @update:model-value="(newVal) => updateSourceFilter(newVal ?? '')"
      />
      <InputText
        placeholder="Filter by target text..."
        class="w-96"
        @update:model-value="(newVal) => updateTargetFilter(newVal ?? '')"
      />
    </div>
  </div>
</template>
