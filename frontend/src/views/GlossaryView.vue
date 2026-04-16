<script setup lang="ts">
import {computed, ref, watch} from 'vue'
import {useQuery, useQueryCache} from '@pinia/colada'
import {useRoute, useRouter} from 'vue-router'

import {
  Button,
  Column,
  DataTable,
  IconField,
  InputIcon,
  InputText,
  Paginator,
} from 'primevue'

import AddTermDialog from '../components/glossary/AddTermDialog.vue'
import EditTermDialog from '../components/glossary/EditTermDialog.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'

import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'
import {debounce} from '../utilities/utils'
import {hasPermission} from '../utilities/auth'
import {GLOSSARY_KEYS} from '../queries/glossaries'
import {listRecords, retrieveGlossary} from '../client/services/GlossaryService'

const route = useRoute()
const id = computed(() => Number(route.params.id))
const page = computed(() => {
  return Number(route.query.page ?? '0')
})

const cache = useQueryCache()
const debouncedSearch = ref('')

const {data: glossary} = useQuery({
  key: () => GLOSSARY_KEYS.byId(id.value),
  query: async () => {
    return await retrieveGlossary(id.value)
  },
  placeholderData: (prevData) => prevData,
})

const {data: records} = useQuery({
  key: () => {
    if (debouncedSearch.value.trim().length > 0) {
      return GLOSSARY_KEYS.recordsWithSearch(
        id.value,
        page.value,
        debouncedSearch.value.trim()
      )
    } else {
      return GLOSSARY_KEYS.recordsByIdPaged(id.value, page.value)
    }
  },
  query: async () => {
    return await listRecords(id.value, page.value, debouncedSearch.value.trim())
  },
  placeholderData: (prevData) => prevData,
})

const docName = computed(
  () =>
    `${glossary.value?.name} (ID: ${id.value}): ${glossary.value?.records_count} records`
)

const router = useRouter()
const updatePage = async (page: number) => {
  await router.push({
    query: {
      page,
    },
  })
}

const search = ref('')
const searchRecords = debounce(() => {
  window.umami.track('glossary-search')
  debouncedSearch.value = search.value
  void updatePage(0)
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
      v-if="records && records?.records.length"
      :rows="100"
      :total-records="records?.total_rows"
      :first="page * 100"
      @page="updatePage($event.page)"
    />
    <div
      v-if="records"
      class="flex flex-col gap-1"
    >
      <DataTable
        :value="records.records"
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
          :field="
            (record: GlossaryRecordSchema) =>
              new Date(record.updated_at).toLocaleString()
          "
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
              v-if="hasPermission('glossary:update')"
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
      v-if="records && records?.records.length"
      :rows="100"
      :total-records="records?.total_rows"
      :first="page * 100"
      @page="updatePage($event.page)"
    />

    <AddTermDialog
      v-if="glossary !== undefined"
      v-model="addTermDialogVisible"
      :glossary-id="glossary?.id"
      @close="cache.invalidateQueries({key: GLOSSARY_KEYS.recordsById(id)})"
    />

    <EditTermDialog
      v-if="glossary !== undefined"
      v-model="editTermDialogVisible"
      :glossary-id="id"
      :current-page="page"
      :current-search="debouncedSearch"
      :record-id="currentRecordId"
      @close="cache.invalidateQueries({key: GLOSSARY_KEYS.recordsById(id)})"
    />
  </div>
</template>
