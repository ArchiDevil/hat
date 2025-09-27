<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import {storeToRefs} from 'pinia'
import {useRoute, useRouter} from 'vue-router'

import Paginator from 'primevue/paginator'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'

import AddTermDialog from '../components/glossary/AddTermDialog.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'

import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'
import EditTermDialog from '../components/glossary/EditTermDialog.vue'
import {useCurrentGlossaryStore} from '../stores/current_glossary'
import {debounce} from '../utilities/utils'

const store = useCurrentGlossaryStore()
const {glossary, records} = storeToRefs(store)

const route = useRoute()
const glossaryId = computed(() => Number(route.params.id))

const loadGlossary = async () => {
  await store.loadGlossary(glossaryId.value)
  await store.loadRecords(page.value, search.value)
}

watch(glossaryId, async () => {
  await loadGlossary()
})

onMounted(() => loadGlossary())

const docName = computed(
  () =>
    `${glossary.value?.name} (ID: ${glossaryId.value}): ${glossary.value?.records_count} records`
)

const page = computed(() => {
  return Number(route.query.page ?? '0')
})

const router = useRouter()
const updatePage = async (page: number) => {
  await router.push({
    query: {
      page,
    },
  })
}

watch(page, async () => {
  if (!glossary.value) {
    return
  }
  await store.loadRecords(page.value, search.value)
})

const search = ref('')
const searchRecords = debounce(() => {
  // eslint-disable-next-line @typescript-eslint/no-floating-promises
  store.loadRecords(page.value, search.value)

  // eslint-disable-next-line @typescript-eslint/no-floating-promises
  updatePage(0)
}, 500)

watch(search, () => {
  searchRecords()
})

const addTermDialogVisible = ref(false)

const editTermDialogVisible = ref(false)
const currentRecordId = ref<number>(-1)
</script>

<template>
  <div class="container">
    <PageNav />
    <PageTitle
      :title="docName"
      class="mb-4"
    />
    <div class="flex flex-row gap-4 mb-4">
      <Button
        label="Add new"
        type="button"
        severity="secondary"
        @click="addTermDialogVisible = true"
      />
      <IconField class="ml-auto">
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="search"
          placeholder="Search"
        />
      </IconField>
    </div>
    <Paginator
      v-if="records && records?.length"
      :rows="100"
      :total-records="store.filteredRecordsCount"
      :first="page * 100"
      @page="updatePage($event.page)"
    />
    <div
      v-if="records"
      class="flex flex-col gap-1"
    >
      <DataTable
        :value="records"
        size="small"
      >
        <Column
          field="source"
          header="Source"
          header-style="width: 28rem"
        />
        <Column
          field="target"
          header="Target"
          header-style="width: 28rem"
        />
        <Column
          field="comment"
          header="Comment"
        />
        <Column
          :field="(record: GlossaryRecordSchema) => new Date(record.updated_at).toLocaleString()"
          header="Last update"
          header-style="width: 14rem;"
        />
        <Column
          field="created_by_user.username"
          header="Created by"
          header-style="width: 7rem;"
        />
        <Column header-style="width: 3rem">
          <template #body="{data}">
            <Button
              icon="pi pi-pencil"
              aria-label="Edit"
              size="small"
              severity="secondary"
              variant="text"
              @click="
                () => {
                  const typedData = data as GlossaryRecordSchema
                  currentRecordId = typedData.id
                  editTermDialogVisible = true
                }
              "
            />
          </template>
        </Column>
      </DataTable>
    </div>
    <Paginator
      v-if="records && records?.length"
      :rows="100"
      :total-records="store.filteredRecordsCount"
      :first="page * 100"
      @page="updatePage($event.page)"
    />

    <AddTermDialog
      v-if="glossary !== undefined"
      v-model="addTermDialogVisible"
      :glossary-id="glossary?.id"
      @close="loadGlossary"
    />

    <EditTermDialog
      v-if="glossary !== undefined"
      v-model="editTermDialogVisible"
      :record-id="currentRecordId"
      @close="loadGlossary"
    />
  </div>
</template>
