<script setup lang="ts">
import {Button, Dialog, InputText} from 'primevue'
import {ref} from 'vue'
import {createGlossaryRecord} from '../../client/services/GlossaryService'

const {glossaryId} = defineProps<{
  glossaryId: number
}>()

const emit = defineEmits<{
  close: []
}>()

const model = defineModel<boolean>()

const source = ref('')
const target = ref('')
const comment = ref('')

const submit = async () => {
  await createGlossaryRecord(glossaryId, {
    source: source.value,
    target: target.value,
    comment: comment.value,
  })
  window.umami.track('glossary-add')
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
    </div>
  </Dialog>
</template>
