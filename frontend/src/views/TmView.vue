<script setup lang="ts">
import {computed, onMounted, ref, watchEffect} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import {getMemory, getMemoryRecords} from '../client/services/TmsService'
import {TranslationMemoryWithRecordsCount} from '../client/schemas/TranslationMemoryWithRecordsCount'
import {TranslationMemoryRecord} from '../client/schemas/TranslationMemoryRecord'

import Paginator, {PageState} from 'primevue/paginator'

import DocSegment from '../components/DocSegment.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'

// TODO: 100 records per page is a magic number, it should be obtained from
// the server side somehow.

const route = useRoute()
const router = useRouter()
const document = ref<TranslationMemoryWithRecordsCount>()
const records = ref<TranslationMemoryRecord[]>()

const page = computed(() => {
  return Number(route.query['page'] ?? '0')
})

const updatePage = async (event: PageState) => {
  router.push({
    query: {
      page: event.page,
    },
  })
}

watchEffect(async () => {
  if (!document.value) {
    return
  }
  records.value = await getMemoryRecords(document.value.id, page.value)
})

onMounted(async () => {
  const route = useRoute()
  document.value = await getMemory(Number(route.params.id))
})
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle title="Translation memory viewer" />
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <p class="mb-4">Number of records: {{ document?.records_count }}</p>
    <Paginator
      :rows="100"
      :total-records="document?.records_count"
      :first="page * 100"
      v-on:page="(event) => updatePage(event)"
      v-if="records && records?.length"
    />
    <div
      v-if="records"
      class="flex flex-col gap-1"
    >
      <DocSegment
        v-for="record in records"
        :key="record.id"
        :id="record.id"
        :source="record.source"
        :target="record.target"
      />
    </div>
    <Paginator
      :rows="100"
      :total-records="document?.records_count"
      :first="page * 100"
      v-on:page="(event) => updatePage(event)"
      v-if="records && records?.length"
    />
  </div>
</template>
