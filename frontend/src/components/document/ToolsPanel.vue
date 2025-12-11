<script setup lang="ts">
import {ref, watch} from 'vue'
import {Button, InputText} from 'primevue'
import {debounce} from '../../utilities/utils'

const emit = defineEmits<{
  sourceFilterUpdate: [string]
  targetFilterUpdate: [string]
  openTmSearch: []
  openAddTerm: []
}>()

const sourceFilter = ref('')
const targetFilter = ref('')

const updateSourceFilter = debounce((value: string) => {
  window.umami.track('source-filter-update')
  emit('sourceFilterUpdate', value)
}, 1000)

const updateTargetFilter = debounce((value: string) => {
  window.umami.track('target-filter-update')
  emit('targetFilterUpdate', value)
}, 1000)

watch(sourceFilter, (newVal) => updateSourceFilter(newVal))
watch(targetFilter, (newVal) => updateTargetFilter(newVal))

const openTmSearch = () => {
  window.umami.track('tm-search-open')
  emit('openTmSearch')
}

const openTermModal = () => {
  emit('openAddTerm')
}
</script>

<template>
  <div class="mx-4 mt-4 p-4 bg-surface-50 rounded-lg border">
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
        icon="pi pi-eraser"
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
      <Button
        icon="pi pi-search"
        label="Search in TM"
        severity="secondary"
        @click="openTmSearch"
      />
      <Button
        icon="pi pi-globe"
        label="Add Term"
        severity="secondary"
        @click="openTermModal"
      />
    </div>
  </div>
</template>
