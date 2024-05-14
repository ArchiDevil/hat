<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'

import {
  getXliff,
  getDownloadXliffLink,
  getXliffRecords,
} from '../client/services/XliffService'
import {XliffFile} from '../client/schemas/XliffFile'

import Link from '../components/Link.vue'
import DocumentPair from '../components/DocumentPair.vue'
import {XliffFileRecord} from '../client/schemas/XliffFileRecord'

const documentId = computed(() => {
  const route = useRoute()
  return Number(route.params.id)
})

const document = ref<XliffFile>()
const records = ref<XliffFileRecord[]>()

const downloadLink = computed(() => {
  return getDownloadXliffLink(documentId.value)
})

const documentStatus = computed(() => {
  return document.value?.status
})

const updateRecords = async () => {
  if (document.value?.status === 'done') {
    records.value = await getXliffRecords(documentId.value)
  } else {
    setTimeout(updateRecords, 1000)
  }
}

onMounted(async () => {
  document.value = await getXliff(documentId.value)
  await updateRecords()
})
</script>

<template>
  <div>
    <h1 class="font-bold text-2xl pt-8">XLIFF file viewer</h1>
    <p>File ID: {{ document?.id }}</p>
    <p>File name: {{ document?.name }}</p>
    <template v-if="documentStatus == 'done'">
      <template v-if="records">
        <p>Number of records: {{ records.length }}</p>
        <Link
          :href="downloadLink"
          class="mb-4 block"
        >
          Download
        </Link>
        <div>
          <DocumentPair
            v-for="record in records"
            :key="record.source"
            :record="record"
          />
        </div>
      </template>
      <template v-else>
        <p>Loading...</p>
      </template>
    </template>
    <template v-else-if="documentStatus != 'error'">
      <p class="mt-2">
        Document is being processed right now. This should not take long.
      </p>
      <p class="mt-2">
        If file is processed too long (it should take not more than 5-10
        minutes), use one of these links to report an issue:
      </p>
      <ul>
        <li>
          Telegram: <Link href="https://t.me/archidevil">@archidevil</Link>
        </li>
        <li>
          Github:
          <Link href="https://github.com/ArchiDevil/hat/issues">
            Issues page
          </Link>
        </li>
      </ul>
    </template>
    <template v-else>
      <p class="mt-2">Error while processing document :(</p>
      <p class="mt-2">
        If this problem persists, use one of these links to report an issue:
      </p>
      <ul>
        <li>
          Telegram: <Link href="https://t.me/archidevil">@archidevil</Link>
        </li>
        <li>
          Github:
          <Link href="https://github.com/ArchiDevil/hat/issues">
            Issues page
          </Link>
        </li>
      </ul>
    </template>
  </div>
</template>
