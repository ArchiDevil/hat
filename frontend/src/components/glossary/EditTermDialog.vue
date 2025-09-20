<script setup lang="ts">
import {ref, watchEffect} from 'vue'
import {Button, Dialog, InputText} from 'primevue'
import {
  deleteGlossaryRecord,
  updateGlossaryRecord,
} from '../../client/services/GlossaryService'
import {storeToRefs} from 'pinia'
import {useCurrentGlossaryStore} from '../../stores/current_glossary'

const {records} = storeToRefs(useCurrentGlossaryStore())

const {recordId} = defineProps<{
  recordId: number
}>()

const emit = defineEmits<{
  close: []
}>()

const model = defineModel<boolean>()

const source = ref('')
const target = ref('')
const comment = ref('')

watchEffect(() => {
  const currentRecord = records.value.find((r) => r.id == recordId)
  if (!currentRecord) return

  source.value = currentRecord.source
  target.value = currentRecord.target
  comment.value = currentRecord.comment ?? ''
})

const submitRecord = async () => {
  await updateGlossaryRecord(recordId, {
    source: source.value,
    target: target.value,
    comment: comment.value,
  })
  model.value = false
  emit('close')
}

const deleteRecord = async () => {
  await deleteGlossaryRecord(recordId)
  model.value = false
  emit('close')
}
</script>

<template>
  <Dialog
    v-model:visible="model"
    modal
    header="Add Term"
    :style="{width: '25rem'}"
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
          placeholder="(Optional) Comment for a term"
        />
      </div>

      <div class="flex justify-end gap-2">
        <Button
          type="button"
          label="Delete"
          severity="danger"
          @click="deleteRecord"
        />
        <Button
          type="button"
          label="Cancel"
          severity="secondary"
          @click="model = false"
        />
        <Button
          type="button"
          label="Save"
          @click="submitRecord"
        />
      </div>
    </div>
  </Dialog>
</template>
