<script setup lang="ts">
import {computed} from 'vue'
import {Button, ProgressBar} from 'primevue'

import Link from './NavLink.vue'

import {DocumentWithRecordsCount} from '../client/schemas/DocumentWithRecordsCount'
import {
  getDownloadDocLink,
  getDownloadOriginalDocLink,
  getDownloadXliffLink,
} from '../client/services/DocumentService'

import {hasPermission} from '../utilities/auth'

const {document} = defineProps<{
  document: DocumentWithRecordsCount
}>()

const downloadLink = computed(() => getDownloadDocLink(document.id))
const originalLink = computed(() => getDownloadOriginalDocLink(document.id))
const xliffLink = computed(() => getDownloadXliffLink(document.id))

const translationProgress = computed(() => {
  if (document.total_word_count === 0) return 0
  return (document.approved_word_count / document.total_word_count) * 100
})

const percentage = computed(
  () => (document.approved_word_count / document.total_word_count) * 100
)
</script>

<template>
  <div class="flex flex-row gap-2 items-center ml-4 mt-4 mb-1">
    <Button
      as="a"
      href="/"
      icon="pi pi-home"
      severity="secondary"
      size="small"
    />

    <h2 class="text-xl font-bold">
      {{ document?.name }}
    </h2>
    <ProgressBar
      class="w-64 h-3 inline-block mx-2 items-center"
      :value="translationProgress"
      :show-value="false"
    />
    {{ document.approved_word_count }} / {{ document.total_word_count }} words
    <span class="text-gray-500">({{ percentage.toFixed(2) }}%)</span>
    <Link
      v-if="hasPermission('document:download')"
      :href="downloadLink"
      class="inline-block"
      title="Download current file"
    />
    <Link
      v-if="hasPermission('document:download')"
      :href="originalLink"
      class="inline-block"
      title="Download original file"
    />
    <Link
      v-if="hasPermission('document:download')"
      :href="xliffLink"
      class="inline-block"
      title="Download XLIFF file"
    />
  </div>
</template>
