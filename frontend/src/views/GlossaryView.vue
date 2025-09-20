<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import {useRoute} from 'vue-router'

import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'

import AddTermDialog from '../components/glossary/AddTermDialog.vue'
import PageTitle from '../components/PageTitle.vue'
import PageNav from '../components/PageNav.vue'

import {GlossaryRecordSchema} from '../client/schemas/GlossaryRecordSchema'
import EditTermDialog from '../components/glossary/EditTermDialog.vue'
import {useCurrentGlossaryStore} from '../stores/current_glossary'

const route = useRoute()
const store = useCurrentGlossaryStore()

const {glossary, records} = storeToRefs(store)

const loadGlossary = async () => {
  await store.loadGlossary(Number(route.params.id))
}

onMounted(async () => {
  await loadGlossary()
})

const docName = computed(
  () =>
    `${glossary.value?.name} (ID: ${glossary.value?.id}): ${records.value?.length} records`
)

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
    </div>
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
        />
        <Column
          field="target"
          header="Target"
        />
        <Column
          field="comment"
          header="Comment"
        />
        <Column
          :field="(record: GlossaryRecordSchema) => new Date(record.updated_at).toLocaleString()"
          header="Last update"
        />
        <Column
          field="created_by_user.username"
          header="Created by"
        />
        <Column header="Actions">
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
