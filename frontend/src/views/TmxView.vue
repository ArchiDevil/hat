<script setup lang="ts">
import {computed, onMounted, ref, watchEffect} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import {getTmx, getTmxRecords} from '../client/services/TmxService'
import {TmxFileWithRecordsCount} from '../client/schemas/TmxFileWithRecordsCount'
import {TmxFileRecord} from '../client/schemas/TmxFileRecord'

import Paginator, {PageState} from 'primevue/paginator'

import DocumentPair from '../components/DocumentPair.vue'
import PageTitle from '../components/PageTitle.vue'

// TODO: 100 records per page is a magic number, it should be obtained from
// the server side somehow.

const route = useRoute()
const router = useRouter()
const document = ref<TmxFileWithRecordsCount>()
const records = ref<TmxFileRecord[]>()

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
  records.value = await getTmxRecords(document.value.id, page.value)
})

onMounted(async () => {
  const route = useRoute()
  document.value = await getTmx(Number(route.params.id))
})
</script>

<template>
  <div>
    <PageTitle title="TMX file viewer" />
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
    <div v-if="records">
      <DocumentPair
        :record="record"
        v-for="(record, i) in records"
        :key="i"
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
