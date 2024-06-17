<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {getTmx} from '../client/services/TmxService'
import {TmxFileWithRecords} from '../client/schemas/TmxFileWithRecords'

import DocumentPair from '../components/DocumentPair.vue'
import PageTitle from '../components/PageTitle.vue'

const document = ref<TmxFileWithRecords>()

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
    <p class="mb-4">Number of records: {{ document?.records.length }}</p>
    <div>
      <DocumentPair
        :record="record"
        v-for="record in document?.records"
        :key="record.source" />
    </div>
  </div>
</template>
