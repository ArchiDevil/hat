<script setup lang="ts">
import {Ref, ref, computed, PropType} from 'vue'

import Button from './Button.vue'

const emit = defineEmits<{
  uploaded: []
}>()

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  extension: {
    type: String,
    required: true,
  },
  url: {
    type: String,
    required: true,
  },
  uploadMethod: {
    type: Function as PropType<(file: File) => Promise<any>>,
    required: true,
  },
})

const file = ref(null) as Ref<File | null>
const input = ref<HTMLInputElement | null>(null)
const uploadAvailable = computed(() => file.value != null)
const uploading = ref(false)
const status = ref()

const updateFiles = () => {
  status.value = undefined
  const element = input.value as HTMLInputElement
  if (!element.files) {
    return
  }
  file.value = element.files[0]
}

const uploadFile = async () => {
  if (!uploadAvailable) {
    return
  }

  const element = input.value as HTMLInputElement
  const attachedFile = element.files![0]

  try {
    uploading.value = true
    status.value = 'Uploading...'
    await props.uploadMethod(attachedFile)
    uploading.value = false
    status.value = 'Done!'
    emit('uploaded')
  } catch (error: any) {
    uploading.value = false
    status.value = `${error.message} :(`
  }
}
</script>

<template>
  <div class="p-2 min-w-96 border border-slate-500">
    <label
      for="file"
      class="font-semibold mr-2">
      {{ title }}
    </label>
    <input
      id="file-input"
      type="file"
      ref="input"
      @change="updateFiles"
      :accept="extension" />
    <Button
      class="ml-2"
      @click="uploadFile"
      :disabled="!uploadAvailable || uploading">
      Upload
    </Button>
    <span
      class="ml-2"
      v-if="status">
      {{ status }}
    </span>
  </div>
</template>
