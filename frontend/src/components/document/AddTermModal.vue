<script setup lang="ts">
import {
  Button,
  Column,
  DataTable,
  Dialog,
  Divider,
  InputText,
  Select,
} from 'primevue'
import {computed, ref, watch} from 'vue'
import {useQuery} from '@pinia/colada'

import {
  createGlossaryRecord,
  listRecords,
} from '../../client/services/GlossaryService'
import {getGlossaries} from '../../client/services/DocumentService'
import {GlossaryResponse} from '../../client/schemas/GlossaryResponse'
import {debounce} from '../../utilities/utils'

const {documentId} = defineProps<{
  documentId: number
}>()

const model = defineModel<boolean>()

const debouncedSearch = ref('')
const updateSourceDebounced = debounce((newVal: string) => {
  debouncedSearch.value = newVal.trim()
}, 1000)

const source = ref('')
watch(source, (newVal) => {
  updateSourceDebounced(newVal)
})

const target = ref('')
const comment = ref('')

const selectedGlossary = ref<GlossaryResponse>()
const {data: glossaries, isLoading: isGlossariesLoading} = useQuery({
  key: () => ['doc-glossaries', documentId],
  query: async () => {
    return (await getGlossaries(documentId)).map((r) => r.glossary)
  },
  enabled: () => model.value === true,
  placeholderData: <T>(prevData: T) => prevData,
})

const clearData = () => {
  source.value = ''
  debouncedSearch.value = ''
  target.value = ''
  comment.value = ''
  selectedGlossary.value = undefined
}

const submit = async () => {
  if (!selectedGlossary.value) {
    console.error('No glossary selected')
    return
  }

  await createGlossaryRecord(selectedGlossary.value.id, {
    source: source.value,
    target: target.value,
    comment: comment.value,
  })
  window.umami.track('glossary-add-doc')
  model.value = false
  clearData()
}

const {data: foundTerms} = useQuery({
  key: () => [
    'glossary-records',
    selectedGlossary.value?.id ?? -1,
    debouncedSearch.value,
  ],
  query: async () =>
    (await listRecords(selectedGlossary.value!.id, 0, debouncedSearch.value))
      .records,
  enabled: () =>
    debouncedSearch.value.length > 2 && selectedGlossary.value !== undefined,
  placeholderData: <T>(prevData: T) => prevData,
})

const creationDisabled = computed(
  () => isGlossariesLoading.value || selectedGlossary.value === undefined
)
</script>

<template>
  <Dialog
    v-model:visible="model"
    modal
    header="Add Term"
    :style="{width: '40rem'}"
    @hide="clearData"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <label
          for="glossary"
          class="font-semibold w-24"
        >
          Glossary
        </label>
        <Select
          v-model="selectedGlossary"
          class="flex-auto"
          :options="glossaries"
          option-label="name"
          :loading="isGlossariesLoading"
          :placeholder="
            isGlossariesLoading ? 'Loading...' : 'Select a glossary'
          "
        />
      </div>
      <div class="flex items-center gap-2">
        <label
          for="username"
          class="font-semibold w-24"
        >
          Source
        </label>
        <InputText
          v-model="source"
          class="flex-auto"
          autocomplete="off"
          placeholder="Input source term"
          :disabled="creationDisabled"
        />
      </div>
      <div class="flex items-center gap-2">
        <label
          for="email"
          class="font-semibold w-24"
        >
          Target
        </label>
        <InputText
          v-model="target"
          class="flex-auto"
          autocomplete="off"
          placeholder="Input target term"
          :disabled="creationDisabled"
        />
      </div>
      <div class="flex items-center gap-2">
        <label
          for="email"
          class="font-semibold w-24"
        >
          Comment
        </label>
        <InputText
          v-model="comment"
          class="flex-auto"
          autocomplete="off"
          placeholder="(Optional) Input comment"
          :disabled="creationDisabled"
        />
      </div>

      <div class="flex justify-end gap-2">
        <Button
          type="button"
          label="Cancel"
          severity="secondary"
          @click="model = false"
        />
        <Button
          type="button"
          label="Save"
          :disabled="creationDisabled"
          @click="submit"
        />
      </div>

      <div v-if="foundTerms && foundTerms.length > 0">
        <Divider />
        <h2 class="text-color text-xl font-semibold mb-3">
          Existing terms
        </h2>
        <DataTable
          :value="foundTerms"
          size="small"
          scroll-height="200px"
          scrollable
        >
          <Column
            header="Source"
            field="source"
          />
          <Column
            header="Target"
            field="target"
          />
        </DataTable>
      </div>
    </div>
  </Dialog>
</template>
