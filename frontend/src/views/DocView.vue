<script setup lang="ts">
import {computed, onMounted, watchEffect} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import {useCurrentDocStore} from '../stores/current_document'
import {useGlossaryStore} from '../stores/glossary'

import Paginator, {PageState} from 'primevue/paginator'
import Skeleton from 'primevue/skeleton'
import ProgressBar from 'primevue/progressbar'

import Link from '../components/NavLink.vue'
import DocSegment from '../components/DocSegment.vue'
import SubstitutionsList from '../components/document/SubstitutionsList.vue'
import LoadingMessage from '../components/document/LoadingMessage.vue'
import ProcessingErrorMessage from '../components/document/ProcessingErrorMessage.vue'
import RoutingLink from '../components/RoutingLink.vue'
import {
  GlossarySubstitution,
  MemorySubstitution,
} from '../components/document/types'

// TODO: 100 records per page is a magic number, it should be obtained from
// the server side somehow

const route = useRoute()
const router = useRouter()
const store = useCurrentDocStore()
const glossaryStore = useGlossaryStore()

const documentId = computed(() => {
  return Number(route.params.id)
})
const page = computed(() => {
  return Number(route.query.page ?? '0')
})
const substitutions = computed(
  (): (GlossarySubstitution | MemorySubstitution)[] => {
    const memorySubs = store.substitutions
      .map((sub): MemorySubstitution => {
        return {type: 'memory', ...sub}
      })
      .sort((a, b) => b.similarity - a.similarity)

    const glossarySubs = store.glossaryRecords
      .map((sub): GlossarySubstitution => {
        return {
          type: 'glossary',
          source: sub.source,
          target: sub.target,
          comment: sub.comment ?? undefined,
          parentName:
            glossaryStore.glossaries.find((g) => g.id == sub.glossary_id)
              ?.name ?? '',
        }
      })
      .sort((a, b) =>
        a.source.toLowerCase().localeCompare(b.source.toLowerCase())
      )
    return [...memorySubs, ...glossarySubs]
  }
)

const loadDocument = async () => {
  if (!documentId.value) return
  await store.loadDocument(documentId.value)
  if (!store.document || !store.documentReady) {
    setTimeout(loadDocument, 1000)
  }
}

const translationProgress = computed(() => {
  const doc = store.document
  return doc && (doc?.approved_records_count / doc?.records_count) * 100
})

const updatePage = async (event: PageState) => {
  await router.push({query: {page: event.page}})
}

const onSegmentUpdate = async (id: number, text: string, approved: boolean) => {
  await store.updateRecord(id, text, approved)
}

const onSegmentCommit = async (id: number, text: string) => {
  await onSegmentUpdate(id, text, true)
  store.focusNextSegment()
}

// eslint-disable-next-line @typescript-eslint/no-misused-promises
watchEffect(async () => {
  if (!store.document || !store.documentReady) {
    return
  }
  await store.loadRecords(page.value)
})

onMounted(async () => {
  await loadDocument()
  await useGlossaryStore().fetchGlossaries()
})
</script>

<template>
  <div
    v-if="store.documentReady"
    class="w-full h-screen grid grid-rows-[auto_1fr] overflow-hidden"
  >
    <div class="bg-surface-0 border-b">
      <div>
        <h2 class="text-xl font-bold my-4 ml-4 inline-block">
          {{ store.document?.name }}
        </h2>
        <RoutingLink
          name="home"
          class="ml-4"
          title="Return to main page"
        />
      </div>
      <div class="ml-4 flex flex-row gap-2 items-baseline">
        Progress:
        <ProgressBar
          class="w-64 h-2 inline-block"
          :value="translationProgress"
          :show-value="false"
        />
        {{ store.document?.approved_records_count }} /
        {{ store.document?.records_count }}
        <Link
          :href="store.downloadLink"
          class="inline-block"
          title="Download in the current state"
        />
      </div>
      <template v-if="store.documentReady && !store.documentLoading">
        <ProcessingErrorMessage
          v-if="store.document?.status == 'error'"
          class="mt-2 ml-4"
        />
      </template>
      <div
        v-if="store.documentReady"
        class="flex flex-row gap-4 items-center"
      >
        <Paginator
          :rows="100"
          :total-records="store.document?.records_count"
          :first="page * 100"
          class="inline-block"
          @page="(event) => updatePage(event)"
        />
      </div>
    </div>
    <div class="overflow-hidden grid grid-cols-[auto_1fr] gap-2">
      <template v-if="store.documentReady && !store.documentLoading">
        <template v-if="store.records">
          <div class="flex flex-col gap-1 overflow-scroll my-1 bg-surface-50">
            <DocSegment
              v-for="(record, idx) in store.records"
              :id="record.id"
              :key="record.id"
              editable
              :source="record.source"
              :target="record.target"
              :disabled="record.loading"
              :focused-id="store.currentFocusId"
              :approved="record.approved"
              @commit="(text) => onSegmentCommit(record.id, text)"
              @update-record="(text) => onSegmentUpdate(record.id, text, false)"
              @focus="store.focusSegment(idx)"
            />
          </div>
          <SubstitutionsList
            class="border-l border-y rounded-l-lg px-2 my-1 overflow-scroll bg-surface-50"
            :substitutions="substitutions"
          />
        </template>
        <p v-else>
          Loading...
        </p>
      </template>
    </div>
  </div>
  <div v-else>
    <div class="ml-8 mt-4 flex flex-col gap-2">
      <Skeleton
        width="20rem"
        height="2rem"
      />
      <Skeleton
        width="10rem"
        height="1.2rem"
      />
      <Skeleton
        width="16rem"
        height="1.2rem"
      />
      <Skeleton
        width="8rem"
        height="1.2rem"
      />
      <RoutingLink
        name="home"
        title="Return to main page"
      />
      <LoadingMessage class="max-w-[600px]" />
    </div>
  </div>
</template>
