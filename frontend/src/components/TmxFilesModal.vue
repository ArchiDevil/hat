<script setup lang="ts">
import {onMounted} from 'vue'

import {TmxUsage} from '../client/schemas/TmxUsage'
import {useTmxStore} from '../stores/tmx'

import AppButton from './AppButton.vue'
import AppModal from './AppModal.vue'
import AppCheckbox from './AppCheckbox.vue'

defineEmits<{
  close: []
}>()
defineProps<{open: boolean}>()

const tmxStore = useTmxStore()

const options = [
  {text: 'Use newest TM', value: 'newest'},
  {text: 'Use oldest TM', value: 'oldest'},
] as {
  text: string
  value: TmxUsage
}[]

onMounted(async () => {
  tmxStore.getTmx()
})
</script>

<template>
  <AppModal :open="open">
    <div class="m-4">
      <p class="mb-2 font-semibold">Select TMX files to use in substitution</p>
      <div class="block mb-4">
        <label>When segment found in multiple TMXs:</label>
        <select
          class="border py-1 px-2 border-slate border-solid rounded"
          v-model="tmxStore.tmxMode"
        >
          <option
            v-for="option in options"
            :value="option.value"
          >
            {{ option.text }}
          </option>
        </select>
      </div>
      <AppButton
        class="mr-2 mb-2"
        @click="tmxStore.selectAll()"
      >
        Use all TMXs
      </AppButton>
      <AppButton
        class="ml-2 mb-2"
        @click="tmxStore.selectNone()"
      >
        Use none of TMXs
      </AppButton>
      <AppCheckbox
        v-for="file in tmxStore.tmxFiles"
        class="mb-2"
        :title="file.name"
        :value="file.selected"
      />
      <AppButton
        class="mt-2 w-20"
        @click="$emit('close')"
      >
        Close
      </AppButton>
    </div>
  </AppModal>
</template>
