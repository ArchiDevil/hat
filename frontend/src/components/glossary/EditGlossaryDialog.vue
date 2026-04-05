<script setup lang="ts">
import {ref, watchEffect} from 'vue'
import {Button, Dialog, InputText} from 'primevue'

import {isAdmin} from '../../utilities/auth'
import {useGlossaries} from '../../queries/glossaries'
import {
  deleteGlossary,
  updateGlossary,
} from '../../client/services/GlossaryService'

const props = defineProps<{
  glossaryId: number
}>()

const emit = defineEmits<{
  close: []
}>()

const {data: glossaries} = useGlossaries()

const name = ref('')
watchEffect(() => {
  const glossary = glossaries.value?.find((g) => g.id == props.glossaryId)
  if (!glossary) return

  name.value = glossary.name
})

const model = defineModel<boolean>()

const busyDelete = ref(false)
const remove = async () => {
  try {
    busyDelete.value = true
    await deleteGlossary(props.glossaryId)
    model.value = false
  } catch (error) {
    console.error(error)
  } finally {
    busyDelete.value = false
    model.value = false
    emit('close')
  }
}

const busyUpdate = ref(false)
const update = async () => {
  try {
    busyUpdate.value = true
    await updateGlossary(props.glossaryId, {name: name.value})
  } catch (error) {
    console.error(error)
  } finally {
    busyUpdate.value = false
    model.value = false
    emit('close')
  }
}
</script>

<template>
  <Dialog
    v-model:visible="model"
    modal
    header="Edit Glossary"
    :style="{width: '25rem'}"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <label
          for="name"
          class="font-semibold w-24"
        >
          Name
        </label>
        <InputText
          id="name"
          v-model="name"
          class="flex-auto"
          autocomplete="off"
          placeholder="Enter name"
        />
      </div>

      <div class="flex justify-end gap-2">
        <Button
          v-if="isAdmin()"
          class="mr-auto"
          type="button"
          label="Delete"
          severity="danger"
          :loading="busyDelete"
          :disabled="busyDelete || busyUpdate"
          @click="remove"
        />
        <Button
          type="button"
          label="Cancel"
          severity="secondary"
          :disabled="busyUpdate || busyDelete"
          @click="model = false"
        />
        <Button
          type="button"
          label="Save"
          :loading="busyUpdate"
          :disabled="busyDelete || busyUpdate"
          @click="update"
        />
      </div>
    </div>
  </Dialog>
</template>
