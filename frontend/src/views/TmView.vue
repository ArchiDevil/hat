<script setup lang="ts">
import {computed, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useQuery} from '@pinia/colada'

import {
  getMemory,
  getMemoryRecords,
  getDownloadMemoryLink,
  getMemoryRecordsSimilar,
} from '../client/services/TmsService'

import ToggleButton from 'primevue/togglebutton'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'

import DocSegment from '../components/DocSegment.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'
import Link from '../components/NavLink.vue'
import {debounce} from '../utilities/utils'
import {TranslationMemoryListSimilarResponse} from '../client/schemas/TranslationMemoryListSimilarResponse'
import {TranslationMemoryListResponse} from '../client/schemas/TranslationMemoryListResponse'
import {TranslationMemoryRecordWithSimilarity} from '../client/schemas/TranslationMemoryRecordWithSimilarity'

// TODO: 100 records per page is a magic number, it should be obtained from
// the server side somehow.

const route = useRoute()

const documentId = computed(() => Number(route.params.id))

const {data: document} = useQuery({
  key: () => ['tm', documentId.value],
  query: () => getMemory(documentId.value),
  placeholderData: <T>(prevData: T) => prevData,
})

const page = computed(() => {
  return Number(route.query.page ?? '0')
})

const updatePage = async (page: number) => {
  await router.push({
    query: {
      page: page,
    },
  })
}

const debouncedSearch = ref('')
const updateDebouncedSearch = debounce((newVal: string) => {
  window.umami.track('tm-view-search', {
    mode: toggleSimilar.value ? 'similar' : 'exact',
  })
  debouncedSearch.value = newVal
  void updatePage(0)
}, 1000)

const toggleSimilar = ref(false)
watch(toggleSimilar, async () => updatePage(0))

const {data: recordsData} = useQuery({
  key: () => [
    'tm-records',
    documentId.value,
    page.value,
    debouncedSearch.value,
    toggleSimilar.value,
  ],
  query: async (): Promise<
    TranslationMemoryListSimilarResponse | TranslationMemoryListResponse
  > => {
    if (toggleSimilar.value) {
      return getMemoryRecordsSimilar(documentId.value, debouncedSearch.value)
    } else {
      return getMemoryRecords(
        documentId.value,
        page.value,
        debouncedSearch.value
      )
    }
  },
  enabled: () => document.value !== undefined,
  placeholderData: <T>(prevData: T) => prevData,
  staleTime: 600 * 1000,
})

const searchQuery = ref('')
watch(searchQuery, (newVal) => {
  updateDebouncedSearch(newVal)
})

const router = useRouter()
const downloadLink = computed(() =>
  document.value?.id ? getDownloadMemoryLink(document.value?.id) : undefined
)

const docName = computed(
  () =>
    `${document.value?.name} (ID: ${documentId.value}): ${document.value?.records_count} records`
)
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle :title="docName" />
    <div class="mb-4 flex flex-col">
      <Link
        v-if="downloadLink"
        :href="downloadLink"
        class="inline"
        title="Download TMX"
      />
    </div>
    <div class="flex flex-row gap-4 mb-4">
      <ToggleButton
        v-model="toggleSimilar"
        class="ml-auto"
        on-label="Search similar"
        off-label="Search same"
      />
      <IconField class="w-96">
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="searchQuery"
          class="w-full"
          placeholder="Search in source"
        />
      </IconField>
    </div>
    <Paginator
      v-if="recordsData && recordsData?.records.length"
      :rows="100"
      :total-records="recordsData.total_records"
      :first="page * 100"
      @page="(event) => updatePage(event.page)"
    />
    <div
      v-if="recordsData"
      class="grid grid-cols-[auto_auto_1fr_1fr] gap-1"
    >
      <DocSegment
        v-for="record in recordsData.records"
        :id="!toggleSimilar ? record.id : (record as TranslationMemoryRecordWithSimilarity).similarity"
        :key="record.id"
        :source="record.source"
        :target="record.target"
      />
    </div>
  </div>
</template>
