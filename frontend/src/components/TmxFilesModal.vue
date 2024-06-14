<script setup lang="ts">
import {onMounted, ref} from 'vue'

import {getTmxs} from '../client/services/TmxService'
import {TmxFile} from '../client/schemas/TmxFile'

import AppButton from './AppButton.vue'
import AppModal from './AppModal.vue'
import AppCheckbox from './AppCheckbox.vue'

interface SelectedTmx extends TmxFile {
  selected: boolean
}

defineEmits<{
  close: []
}>()
defineProps<{open: boolean}>()

const tmxFiles = ref<SelectedTmx[]>([])

const select = (select: boolean) => {
  for (const tmxFile of tmxFiles.value) {
    if (select && !tmxFile.selected) {
      tmxFile.selected = true
    } else if (!select && tmxFile.selected) {
      tmxFile.selected = false
    }
  }
}

onMounted(async () => {
  const files = await getTmxs()
  for (const file of files) {
    tmxFiles.value = [
      ...tmxFiles.value,
      {
        id: file.id,
        name: file.name,
        selected: true,
      },
    ]
  }
})
</script>

<template>
  <AppModal :open="open">
    <div class="m-2">
      <p class="mb-2">Select TMX files to use in substitution</p>
      <AppButton
        class="mr-2 mb-2"
        @click="select(true)"
      >
        Select All
      </AppButton>
      <AppButton
        class="ml-2 mb-2"
        @click="select(false)"
      >
        Select None
      </AppButton>
      <AppCheckbox
        v-for="file in tmxFiles"
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
