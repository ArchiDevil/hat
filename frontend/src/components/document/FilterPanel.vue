<script setup lang="ts">
import {ref, watch} from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import {debounce} from '../../utilities/utils'

const emit = defineEmits<{
  sourceFilterUpdate: [string]
  targetFilterUpdate: [string]
}>()

const sourceFilter = ref('')
const targetFilter = ref('')

const updateSourceFilter = debounce((value: string) => {
  emit('sourceFilterUpdate', value)
}, 1000)

const updateTargetFilter = debounce((value: string) => {
  emit('targetFilterUpdate', value)
}, 1000)

watch(sourceFilter, (newVal) => updateSourceFilter(newVal))
watch(targetFilter, (newVal) => updateTargetFilter(newVal))
</script>

<template>
  <div class="mx-4 mt-4 p-4 bg-surface-50 rounded-lg border">
    <h3 class="font-semibold mb-3 text-surface-700">
      Filter Segments
    </h3>
    <div class="flex flex-row gap-4 items-center">
      <InputText
        v-model="sourceFilter"
        placeholder="Filter by source text..."
        class="w-72"
      />
      <InputText
        v-model="targetFilter"
        placeholder="Filter by target text..."
        class="w-72"
      />
      <Button
        label="Clear Filters"
        severity="secondary"
        @click="
          () => {
            sourceFilter = ''
            emit('sourceFilterUpdate', sourceFilter)

            targetFilter = ''
            emit('targetFilterUpdate', targetFilter)
          }
        "
      />
    </div>
  </div>
</template>
