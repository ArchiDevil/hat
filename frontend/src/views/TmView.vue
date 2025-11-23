<script setup lang="ts">
import {computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useQuery} from '@pinia/colada'

import {
  getMemory,
  getMemoryRecords,
  getDownloadMemoryLink,
} from '../client/services/TmsService'

import Paginator, {PageState} from 'primevue/paginator'

import DocSegment from '../components/DocSegment.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'
import Link from '../components/NavLink.vue'

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

const {data: records} = useQuery({
  key: () => ['tm-records', documentId.value, page.value],
  query: () => getMemoryRecords(documentId.value, page.value),
  enabled: () => document.value !== undefined,
  placeholderData: <T>(prevData: T) => prevData,
})

const router = useRouter()
const updatePage = async (event: PageState) => {
  await router.push({
    query: {
      page: event.page,
    },
  })
}

const downloadLink = computed(() =>
  document.value?.id ? getDownloadMemoryLink(document.value?.id) : undefined
)
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle title="Translation memory viewer" />
    <div class="mb-4 flex flex-col">
      <p>File ID: {{ document?.id }}</p>
      <p>File name: {{ document?.name }}</p>
      <p>Number of records: {{ document?.records_count }}</p>
      <Link
        v-if="downloadLink"
        :href="downloadLink"
        class="block"
        title="Download TMX file"
      />
    </div>
    <Paginator
      v-if="records && records?.length"
      :rows="100"
      :total-records="document?.records_count"
      :first="page * 100"
      @page="(event) => updatePage(event)"
    />
    <div
      v-if="records"
      class="grid grid-cols-[auto_auto_1fr_1fr] gap-1"
    >
      <DocSegment
        v-for="record in records"
        :id="record.id"
        :key="record.id"
        :source="record.source"
        :target="record.target"
      />
    </div>
    <Paginator
      v-if="records && records?.length"
      :rows="100"
      :total-records="document?.records_count"
      :first="page * 100"
      @page="(event) => updatePage(event)"
    />
  </div>
</template>
