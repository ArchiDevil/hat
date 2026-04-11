<script setup lang="ts">
import {ref, watch} from 'vue'
import {Button, InputText} from 'primevue'
import {debounce} from '../../utilities/utils'

const emit = defineEmits<{
  sourceFilterUpdate: [string]
  targetFilterUpdate: [string]
  openTmSearch: []
  openAddTerm: []
  openGoModal: []
  jumpToUnapproved: []
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

const openGoModal = () => {
  window.umami.track('go-segment-open')
  emit('openGoModal')
}

const jumpToUnapproved = () => {
  window.umami.track('jump-unconfirmed')
  emit('jumpToUnapproved')
}
</script>

<template>
  <div class="px-4 py-2 bg-surface-50 rounded-lg border border-surface">
    <div class="flex flex-row gap-4 items-center flex-wrap">
      <InputText
        v-model="sourceFilter"
        placeholder="Filter by source text..."
        class="w-64"
        size="small"
      />
      <InputText
        v-model="targetFilter"
        placeholder="Filter by target text..."
        class="w-64"
        size="small"
      />
      <Button
        icon="pi pi-eraser"
        label="Clear filters"
        severity="secondary"
        size="small"
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
        icon="pi pi-hashtag"
        label="Go to segment"
        severity="secondary"
        size="small"
        @click="openGoModal"
      />
      <Button
        icon="pi pi-reply"
        label="Jump unapproved"
        severity="secondary"
        size="small"
        @click="jumpToUnapproved"
      />
      <Button
        icon="pi pi-search"
        label="Search TM"
        severity="secondary"
        size="small"
        @click="openTmSearch"
      />
      <Button
        icon="pi pi-globe"
        label="Add term"
        severity="secondary"
        size="small"
        @click="openTermModal"
      />
    </div>
  </div>
</template>
