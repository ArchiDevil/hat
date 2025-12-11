<script setup lang="ts">
import {Button, Column, DataTable, Dialog, Divider, InputText} from 'primevue'
import {ref, watch} from 'vue'
import {useQuery} from '@pinia/colada'

import {
  createGlossaryRecord,
  listRecords,
} from '../../client/services/GlossaryService'
import {debounce} from '../../utilities/utils'

const {glossaryId} = defineProps<{
  glossaryId: number
}>()

const emit = defineEmits<{
  close: []
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

const clearData = () => {
  model.value = false
  source.value = ''
  debouncedSearch.value = ''
  target.value = ''
  comment.value = ''
}

const submit = async () => {
  await createGlossaryRecord(glossaryId, {
    source: source.value,
    target: target.value,
    comment: comment.value,
  })
  window.umami.track('glossary-add')
  clearData()
  emit('close')
}

const {data: foundTerms} = useQuery({
  key: () => ['glossary-records', glossaryId, debouncedSearch.value],
  query: async () =>
    (await listRecords(glossaryId, 0, debouncedSearch.value)).records,
  enabled: () => debouncedSearch.value.length > 2,
  placeholderData: <T>(prevData: T) => prevData,
})
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
