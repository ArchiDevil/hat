<script setup lang="ts">
import {computed, ref, watch} from 'vue'
import {useQuery} from '@pinia/colada'

import Dialog from 'primevue/dialog'
import ToggleButton from 'primevue/togglebutton'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'

import DocSegment from './DocSegment.vue'
import {debounce} from '../utilities/utils'
import {
  searchTmExact,
  searchTmSimilar,
} from '../client/services/DocumentService'
import {TranslationMemoryListSimilarResponse} from '../client/schemas/TranslationMemoryListSimilarResponse'
import {TranslationMemoryListResponse} from '../client/schemas/TranslationMemoryListResponse'
import {TranslationMemoryRecordWithSimilarity} from '../client/schemas/TranslationMemoryRecordWithSimilarity'

const props = defineProps<{
  documentId: number
}>()

const modalVisible = defineModel<boolean>()

const searchQuery = ref('')
const debouncedSearch = ref('')
const toggleSimilar = ref(false)

const updateDebouncedSearch = debounce((newVal: string) => {
  debouncedSearch.value = newVal.trim()
  window.umami.track('tm-modal-search', {
    mode: toggleSimilar.value ? 'similar' : 'exact',
  })
}, 1000)

watch(searchQuery, (newVal) => {
  updateDebouncedSearch(newVal)
})

watch(toggleSimilar, () => {
  // Reset search when toggling mode
  debouncedSearch.value = searchQuery.value
})

const {data: searchResults, isLoading} = useQuery({
  key: () => [
    'tm-search',
    props.documentId,
    debouncedSearch.value,
    toggleSimilar.value,
  ],
  query: async (): Promise<
    TranslationMemoryListSimilarResponse | TranslationMemoryListResponse
  > => {
    const search = debouncedSearch.value.trim()
    if (!search) {
      return {records: [], page: 0, total_records: 0}
    }

    if (toggleSimilar.value) {
      return await searchTmSimilar(props.documentId, search)
    } else {
      return await searchTmExact(props.documentId, search)
    }
  },
  enabled: () =>
    (modalVisible.value ?? false) && debouncedSearch.value.trim().length > 0,
  placeholderData: <T>(prevData: T) => prevData,
})

const hasResults = computed(() => {
  return searchResults.value && searchResults.value.records.length > 0
})

watch(modalVisible, (newVal) => {
  if (newVal) {
    searchQuery.value = ''
    debouncedSearch.value = ''
    toggleSimilar.value = false
  }
})

const header = computed(() => {
  if (searchResults.value) {
    return `Search Memory Record (${searchResults.value.total_records} found)`
  } else {
    return 'Search Memory Record'
  }
})
</script>

<template>
  <Dialog
    v-model:visible="modalVisible"
    modal
    :header="header"
    class="w-[90%] max-w-[1200px]"
  >
    <div class="flex flex-row gap-4 mb-4">
      <ToggleButton
        v-model="toggleSimilar"
        on-label="Search similar"
        off-label="Search exact"
      />
      <IconField class="flex-1">
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="searchQuery"
          class="w-full"
          placeholder="Enter source text to search"
        />
      </IconField>
    </div>

    <div
      v-if="isLoading"
      class="text-center py-4"
    >
      <i class="pi pi-spin pi-spinner text-2xl" />
      <p class="mt-2">
        Searching...
      </p>
    </div>

    <div
      v-else-if="hasResults"
      class="max-h-96 overflow-y-auto"
    >
      <div class="grid grid-cols-[auto_auto_1fr_1fr] gap-1">
        <DocSegment
          v-for="record in searchResults?.records"
          :id="!toggleSimilar ? record.id : (record as TranslationMemoryRecordWithSimilarity).similarity"
          :key="record.id"
          :source="record.source"
          :target="record.target"
        />
      </div>
    </div>

    <div
      v-else-if="searchQuery.trim()"
      class="text-center py-4"
    >
      <i class="pi pi-search text-2xl text-gray-400" />
      <p class="mt-2 text-gray-600">
        No results found
      </p>
    </div>

    <div
      v-else
      class="text-center py-4"
    >
      <i class="pi pi-info-circle text-2xl text-gray-400" />
      <p class="mt-2 text-gray-600">
        Enter search text to find translation memory records
      </p>
    </div>
  </Dialog>
</template>
