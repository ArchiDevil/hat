<script setup lang="ts">
import {onMounted} from 'vue'

import AppButton from './AppButton.vue'
import AppModal from './AppModal.vue'
import AppCheckbox from './AppCheckbox.vue'
import {useTmxStore} from '../stores/tmx'

defineEmits<{
  close: []
}>()
defineProps<{open: boolean}>()

const tmxStore = useTmxStore()

onMounted(async () => {
  tmxStore.getTmx()
})
</script>

<template>
  <AppModal :open="open">
    <div class="m-2">
      <p class="mb-2">Select TMX files to use in substitution</p>
      <AppButton
        class="mr-2 mb-2"
        @click="tmxStore.selectAll()"
      >
        Select All
      </AppButton>
      <AppButton
        class="ml-2 mb-2"
        @click="tmxStore.selectNone()"
      >
        Select None
      </AppButton>
      <AppCheckbox
        v-for="file in tmxStore.tmxFiles"
        class="mb-2"
        :title="file.name"
        :value="file.selected"
      />
      <AppButton
        class="mt-2"
        @click="$emit('close')"
      >
        Close
      </AppButton>
    </div>
  </AppModal>
</template>
