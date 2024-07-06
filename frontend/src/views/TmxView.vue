<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {getTmx} from '../client/services/TmxService'
import {TmxFileWithRecordsCount} from '../client/schemas/TmxFileWithRecordsCount'
import {TmxFileRecord} from '../client/schemas/TmxFileRecord'

import DocumentPair from '../components/DocumentPair.vue'
import PageTitle from '../components/PageTitle.vue'

const document = ref<TmxFileWithRecordsCount>()
const records = ref<TmxFileRecord[]>()

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
    <div v-if="records">
      <DocumentPair
        :record="record"
        v-for="record in records"
        :key="record.source"
      />
    </div>
  </div>
</template>
