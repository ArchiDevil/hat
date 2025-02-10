<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import DocSegment from '../components/DocSegment.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'
import {GlossaryResponse} from '../client/schemas/GlossaryResponse'
import {retrieveGlossary, listRecords} from '../client/services/GlossaryService'
import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'

const document = ref<GlossaryResponse>()
const records = ref<GlossaryRecordSchema[]>()

onMounted(async () => {
  const route = useRoute()
  document.value = await retrieveGlossary(Number(route.params.id))
  records.value = await listRecords(Number(route.params.id))
})
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle title="Glossary viewer" />
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <p class="mb-4">
      Number of records: {{ records?.length }}
    </p>
    <div
      v-if="records"
      class="flex flex-col gap-1"
    >
      <DocSegment
        v-for="record in records"
        :id="record.id"
        :key="record.id"
        :source="record.source"
        :target="record.target"
      />
    </div>
  </div>
</template>
