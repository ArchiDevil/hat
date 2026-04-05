<script setup lang="ts">
import {computed, ref} from 'vue'
import {Button, Dialog, InputText} from 'primevue'

const model = defineModel<boolean>()

defineEmits<{
  go: [number]
}>()

const targetRow = ref('')
const clearData = () => {
  targetRow.value = ''
}

const goDisabled = computed(() => {
  return /^[1-9][0-9]*$/g.test(targetRow.value) == false
})
</script>

<template>
  <Dialog
    v-model:visible="model"
    modal
    header="Go to Segment"
    :style="{width: '32rem'}"
    @hide="clearData"
  >
    <div class="mb-4">
      <div class="flex items-center gap-2">
        <label
          for="glossary"
          class="font-semibold w-40"
        >
          Segment number:
        </label>
        <InputText
          v-model="targetRow"
          class="flex-auto"
          autocomplete="off"
          placeholder="Enter target segment"
        />
      </div>
    </div>

    <div class="flex justify-end gap-2">
      <Button
        type="button"
        label="Cancel"
        severity="secondary"
        class="w-20"
        @click="model = false"
      />
      <Button
        type="button"
        label="Go"
        class="w-20"
        :disabled="goDisabled"
        @click="
          () => {
            $emit('go', parseInt(targetRow))
            model = false
          }
        "
      />
    </div>
  </Dialog>
</template>
